import unittest
from unittest import mock
from test_renewal_arbitration import RenewalCase
from baton_v12.worker_manager import tokens, ControlStore
from baton_v12.contracts import ContractRefusal


class FinalArbitration(RenewalCase):
    def scheduled_renewal(self, rollback):
        token = self.held(seconds=60)
        self.instant = '2026-09-27T03:00:30.000Z'
        second = ControlStore.open(self._path, incarnation='renewing-peer', clock=lambda: self.instant)
        self.addCleanup(second.close)
        read = tokens._renewals_of
        judge = tokens._judge_expired
        intercepted = []
        observations = []

        def paused(control, domain, generation):
            answer = read(control, domain, generation)
            if control is self.store and not intercepted:
                intercepted.append(True)
                tokens.renew(second, token, execution='attempt-b', operation='runtime.start:b', expected_revision=0, seconds=900)
                self.instant = '2026-09-27T03:02:00.000Z'
            return answer

        def deciding(control, domain, generation, observed):
            observations.append(dict(observed))
            if rollback:
                self.instant = '2026-09-27T03:00:30.000Z'
            return judge(control, domain, generation, observed)

        with mock.patch.object(tokens, '_renewals_of', paused), mock.patch.object(tokens, '_judge_expired', deciding):
            with self.assertRaises(ContractRefusal):
                tokens.renew(self.store, token, execution='attempt-b', operation='runtime.start:b', expected_revision=0)
        self.assertEqual(intercepted, [True])
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]['revision'], 0)
        self.assertEqual(observations[0]['expires_at'], token['expires_at'])
        state = self.current()
        self.assertEqual(state['revision'], 1)
        self.assertFalse(state['expired'])
        self.assertFalse(state['timing_ambiguous'])
        self.assertIsNone(state['expiry_judged_at'])
        self.renewing(token, expected_revision=1)

    def test_stale_observation_does_not_expire_renewal(self):
        self.scheduled_renewal(False)

    def test_stale_observation_with_rollback_does_not_hold_renewal(self):
        self.scheduled_renewal(True)

    def test_rollback_judgement_is_one_write_and_replays_on_fresh_handle(self):
        token = self.held(seconds=60)
        self.instant = '2026-09-27T03:02:00.000Z'
        judge = tokens._judge_expired
        statements = []
        observed = []

        def deciding(control, domain, generation, observation):
            observed.append(observation)
            self.instant = '2026-09-27T03:00:30.000Z'
            self.store._connection.set_trace_callback(statements.append)
            try:
                return judge(control, domain, generation, observation)
            finally:
                self.store._connection.set_trace_callback(None)

        with mock.patch.object(tokens, '_judge_expired', deciding):
            self.refusal(lambda: self.renewing(token))
        self.assertEqual(sum(s == 'BEGIN IMMEDIATE' for s in statements), 1)
        self.assertEqual(sum(s == 'COMMIT' for s in statements), 1)
        self.assertFalse(any(s == 'ROLLBACK' for s in statements))
        before = self.current()
        self.assertTrue(before['timing_ambiguous'])
        second = ControlStore.open(self._path, incarnation='fresh-reader', clock=lambda: self.instant)
        self.addCleanup(second.close)
        replay = judge(second, token['domain'], token['generation'], observed[0])
        self.assertEqual(replay['decided_at'], before['timing_decided_at'])
        with self.assertRaises(ContractRefusal):
            tokens.renew(second, token, execution='attempt-b', operation='runtime.start:b', expected_revision=0)
        self.assertEqual(self.current()['revision'], 0)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FinalArbitration)
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
