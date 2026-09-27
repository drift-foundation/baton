"""W275774 — `_writer_access`'s comparison window, at the REAL seam.

Review 23:02:00Z traced the leak and 23:13:46Z verified the correction; these are the three
regressions it scheduled, and the route it named: reuse the EXISTING representative fixture,
capture the REAL `_writer_access` arguments, inject faults on the REAL roots, and assert the
JOURNAL's own outcome -- never a mocked release call.

  * the full traversal leaves no standing admission, with the representative case's own
    assertions preserved by CALLING it rather than copying it;
  * a mismatched root refuses and still leaves no standing admission, because a failed
    validation that kept its window would make every later ending for that attempt refuse;
  * a FOREIGN admission over the same roots survives the validation, which is the property
    the release must not weaken.

No live engine, no provider, no container: the stage suite's own recording engine boundary
and its deterministic simulated-human turns.
"""
import copy
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import review_cycles, workspaces

from baton_v12.job_manager import submit, sweep as tick
from tests.job_manager import fixtures
from tests.tools import test_stage_execution as stages


class TheComparisonWindowAtTheRealSeam(
        stages.AAcceptedPRSeedsTheSuccessorOnTheSameStores):
    """The writer-access validation as the production start actually reaches it."""

    def watching(self, hook=None):
        """Capture every real `_writer_access` call, optionally bending its operands.

        THE ARGUMENTS ARE THE REAL ONES. Nothing here composes a line, a writer or a set of
        roots: the deployment does that, and this records what it handed over -- which is
        why a fault injected through `hook` lands on roots the production path proved.
        """
        honest = review_cycles._writer_access
        seen = []

        def watching(store, writer_id, generation, roots, gid, labels):
            seen.append({"store": store, "writer_id": writer_id,
                         "generation": generation, "roots": roots, "gid": gid,
                         "labels": labels,
                         "attempt_id": review_cycles.writer_of(
                             store, writer_id)["runtime_attempt_id"]})
            if hook is not None:
                return hook(honest, seen[-1])
            return honest(store, writer_id, generation, roots, gid, labels)

        review_cycles._writer_access = watching
        self.addCleanup(setattr, review_cycles, "_writer_access", honest)
        return seen

    def started(self):
        """The representative fixture's own composition, driven to a started worker."""
        document = self.only_a(self.traversing())
        document["workers"] = [one for one in document["workers"]
                               if one["role"] != "integration"]
        job, control, composed = self.serving(**document)
        self._composed = composed
        first = copy.deepcopy(self.submission["jobs"][0])
        first["stages"] = [one for one in first["stages"]
                           if one["kind"] != "integration"]
        submit(job, fixtures.submission(jobs=[first]))
        return job, control, composed

    def standing(self, control, attempt_id):
        return workspaces.standing_adoption(control, attempt_id)

    # -- the success path, with the traversal's own assertions kept --------------

    def test_the_FULL_TRAVERSAL_leaves_no_standing_admission(self):
        """The representative case is CALLED, not copied, so its own assertions stand.

        Whatever it proves about the traversal it still proves here; what this adds is the
        journal read the leak would have failed: after a start whose validation passed,
        nothing of that comparison is still admitted.
        """
        seen = self.watching()
        self.test_the_accepted_candidate_seeds_job_b_on_the_same_stores()
        self.assertTrue(seen, "no writer-access validation was reached at all")
        for one in seen:
            with self.subTest(attempt=one["attempt_id"]):
                self.assertEqual(
                    self.standing(one["store"], one["attempt_id"]), [],
                    "the validation left its comparison window open")

    # -- the failure path -------------------------------------------------------

    def test_a_MISMATCHED_root_refuses_and_leaves_no_standing_admission(self):
        """FAULT INJECTED ON THE REAL ROOTS: the workspace the deployment proved, with one
        path changed, so the comparison inside `_writer_access` is the one that fails.

        The journal's own outcome is what is asserted -- the start refuses
        `runtime-observation/identity-mismatch` -- and then that the refusal ended its
        window anyway.
        """
        def bending(honest, call):
            wrong = dict(call["roots"])
            wrong["workspace"] = wrong["workspace"] + "-elsewhere"
            return honest(call["store"], call["writer_id"], call["generation"],
                          wrong, call["gid"], call["labels"])

        seen = self.watching(bending)
        job, control, composed = self.started()
        refusals = []
        for _ in range(6):
            report = tick(job, composed, now=fixtures.NOW)
            for one in report.get("started") or []:
                detail = one.get("detail") or {}
                if detail.get("message"):
                    refusals.append(detail)
        self.assertTrue(seen, "the validation was never reached")
        self.assertTrue(
            any("differ from the durable writer line" in (one.get("message") or "")
                for one in refusals),
            f"the mismatch never reached the journal: {refusals}")
        for one in seen:
            with self.subTest(attempt=one["attempt_id"]):
                self.assertEqual(
                    self.standing(one["store"], one["attempt_id"]), [],
                    "a refused validation left its comparison window open")

    # -- and the property the release must not weaken ---------------------------

    def test_a_FOREIGN_admission_over_the_same_roots_SURVIVES(self):
        """Another holder's admission is not this validation's to end.

        Taken at the moment of the real call, over the REAL line the deployment recorded,
        and read back from the journal afterwards. If the release ended it, every removal
        that should have been blocked would proceed.
        """
        foreign = []

        def also_adopting(honest, call):
            line = review_cycles.line_of(
                call["store"],
                review_cycles.writer_of(call["store"],
                                        call["writer_id"])["line_id"])
            foreign.append(workspaces.line_assignment_workspace(
                review_cycles._storage(call["store"]), call["attempt_id"],
                line["line_path"],
                (line["line_device"], line["line_inode"]),
                control=call["store"]))
            return honest(call["store"], call["writer_id"], call["generation"],
                          call["roots"], call["gid"], call["labels"])

        seen = self.watching(also_adopting)
        job, control, composed = self.started()
        self.drive_job(job, composed, "job-a", "implementation", "waiting")
        self.assertTrue(foreign, "no foreign admission was taken")
        for one in foreign:
            self.addCleanup(workspaces.release_adopted_workspace, one)
        for one in seen:
            with self.subTest(attempt=one["attempt_id"]):
                self.assertNotEqual(
                    self.standing(one["store"], one["attempt_id"]), [],
                    "the validation ended somebody else's admission")


if __name__ == "__main__":
    unittest.main()
