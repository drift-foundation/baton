import unittest
from unittest import mock
from test_renewal_arbitration import RenewalCase
from baton_v12.worker_manager import tokens
from baton_v12.contracts import ContractRefusal

class ClockGap(RenewalCase):
    def test_rollback_between_expiry_refusal_and_judgement_cannot_revive(self):
        token = self.held(seconds=60)
        self.instant = '2026-09-27T03:02:00.000Z'
        original = tokens._judge_expired
        def rollback(*args, **kwargs):
            self.instant = '2026-09-27T03:00:30.000Z'
            return original(*args, **kwargs)
        with mock.patch.object(tokens, '_judge_expired', rollback):
            refusal = self.refusal(lambda: self.renewing(token))
        self.assertIn('expired', refusal.message)
        with self.assertRaises(ContractRefusal):
            self.renewing(token)
        self.assertEqual(self.current()['renewals'], 0)

if __name__ == '__main__':
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([ClockGap('test_rollback_between_expiry_refusal_and_judgement_cannot_revive')])).wasSuccessful())
