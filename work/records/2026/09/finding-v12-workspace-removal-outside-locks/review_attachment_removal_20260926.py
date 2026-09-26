"""Real review attachment admission and removal exclude one another."""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attach_review, workspaces
from tests.manager.test_review_cycles import ReviewCycles


class AttachmentRemoval(ReviewCycles):
    def prepared(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        checkpoint = self.freeze(writer, 1)
        attempt = self.attempt("review-attempt-1", 1, "baton.review", "reviewer-1")
        workspaces.assignment_workspace(self.group, self.storage, attempt)
        return checkpoint, attempt

    def attach(self, checkpoint, attempt):
        return attach_review(self.store, checkpoint_id=checkpoint["checkpoint_id"],
                             attempt_id=attempt, generation=1,
                             reviewer_worker_id="review-worker-1", profile=self.profile)

    def test_real_attachment_excludes_removal(self):
        checkpoint, attempt = self.prepared()
        attached = self.attach(checkpoint, attempt)
        self.assertEqual(workspaces._durably_in_use(self.store, attempt),
                         ("an active review attachment", attached["attachment_id"]))
        with self.assertRaises(ContractRefusal):
            workspaces.discard_workspace(self.storage, attempt, control=self.store)
        self.assertFalse(workspaces.standing_removal(self.store, attempt))

    def test_admitted_removal_excludes_real_attachment(self):
        checkpoint, attempt = self.prepared()
        workspaces._admitted_removal(self.store, attempt, "review competing removal",
                                    workspaces._pinned_home(self.storage, attempt))
        with self.assertRaises(ContractRefusal):
            self.attach(checkpoint, attempt)


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(AttachmentRemoval(name) for name in (
        "test_real_attachment_excludes_removal", "test_admitted_removal_excludes_real_attachment"))
