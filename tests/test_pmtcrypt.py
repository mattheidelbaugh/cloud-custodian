# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
import json
import time
from unittest.mock import patch
from datetime import datetime, timedelta


from c7n.resources.aws import shape_validate
from .common import BaseTest, functional

from c7n.config import Config
from c7n.executor import MainThreadExecutor
from c7n.filters.iamaccess import CrossAccountAccessFilter

class PmtcryptTest(BaseTest):
    def test_mark_for_op(self):
        session_factory = self.replay_flight_data('test_pmtcrypt_mark_for_op')
        p = self.load_policy(
            {
                "name": "mark-unused-keys-for-deletion",
                "resource": "payment-cryptography",
                "filters": [{"tag:custodian_cleanup": "absent"}],
                "actions" : [
                    {
                        "type": "mark-for-op",
                        "tag": "custodian_cleanup",
                        "msg": "Unused Key - : {op}@{action_date}",
                        "op" : "delete",
                        "days": 4,
                    }
                ]
            },
            session_factory=session_factory,
        )

        resources= p.run()
        (json.dumps(resources, indent=2))
        self.assertEqual(len(resources), 1)
        tag_value = resources[0] ["Tags"] [0] ["Value"]
        action_date = (datetime.utcnow()+ timedelta(days=4)).strftime('%y/%m/%d')
        self.assertIn(f"delete@{action_date}", tag_value)
 

        
        