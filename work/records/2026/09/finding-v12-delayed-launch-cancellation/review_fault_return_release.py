"""One bounded stage2 regression: synchronous start fault after runtime creation.

Uses the real disposable fixture and controlled synchronous adapter. No daemon,
provider, deployed resources, or asynchronous engine-completion claim.
"""
import unittest

from baton_v12.worker_manager import attempts
from test_delayed_launch_release import ADelayedSubmitterKeepsTheResource, ATTEMPT


class ReturnedFault(ADelayedSubmitterKeepsTheResource):
    def test_completed_fault_with_known_runtime_can_settle(self):
        adapter, _order = self.prepared()
        fault = RuntimeError('controlled synchronous start fault')
        adapter.start_failure = fault
        with self.assertRaises(RuntimeError) as caught:
            attempts.request_runtime_start(self.store, adapter,
                                           attempt_id=ATTEMPT)
        self.assertIs(caught.exception, fault)
        self.assertEqual(self.row()['runtime_id'], 'runtime-1')
        self.assertEqual(self.lane_holders(), [ATTEMPT])
        ended = self.ending(adapter, reason='settle completed synchronous fault')
        self.assertEqual(ended[:3], ('answered', 'retained', 'absent'), ended)
        self.assertEqual(self.lane_holders(), [])


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([ReturnedFault(
        'test_completed_fault_with_known_runtime_can_settle')])
