"""Deadline review: cooperative failures must not permanently veto exact cleanup."""
import unittest
from unittest import mock

from baton_v12.worker_manager import runtime_lane
from tests.manager import test_runtime_deadlines as candidate
from tests.manager import test_reconciliation_worker as no_start


class Observations(candidate.Deadlines):
    def test_unreachable_agent_permanently_prevents_force_cleanup(self):
        self.started()
        self.reached()
        with mock.patch.object(self.agent, "cancel", side_effect=OSError("agent unreachable")):
            for _ in range(2):
                with self.assertRaisesRegex(OSError, "agent unreachable"):
                    self.advance()
        self.assertEqual(len(self.adapter.stopped), 2)
        self.assertEqual(self.adapter.removed, [])
        self.assertEqual(self.row()["cleanup"], "pending")
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:1")
        self.assertIsNotNone(runtime_lane(self.store, candidate.ATTEMPT))
        print("DEFECT OBSERVED: confirmed fence and successful stop orders, but recurring agent fault vetoes every force-cleanup attempt")

    def test_failing_cooperative_stop_never_reaches_available_force_removal(self):
        self.started()
        self.reached()
        with mock.patch.object(self.adapter, "stop", side_effect=OSError("cooperative stop failed")):
            for _ in range(2):
                with self.assertRaisesRegex(OSError, "cooperative stop failed"):
                    self.advance()
        self.assertEqual(self.adapter.removed, [])
        self.assertEqual(self.row()["cleanup"], "pending")
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:1")
        print("OBSERVED: stop fault likewise prevents attempting separately available exact force removal")


def load_tests(loader, tests, pattern):
    selected = unittest.TestSuite()
    for cls in (candidate.Deadlines, candidate.DeadlineDocuments,
                candidate.DeadlineAdapterBoundary, candidate.DeadlineReceiptedOutput,
                Observations):
        for name in sorted(cls.__dict__):
            if name.startswith("test_"):
                selected.addTest(cls(name))
    selected.addTests(loader.loadTestsFromModule(no_start))
    return selected


if __name__ == "__main__":
    unittest.main(verbosity=2)
