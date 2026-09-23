"""Passing counterexamples demonstrate unreadable/absent conflation."""
from pathlib import Path
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE), str(ROOT / 'v12/python/src'), str(ROOT / 'v12/python')]
from baton_v12.worker_manager import attempts
import supervisor


class Classification(unittest.TestCase):
    def test_failed_read_is_classified_unallocated_and_stop_skipped(self):
        operations = mock.Mock()
        uncertainty = []
        with mock.patch.object(attempts, 'attempt_runtime_of', side_effect=RuntimeError('read unavailable')):
            origin, why = supervisor._origin(mock.Mock(), 'foreign-attempt', set(), uncertainty)
            answer = supervisor._cancel_active(operations, mock.Mock(), {},
                {'foreign-attempt': 'implementation'}, {}, uncertainty,
                reason='exceptional', launched=set())
        self.assertEqual(origin, supervisor.UNALLOCATED)
        self.assertIn('read unavailable', why)
        operations.cancel_attempt.assert_not_called()
        self.assertTrue(answer['foreign-attempt']['requested'])
        self.assertIn('no runtime was ever allocated', answer['foreign-attempt']['why'])
        self.assertTrue(uncertainty)

    def test_positive_missing_row_is_also_classified_unallocated(self):
        with mock.patch.object(attempts, 'attempt_runtime_of', return_value=None):
            self.assertEqual(supervisor._origin(mock.Mock(), 'episode-only', set(), [])[0], supervisor.UNALLOCATED)

    def test_own_launch_still_receives_stop_on_read_failure(self):
        operations = mock.Mock()
        operations.cancel_attempt.return_value = {'fenced': True}
        with mock.patch.object(attempts, 'attempt_runtime_of', side_effect=RuntimeError('read unavailable')):
            self.assertEqual(supervisor._origin(mock.Mock(), 'own-attempt', {'own-attempt'}, [])[0], supervisor.STARTED)
            supervisor._cancel_active(operations, mock.Mock(), {},
                {'own-attempt': 'implementation'}, {}, [], reason='exceptional',
                launched={'own-attempt'})
        operations.cancel_attempt.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)
