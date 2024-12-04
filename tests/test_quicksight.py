# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0

from pytest_terraform import terraform

from .common import BaseTest


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

    # def test_quicksight_user_query(self):
    #     factory = self.record_flight_data("test_quicksight_user_query")

    #     policy = self.load_policy({
    #         "name": "test-aws-quicksight-user",
    #         "resource": "aws.quicksight-user"
    #     }, session_factory=factory)

    #     resources = policy.run()
    #     self.assertEqual(len(resources), 1)
    #     self.assertEqual(resources[0]['UserName'], 'test-user')

    def test_quicksight_dashboard_query(self):
        factory = self.record_flight_data("test_quicksight_dashboard_query")

        policy = self.load_policy({
            "name": "test-aws-quicksight-dashboard",
            "resource": "aws.quicksight-dashboard",
        }, session_factory=factory)

        resources = policy.run()
        self.assertEqual(len(resources), 1)
        # self.assertEqual(resources[0]['Name'], 'test-dashboard')

    def test_quicksight_account_query(self):
        factory = self.record_flight_data("test_quicksight_account_query")

        policy = self.load_policy({
            "name": "test-aws-quicksight-account",
            "resource": "aws.quicksight-account",
        }, session_factory=factory)

        resources = policy.run()
        self.assertEqual(len(resources), 1)