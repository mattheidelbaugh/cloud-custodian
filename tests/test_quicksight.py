# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0

from pytest_terraform import terraform

from .common import BaseTest
from botocore.exceptions import ClientError
from unittest.mock import patch


@terraform("quicksight_group")
def test_quicksight_group_query(test, quicksight_group):
    factory = test.replay_flight_data("test_quicksight_group_query")

    policy = test.load_policy({
      "name": "test-aws-quicksight-group",
      "resource": "aws.quicksight-group"
    }, session_factory=factory, config={'account_id': '490065885863'})

    resources = policy.run()
    assert len(resources) > 0
    assert resources[0]['GroupName'] == 'tf-example'


class TestQuicksight(BaseTest):

    def test_quicksight_account_query(self):
        factory = self.replay_flight_data("test_quicksight_account_query")

        policy = self.load_policy({
            "name": "test-aws-quicksight-account",
            "resource": "aws.quicksight-account",
            "filters": [{"PublicSharingEnabled": False}]
        }, session_factory=factory)

        resources = policy.run()
        self.assertEqual(len(resources), 1)

    @patch('c7n.resources.quicksight.local_session')
    def test_quicksight_account_get_account_not_found(self, local_session_mock):
        session_mock = local_session_mock.return_value
        client_mock = session_mock.client.return_value
        client_mock.describe_account_settings.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}}, "describe_account_settings"
        )

        factory = self.replay_flight_data("test_quicksight_account_not_found")

        policy = self.load_policy({
            "name": "test-aws-quicksight-account",
            "resource": "aws.quicksight-account"
        }, session_factory=factory)

        resources = policy.run()
        self.assertEqual(resources, [])
