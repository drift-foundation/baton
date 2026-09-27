import unittest
from test_renewal_arbitration import RenewalCase
from baton_v12.contracts import ContractRefusal

class RenewalEdges(RenewalCase):
    def test_last_allowed_renewal_lost_reply_replays(self):
        from baton_v12.worker_manager import tokens
        token = self.held()
        for revision in range(tokens.RENEWAL_LIMIT):
            answer = self.renewing(token, expected_revision=revision)
        replay = self.renewing(token, expected_revision=tokens.RENEWAL_LIMIT - 1)
        self.assertEqual(replay, answer)
        self.assertEqual(self.current()['renewals'], tokens.RENEWAL_LIMIT)

    def test_clock_rollback_cannot_revive_observed_expiry(self):
        token = self.held(seconds=60)
        self.instant = '2026-09-27T03:02:00.000Z'
        self.assertTrue(self.current()['expired'])
        self.refusal(lambda: self.renewing(token))
        self.instant = '2026-09-27T03:00:30.000Z'
        with self.assertRaises(ContractRefusal):
            self.renewing(token)
        self.assertEqual(self.current()['renewals'], 0)

if __name__ == '__main__':
    suite = unittest.TestSuite(RenewalEdges(n) for n in RenewalEdges.__dict__ if n.startswith('test_'))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
