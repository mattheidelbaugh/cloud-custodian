from .common import BaseTest


class TestStorageGateway(BaseTest):

    def test_storage_gateway_tag(self):
        session_factory = self.replay_flight_data("test_storage_gateway_tag")
        client = session_factory().client("storagegateway")
        p = self.load_policy(
            {
                "name": "storage-gw-tag",
                "resource": "storage-gateway",
                "filters": [{"GatewayName": "c7n-test"}],
                "actions": [
                    {
                        "type": "tag",
                        "key": "TestTag",
                        "value": "c7n"
                    }
                ],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        tags = client.list_tags_for_resource(ResourceARN=resources[0]["GatewayARN"])['Tags']
        self.assertEqual(tags[0]['Key'], 'TestTag')
        self.assertEqual(tags[0]['Value'], 'c7n')

        p = self.load_policy(
            {
                "name": "storage-gw-untag",
                "resource": "storage-gateway",
                "filters": [{"tag:TestTag": "c7n"}],
                "actions": [{"type": "remove-tag", "tags": ["TestTag"]}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        tags = client.list_tags_for_resource(ResourceARN=resources[0]["GatewayARN"])['Tags']
        self.assertEqual(len(tags), 0)

    def test_storage_gateway_info(self):
        session_factory = self.replay_flight_data("test_storage_gateway_info")
        p = self.load_policy(
            {
                "name": "storage-gw-info",
                "resource": "storage-gateway",
                "filters": [{"type": "info", "key": "GatewayTimezone", "value": "GMT-8:00"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]['c7n:Info']['GatewayTimezone'], 'GMT-8:00')
        self.assertTrue('c7n:MatchedInfo' in resources[0])
