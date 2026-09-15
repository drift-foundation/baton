"""Independent correction checks; fixtures simulate provider and Authority boundaries."""
import unittest
from unittest import mock

from baton_v12.worker_manager import attempts, runtime_lane
from tests.manager import test_runtime_deadlines as candidate
from tests.manager import test_reconciliation_worker as no_start
from tests.manager.test_boundary_inventory import DeadlineForwardingInventory


class Correction(candidate.Deadlines):
    def test_persistent_agent_fault_reaches_cleanup_and_replays_without_reexecution(self):
        self.started()
        self.reached()
        with mock.patch.object(self.agent, "cancel", side_effect=OSError("unreachable")) as cancel:
            result = self.advance()
            self.assertIsNotNone(result["discharge"])
            for _ in range(2):
                self.assertEqual(self.advance(), result)
            self.assertEqual(cancel.call_count, 1)
        self.assertEqual(len(self.adapter.stopped), 1)
        self.assertEqual(len(self.adapter.removed), 1)
        self.assertIsNone(runtime_lane(self.store, candidate.ATTEMPT)["holder"])
        self.assertFalse(runtime_lane(self.store, candidate.ATTEMPT)["held_by_this_attempt"])

    def test_stop_failure_reaches_force_cleanup(self):
        self.started()
        self.reached()
        with mock.patch.object(self.adapter, "stop", side_effect=OSError("stop unreachable")):
            result = self.advance()
            self.assertIsNotNone(result["discharge"])
        self.assertEqual(len(self.adapter.removed), 1)

    def test_process_interruption_does_not_authorize_force_cleanup(self):
        self.started()
        self.reached()
        with mock.patch.object(self.agent, "cancel", side_effect=KeyboardInterrupt("interrupt")):
            with self.assertRaises(KeyboardInterrupt):
                self.advance()
        self.assertEqual(len(self.adapter.stopped), 1)
        self.assertEqual(self.adapter.removed, [])
        self.assertTrue(runtime_lane(self.store, candidate.ATTEMPT)["held_by_this_attempt"])

    def test_replaced_manager_exception_is_not_the_captured_advisory_fault(self):
        self.started()
        self.reached()
        original = attempts.request_cancellation
        manager_failure = OSError("manager failure after cooperative fault")

        def cancellation(*args, **kwargs):
            try:
                return original(*args, **kwargs)
            except OSError:
                raise manager_failure

        with mock.patch.object(self.agent, "cancel", side_effect=OSError("advisory")), mock.patch.object(attempts, "request_cancellation", side_effect=cancellation):
            with self.assertRaises(OSError) as caught:
                self.advance()
        self.assertIs(caught.exception, manager_failure)
        self.assertEqual(self.adapter.removed, [])
        self.assertTrue(runtime_lane(self.store, candidate.ATTEMPT)["held_by_this_attempt"])


def load_tests(loader, tests, pattern):
    selected = unittest.TestSuite()
    for name in sorted(Correction.__dict__):
        if name.startswith("test_"):
            selected.addTest(Correction(name))
    return selected


if __name__ == "__main__":
    unittest.main(verbosity=2)
