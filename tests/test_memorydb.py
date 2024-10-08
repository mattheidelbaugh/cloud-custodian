# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
from .common import BaseTest
from unittest.mock import MagicMock
import time


class MemoryDbTest(BaseTest):

    def test_memorydb(self):
        factory = self.replay_flight_data("test_memory_db")
        p = self.load_policy({
            'name': 'memorydb',
            'resource': 'aws.memorydb'},
            session_factory=factory,
            config={'region': 'us-east-1'})
        resources = p.run()
        self.assertEqual(len(resources), 1)
        assert resources[0]['Name'] == 'test-cluster'

    def test_memorydb_tag_untag(self):
        session_factory = self.replay_flight_data('test_memorydb_tag_untag')
        tag = {'env': 'dev'}
        p = self.load_policy(
            {
                'name': 'memorydb-tag-untag',
                'resource': 'memorydb',
                'filters': [{
                    'tag:owner': 'policy'
                }],
                'actions': [{
                    'type': 'tag',
                    'tags': tag
                },
                {
                    'type': 'remove-tag',
                    'tags': ['owner']
                }]
            },
            session_factory=session_factory
        )
        resources = p.run()
        self.assertEqual(1, len(resources))
        client = session_factory().client("memorydb")
        tags = client.list_tags(ResourceArn=resources[0]["ARN"])["TagList"]
        self.assertEqual(1, len(tags))
        new_tag = {}
        new_tag[tags[0]['Key']] = tags[0]['Value']
        self.assertEqual(tag, new_tag)

    def test_memorydb_mark_for_op(self):
        session_factory = self.replay_flight_data("test_memorydb_mark_for_op")
        p = self.load_policy(
            {
                "name": "memorydb-mark",
                "resource": "memorydb",
                "filters": [
                    {'tag:owner': 'policy'},
                ],
                "actions": [
                    {
                        "type": "mark-for-op",
                        "tag": "custodian_cleanup",
                        "op": "delete",
                        "days": 1,
                    }
                ],
            },
            session_factory=session_factory
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)

        p = self.load_policy(
            {
                "name": "memorydb-marked",
                "resource": "memorydb",
                "filters": [
                    {
                        "type": "marked-for-op",
                        "tag": "custodian_cleanup",
                        "op": "delete",
                        "skew": 3,
                    }
                ],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        assert resources[0]['Name'] == 'test-cluster'

    def test_delete_memorydb(self):
        session_factory = self.replay_flight_data("test_delete_memorydb")
        p = self.load_policy(
            {
                "name": "delete-memorydb",
                "resource": "memorydb",
                "filters": [{"tag:owner": "policy"}],
                "actions": [{
                                "type": "delete",
                            }],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(1, len(resources))
        self.assertEqual(resources[0]["Name"], "test-cluster")

    def test_delete_memorydb_exception(self):
        factory = self.replay_flight_data("test_delete_memorydb")
        client = factory().client("memorydb")
        mock_factory = MagicMock()
        mock_factory.region = 'us-east-1'
        mock_factory().client(
            'memorydb').exceptions.ClusterNotFoundFault = (
                client.exceptions.ClusterNotFoundFault)
        mock_factory().client('memorydb').delete_cluster.side_effect = (
            client.exceptions.ClusterNotFoundFault(
                {'Error': {'Code': 'xyz'}},
                operation_name='delete_cluster'))
        p = self.load_policy({
            'name': 'delete-memorydb-exception',
            'resource': 'memorydb',
            "filters": [{"tag:owner": "policy"}],
            'actions': [{
                            "type": "delete",
                        }],
            },
            session_factory=mock_factory)

        try:
            p.resource_manager.actions[0].process(
                [{'Name': 'abc'}])
        except client.exceptions.ClusterNotFoundFault:
            self.fail('should not raise')
        mock_factory().client('memorydb').delete_cluster.assert_called_once()

    def test_memorydb_security_group(self):
        session_factory = self.replay_flight_data("test_memorydb_security_group")
        p = self.load_policy(
            {
                "name": "memorydb-security-group",
                "resource": "memorydb",
                "filters": [
                    {"type": "security-group", "key": "tag:ASV", "value": "PolicyTest"}
                ],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        assert resources[0]['Name'] == 'test-cluster-custodian'

    def test_memorydb_subnet_filter(self):
        session_factory = self.replay_flight_data(
            "test_memorydb_subnet_filter"
        )
        p = self.load_policy(
            {
                "name": "memorydb-subnet-filter",
                "resource": "memorydb",
                "filters": [
                    {"type": "subnet", "key": "tag:Name", "value": "PublicSubnetA"}
                ],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        assert resources[0]['Name'] == 'test-cluster-custodian'

    def test_memorydb_network_location_filter(self):
        factory = self.replay_flight_data("test_memorydb_network_location_filter")

        p = self.load_policy(
            {
                "name": "test_memorydb_network_location_filter",
                "resource": "memorydb",
                "filters": [
                    {
                        "type": "network-location",
                        "compare": ["resource", "subnet"],
                        "key": "tag:ASV",
                        "match": "equal"
                    }
                ]
            },
            session_factory=factory
        )

        resources = p.run()
        self.assertEqual(len(resources), 1)
        assert resources[0]['Name'] == 'test-cluster-custodian'

    def test_memorydb_kms_encryption(self):
        session_factory = self.replay_flight_data('test_memorydb_kms_encryption')
        p = self.load_policy(
            {
                'name': 'memorydb-kms-encryption',
                'resource': 'memorydb',
                'filters': [
                    {
                        'type': 'kms-key',
                        'key': 'c7n:AliasName',
                        'value': 'alias/tes/pratyush',
                    }
                ],
            }, session_factory=session_factory
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]['Name'], 'test-cluster-2')

    def test_memorydb_snapshot(self):
        factory = self.replay_flight_data("test_memory_db_snapshot")
        p = self.load_policy({
            'name': 'memorydb-snapshot',
            'resource': 'aws.memorydb-snapshot'},
            session_factory=factory,
            config={'region': 'us-east-1'})
        resources = p.run()
        self.assertEqual(len(resources), 1)
        assert resources[0]['Name'] == 'test-snapshot-2'

    def test_memorydb_snapshot_tag_untag(self):
        session_factory = self.replay_flight_data('test_memorydb_snapshot_tag_untag')
        tag = {'env': 'dev'}
        p = self.load_policy(
            {
                'name': 'memorydb-tag-untag',
                'resource': 'memorydb-snapshot',
                'filters': [{
                    'tag:owner': 'policy'
                }],
                'actions': [{
                    'type': 'tag',
                    'tags': tag
                },
                {
                    'type': 'remove-tag',
                    'tags': ['owner']
                }]
            },
            session_factory=session_factory
        )
        resources = p.run()
        self.assertEqual(1, len(resources))
        client = session_factory().client("memorydb")
        tags = client.list_tags(ResourceArn=resources[0]["ARN"])["TagList"]
        self.assertEqual(1, len(tags))
        new_tag = {}
        new_tag[tags[0]['Key']] = tags[0]['Value']
        self.assertEqual(tag, new_tag)

    def test_memorydb_snapshot_mark_for_op(self):
        session_factory = self.replay_flight_data("test_memorydb_snapshot_mark_for_op")
        p = self.load_policy(
            {
                "name": "memorydb-snapshot-mark",
                "resource": "memorydb-snapshot",
                "filters": [
                    {'tag:owner': 'policy'},
                ],
                "actions": [
                    {
                        "type": "mark-for-op",
                        "tag": "custodian_cleanup",
                        "op": "delete",
                        "days": 1,
                    }
                ],
            },
            session_factory=session_factory
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)

        p = self.load_policy(
            {
                "name": "memorydb-marked",
                "resource": "memorydb-snapshot",
                "filters": [
                    {
                        "type": "marked-for-op",
                        "tag": "custodian_cleanup",
                        "op": "delete",
                        "skew": 3,
                    }
                ],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        assert resources[0]['Name'] == 'test-snapshot-2'

    def test_delete_memorydb_snapshot(self):
        session_factory = self.replay_flight_data("test_delete_memorydb_snapshot")
        p = self.load_policy(
            {
                "name": "delete-memorydb-snapshot",
                "resource": "memorydb-snapshot",
                "filters": [{"tag:owner": "policy"}],
                "actions": [{
                                "type": "delete",
                            }],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(1, len(resources))
        self.assertEqual(resources[0]["Name"], "test-snapshot-2")

    def test_memorydb_user_tag_untag(self):
        session_factory = self.replay_flight_data('test_memorydb_user_tag_untag')
        tag = {'env': 'dev'}
        p = self.load_policy(
            {
                'name': 'memorydb-tag-untag',
                'resource': 'memorydb-user',
                'filters': [{
                    'tag:owner': 'policy'
                }],
                'actions': [{
                    'type': 'tag',
                    'tags': tag
                }]
            },
            session_factory=session_factory
        )
        resources = p.run()
        self.assertEqual(1, len(resources))
        time.sleep(60)
        p = self.load_policy(
            {
                'name': 'memorydb-tag-untag',
                'resource': 'memorydb-user',
                'filters': [{
                    'tag:owner': 'policy'
                }],
                'actions': [
                {
                    'type': 'remove-tag',
                    'tags': ['owner']
                }]
            },
            session_factory=session_factory
        )
        resources = p.run()
        time.sleep(60)
        client = session_factory().client("memorydb")
        tags = client.list_tags(ResourceArn=resources[0]["ARN"])["TagList"]
        new_tag = {}
        new_tag[tags[0]['Key']] = tags[0]['Value']
        self.assertEqual(tag, new_tag)

    def test_memorydb_user_mark_for_op(self):
        session_factory = self.replay_flight_data("test_memorydb_user_mark_for_op")
        p = self.load_policy(
            {
                "name": "memorydb-user-mark",
                "resource": "memorydb-user",
                "filters": [
                    {'tag:owner': 'policy'},
                ],
                "actions": [
                    {
                        "type": "mark-for-op",
                        "tag": "custodian_cleanup",
                        "op": "delete",
                        "days": 1,
                    }
                ],
            },
            session_factory=session_factory
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        time.sleep(30)
        p = self.load_policy(
            {
                "name": "memorydb-marked",
                "resource": "memorydb-user",
                "filters": [
                    {
                        "type": "marked-for-op",
                        "tag": "custodian_cleanup",
                        "op": "delete",
                        "skew": 3,
                    }
                ],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        assert resources[0]['Name'] == 'test-user'

    def test_delete_memorydb_user(self):
        session_factory = self.replay_flight_data("test_delete_memorydb_user")
        p = self.load_policy(
            {
                "name": "delete-memorydb-user",
                "resource": "memorydb-user",
                "filters": [{"tag:owner": "policy"}],
                "actions": [{
                                "type": "delete",
                            }],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(1, len(resources))
        self.assertEqual(resources[0]["Name"], "test-user")

    def test_memorydb_acl_tag_untag(self):
        session_factory = self.replay_flight_data('test_memorydb_acl_tag_untag')
        tag = {'env': 'dev'}
        p = self.load_policy(
            {
                'name': 'memorydb-tag-untag',
                'resource': 'memorydb-acl',
                'filters': [{
                    'tag:owner': 'policy'
                }],
                'actions': [{
                    'type': 'tag',
                    'tags': tag
                },
                {
                    'type': 'remove-tag',
                    'tags': ['owner']
                }]
            },
            session_factory=session_factory
        )
        resources = p.run()
        self.assertEqual(1, len(resources))
        client = session_factory().client("memorydb")
        tags = client.list_tags(ResourceArn=resources[0]["ARN"])["TagList"]
        self.assertEqual(1, len(tags))
        new_tag = {}
        new_tag[tags[0]['Key']] = tags[0]['Value']
        self.assertEqual(tag, new_tag)

    def test_memorydb_acl_mark_for_op(self):
        session_factory = self.replay_flight_data("test_memorydb_acl_mark_for_op")
        p = self.load_policy(
            {
                "name": "memorydb-snapshot-mark",
                "resource": "memorydb-acl",
                "filters": [
                    {'tag:owner': 'policy'},
                ],
                "actions": [
                    {
                        "type": "mark-for-op",
                        "tag": "custodian_cleanup",
                        "op": "delete",
                        "days": 1,
                    }
                ],
            },
            session_factory=session_factory
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)

        p = self.load_policy(
            {
                "name": "memorydb-marked",
                "resource": "memorydb-acl",
                "filters": [
                    {
                        "type": "marked-for-op",
                        "tag": "custodian_cleanup",
                        "op": "delete",
                        "skew": 3,
                    }
                ],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        assert resources[0]['Name'] == 'open-access'

    def test_delete_memorydb_acl(self):
        session_factory = self.replay_flight_data("test_delete_memorydb_acl")
        p = self.load_policy(
            {
                "name": "delete-memorydb-acl",
                "resource": "memorydb-acl",
                "filters": [{"tag:team": "test"}],
                "actions": [{
                                "type": "delete",
                            }],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(1, len(resources))
        self.assertEqual(resources[0]["Name"], "test-acl")
