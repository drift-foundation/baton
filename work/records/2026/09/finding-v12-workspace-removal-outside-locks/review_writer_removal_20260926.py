"""Real lifecycle admission must exclude removal in both orders."""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import grant_writer, workspaces
from tests.manager.test_review_cycles import ReviewCycles


class WriterRemoval(ReviewCycles):
    def prepared(self):
        line = self.line()
        attempt = self.attempt("writer-attempt-1", 1, "baton.impl", "writer-1")
        workspaces.assignment_workspace(self.group, self.storage, attempt)
        return line, attempt

    def grant(self, line, attempt):
        return grant_writer(self.store, line_id=line["line_id"], attempt_id=attempt,
                            generation=1, worker_id="worker-1", profile=self.profile)

    def test_real_writer_excludes_removal(self):
        line, attempt = self.prepared()
        writer = self.grant(line, attempt)
        self.assertEqual(workspaces._durably_in_use(self.store, attempt),
                         ("an active line writer", writer["writer_id"]))
        with self.assertRaises(ContractRefusal):
            workspaces.discard_workspace(self.storage, attempt, control=self.store)
        self.assertFalse(workspaces.standing_removal(self.store, attempt))

    def test_admitted_removal_excludes_real_writer(self):
        line, attempt = self.prepared()
        workspaces._admitted_removal(self.store, attempt, "review competing removal",
                                    workspaces._pinned_home(self.storage, attempt))
        with self.assertRaises(ContractRefusal):
            self.grant(line, attempt)


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(WriterRemoval(name) for name in (
        "test_real_writer_excludes_removal", "test_admitted_removal_excludes_real_writer"))
