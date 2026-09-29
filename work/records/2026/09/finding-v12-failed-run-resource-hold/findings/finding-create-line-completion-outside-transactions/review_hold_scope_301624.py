"""Same-process preparation lifetime and connection identity checks."""
import unittest
from unittest import mock
from tests.manager.test_review_cycles import StableLineLifecycle, NOW
from baton_v12.worker_manager import workspaces, review_cycles, ControlStore
from baton_v12.contracts import ContractRefusal

class HoldScope(StableLineLifecycle):
    def test_refused_competitor_never_enters_materialize(self):
        original = workspaces.prove_line_integrity
        called = False
        def interleave(*args, **kwargs):
            nonlocal called
            if not called:
                called = True
                with self.assertRaises(ContractRefusal):
                    self.line()
            return original(*args, **kwargs)
        with mock.patch.object(workspaces, "prove_line_integrity", side_effect=interleave):
            self.line()
        self.assertEqual(self.profile.materialize_calls, 1, "refused competitor reached external materialization before hold check")

    def test_second_connection_same_process_cannot_bypass_hold(self):
        original = workspaces.os.fchmod
        switched = False
        states = []
        def interleave(fd, mode):
            nonlocal switched
            if not switched:
                switched = True
                first = self.store
                with ControlStore.open(self.control_path, incarnation="same-process-second-handle", clock=lambda: NOW) as second:
                    self.store = second
                    try:
                        line = self.line()
                        self.writer(line["line_id"], 1)
                    except ContractRefusal:
                        pass
                    else:
                        states.append(review_cycles.line_of(second, line["line_id"])["state"])
                    finally:
                        self.store = first
            return original(fd, mode)
        with mock.patch.object(workspaces.os, "fchmod", side_effect=interleave):
            self.line()
        self.assertNotIn("writing", states, "store-object identity lets second handle bypass resource exclusion")

if __name__ == "__main__":
    suite=unittest.TestSuite(HoldScope(n) for n in ("test_refused_competitor_never_enters_materialize", "test_second_connection_same_process_cannot_bypass_hold"))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
