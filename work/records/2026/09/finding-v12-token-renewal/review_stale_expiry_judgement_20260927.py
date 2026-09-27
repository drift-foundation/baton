import unittest
from unittest import mock
from test_renewal_arbitration import RenewalCase
from baton_v12.worker_manager import tokens, ControlStore
from baton_v12.contracts import ContractRefusal

class StaleExpiryJudgement(RenewalCase):
    def test_stale_deadline_cannot_judge_committed_renewal_expired(self):
        token = self.held(seconds=60)
        self.instant = '2026-09-27T03:00:30.000Z'
        second = ControlStore.open(self._path, incarnation='renewing-peer', clock=lambda: self.instant)
        self.addCleanup(second.close)
        original = tokens._deadline_of
        intercepted = []
        def paused(control, domain, generation, acquired=None):
            deadline = original(control, domain, generation, acquired)
            if control is self.store and not intercepted:
                intercepted.append(True)
                tokens.renew(second, token, execution='attempt-b', operation='runtime.start:b', expected_revision=0, seconds=900)
                self.instant = '2026-09-27T03:02:00.000Z'
            return deadline
        with mock.patch.object(tokens, '_deadline_of', paused):
            try:
                self.renewing(token, expected_revision=0)
            except ContractRefusal:
                pass  # stale request may refuse; it may not expire the renewed token
        state = self.current()
        self.assertEqual(state['revision'], 1)
        self.assertLess(self.instant, state['expires_at'])
        self.assertFalse(state['expired'])
        self.assertIsNone(state['expiry_judged_at'])

if __name__ == '__main__':
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([StaleExpiryJudgement('test_stale_deadline_cannot_judge_committed_renewal_expired')])).wasSuccessful())
