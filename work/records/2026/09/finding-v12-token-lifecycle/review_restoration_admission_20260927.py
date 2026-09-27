"""Independent current-boundary proof; inherited fixtures, one explicit selector."""
import unittest
from unittest import mock
from tests.manager.test_review_cycles import AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint
from baton_v12.worker_manager import review_cycles

class AdmissionBoundary(AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint):
    def test_moved_line_before_atomic_admission_has_no_effect(self):
        self.abandoned()
        original = review_cycles._admitted_execution
        def moved(store, operation_id, line, writer, checkpoint, what):
            store._connection.execute(
                "UPDATE review_lines SET state = 'reviewing' WHERE line_id = ?",
                (self.line_id,))
            return original(store, operation_id, line, writer, checkpoint, what)
        with mock.patch.object(review_cycles, '_admitted_execution', moved):
            refusal = self.refused()
        self.assertEqual((refusal.category, refusal.code), ('refused', 'precondition'))
        self.assertIn('no longer holds the exclusion', refusal.message)
        self.assertEqual(self.profile.restore_calls, [])
        self.assertIsNone(review_cycles.abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))

if __name__ == '__main__':
    suite = unittest.TestSuite([AdmissionBoundary('test_moved_line_before_atomic_admission_has_no_effect')])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
