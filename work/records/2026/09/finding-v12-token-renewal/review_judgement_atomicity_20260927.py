import unittest
from unittest import mock
from test_renewal_arbitration import RenewalCase
from baton_v12.worker_manager import tokens, ControlStore
from baton_v12.contracts import ContractRefusal


class JudgementAtomicity(RenewalCase):
    def test_two_decisions_cannot_leave_expiry_unrecorded(self):
        token = self.held(seconds=60)
        self.instant = '2026-09-27T03:02:00.000Z'
        original = self.store.transact

        def scheduled(identity, kind, signature, act):
            if kind == tokens.EXPIRED_KIND:
                self.instant = '2026-09-27T03:00:30.000Z'
            elif kind == tokens.TIMING_AMBIGUOUS_KIND:
                self.instant = '2026-09-27T03:02:00.000Z'
            return original(identity, kind, signature, act)

        with mock.patch.object(self.store, 'transact', scheduled):
            self.refusal(lambda: self.renewing(token))
        self.instant = '2026-09-27T03:00:30.000Z'
        with self.assertRaises(ContractRefusal):
            self.renewing(token)

    def test_torn_observation_cannot_hold_a_successful_renewal(self):
        token = self.held(seconds=60)
        self.instant = '2026-09-27T03:00:30.000Z'
        second = ControlStore.open(self._path, incarnation='renewing-peer', clock=lambda: self.instant)
        self.addCleanup(second.close)
        deadline_of = tokens._deadline_of
        judge = tokens._judge_expired
        intercepted = []

        def paused(control, domain, generation, acquired=None):
            deadline = deadline_of(control, domain, generation, acquired)
            if control is self.store and not intercepted:
                intercepted.append(True)
                tokens.renew(second, token, execution='attempt-b', operation='runtime.start:b', expected_revision=0, seconds=900)
                self.instant = '2026-09-27T03:02:00.000Z'
            return deadline

        def rollback(*args, **kwargs):
            self.instant = '2026-09-27T03:00:30.000Z'
            return judge(*args, **kwargs)

        with mock.patch.object(tokens, '_deadline_of', paused), mock.patch.object(tokens, '_judge_expired', rollback):
            self.refusal(lambda: self.renewing(token, expected_revision=0))
        state = self.current()
        self.assertEqual(state['revision'], 1)
        self.assertFalse(state['timing_ambiguous'], 'an old deadline paired with the new revision poisoned the committed renewal')


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(JudgementAtomicity)
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
