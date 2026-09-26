"""W270664 F2 — the real-row half of this Work's selector.

REUSING THE REVIEWER'S FIXTURE, as review 2026-09-26T08:14:20Z asked ("reuse immutable
writer/attachment probes in selectors"). The accepted `ReviewCycles` fixture builds real lines,
attempts, writers and attachments, which my `Workspace`-based selector cannot -- its inserts hit
foreign keys, which is exactly why my durable-use case had to use a labelled answer and why I had
to withdraw a mutation claim about the grant-side hook.

THESE CASES CLOSE BOTH OF THOSE GAPS WITH REAL ROWS. `ReviewCycles` is an accepted suite class and
is NOT modified; it is subclassed, which is the same discipline the reviewer's own probes use.
"""
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attach_review, grant_writer, workspaces

from tests.manager.test_review_cycles import ReviewCycles


class RealRowsExcludeRemoval(ReviewCycles):

    def prepared(self, attempt_id="writer-attempt-1", worker="writer-1"):
        line = self.line()
        attempt = self.attempt(attempt_id, 1, "baton.impl", worker)
        workspaces.assignment_workspace(self.group, self.storage, attempt)
        return line, attempt

    def test_the_durable_use_query_answers_from_real_rows(self):
        """THE QUERY ITSELF, which my labelled answer could not exercise.

        `_durably_in_use` is pure SQL over `line_writers` and `review_attachments`. With a REAL
        granted writer it names that writer; the removal then refuses and takes no ownership.
        This is the case my `Workspace`-fixture selector could not write, because inserting a
        writer row there violates the foreign keys -- recorded at the time rather than papered
        over, and closed here.
        """
        line, attempt = self.prepared()
        writer = grant_writer(self.store, line_id=line["line_id"], attempt_id=attempt,
                              generation=1, worker_id="worker-1", profile=self.profile)
        self.assertEqual(workspaces._durably_in_use(self.store, attempt),
                         ("an active line writer", writer["writer_id"]))
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.discard_workspace(self.storage, attempt, control=self.store)
        self.assertIn("held by an active line writer", caught.exception.message)
        self.assertFalse(workspaces.standing_removal(self.store, attempt),
                         "a refused removal takes no ownership")

    def test_an_admitted_removal_excludes_a_real_writer_grant(self):
        """THE GRANT-SIDE HOOK, which I implemented and then WRONGLY claimed was covered.

        I wrote in PROGRESS that a mutation dropping `grant_writer`'s standing-removal read
        failed a case; it did not, because no case of mine took an ownership and then granted.
        This is that case, with a real line and attempt: the removal is admitted first and the
        grant is refused at its own admission.
        """
        line, attempt = self.prepared()
        workspaces._admitted_removal(
            self.store, attempt, "author competing removal",
            workspaces._pinned_home(self.storage, attempt))
        with self.assertRaises(ContractRefusal) as caught:
            grant_writer(self.store, line_id=line["line_id"], attempt_id=attempt,
                         generation=1, worker_id="worker-1", profile=self.profile)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("recorded no completion", caught.exception.message)


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only the cases defined in THIS module, never the accepted suite's own."""
    suite = unittest.TestSuite()
    for name in loader.getTestCaseNames(RealRowsExcludeRemoval):
        if name in RealRowsExcludeRemoval.__dict__:
            suite.addTest(RealRowsExcludeRemoval(name))
    return suite
