"""A deterministic switch at the actual syscall boundary, after the DB guard."""
import unittest
from unittest import mock
from tests.manager.test_review_cycles import StableLineLifecycle
from baton_v12.worker_manager import workspaces, review_cycles
from baton_v12.contracts import ContractRefusal

class AccessBoundary(StableLineLifecycle):
    def test_no_access_mutation_after_competing_writer_admission(self):
        original = workspaces.os.fchmod
        switched = False
        states = []
        def switch(fd, mode):
            nonlocal switched
            if not switched:
                switched = True
                try:
                    line = self.line()
                    self.writer(line["line_id"], 1)
                except ContractRefusal:
                    # Exclusive preparation may safely refuse a live competitor.
                    # Recovery after termination is a different schedule.
                    pass
                else:
                    states.append(review_cycles.line_of(self.store, line["line_id"])["state"])
            return original(fd, mode)
        with mock.patch.object(workspaces.os, "fchmod", side_effect=switch):
            self.line()
        self.assertTrue(switched)
        self.assertNotIn("writing", states, "actual fchmod still runs after a competing creator admitted a writer")

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([AccessBoundary("test_no_access_mutation_after_competing_writer_admission")]))
    raise SystemExit(not result.wasSuccessful())
