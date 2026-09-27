"""Independent expiry proof: a running worker has no result intake receipt."""
import unittest
from baton_v12.worker_manager import attempts, intake, tokens
from tests.manager.test_intake import ATTEMPT, RETENTION, TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence as Fixture

class RunningExpiry(unittest.TestCase):
    def test_expiry_stops_a_running_attempt_without_intake(self):
        f = Fixture()
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.addCleanup(f.tearDown)
        f.running_attempt()
        attempts.pin_boundary_identity(f.store, attempt_id=ATTEMPT, source=(66, 111), workspace=(66, 4242))
        attempt = f.attempt_row()
        govern = tokens.workspace_governance()
        reservation = govern.reserve(f.store, attempt, operation=attempts._start_operation_id(attempt))
        reservation.bind(attempt['runtime_id'])()
        reservation.settle(attempt['runtime_id'])
        self.assertIsNone(intake.intake_receipt_of(f.store, ATTEMPT))
        f.store._clock = lambda: '2026-08-24T01:00:00.000Z'
        adapter = f.Abandoner()
        calls = []
        original = adapter.destroy
        def watched(command):
            calls.append(command)
            return original(command)
        adapter.destroy = watched
        try:
            answer = intake.reclaim_expired_resource(f.store, adapter, attempt_id=ATTEMPT, govern=govern, retention_policy_digest=RETENTION)
        finally:
            self.assertTrue(tokens.token_of(f.store, 'workspace:66:4242', 1)['revoked'])
            self.assertEqual(len(calls), 1, 'expiry revoked permission but never attempted runtime shutdown')
        self.assertEqual(answer['reclaimed'], 'held')

if __name__ == '__main__':
    unittest.main(defaultTest='RunningExpiry')
