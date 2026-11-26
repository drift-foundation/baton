"""W385263: the review verdict a Job headline may show, and only that one.

Owner decision 2026-11-26: ALL PHASES COMPLETE shows a durable review verdict
beside it only when the verdict matches this Job's review attempt and
candidate checkpoint. `review_verdicts.matching` is the one place that decides
the match; these cases drive the REAL review-line acts (`attach_review`,
`record_verdict`, a correction round) in a disposable control store and read
the answer back through the stopped-manager read surface.

The fixture is `tests.manager.test_review_cycles.ReviewCycles`, composed by
module attribute: none of that module's test classes is bound here.
"""
import unittest

from baton_v12.job_manager import projection, reading, review_verdicts
from baton_v12.job_manager.delegation import Unobserved
from baton_v12.worker_manager import ControlStore

from tests.manager import test_review_cycles as cycles


class AVerdictIsShownOnlyForItsOwnAttemptAndCandidate(unittest.TestCase):
    def setUp(self):
        self.cycles = cycles.ReviewCycles("test_line_and_each_operation_replay_exactly")
        self.cycles.setUp()
        self.addCleanup(self.cycles.tearDown)
        self.store = self.cycles.store

    def round(self, line, number, prior=None, disposition=None):
        writer = self.cycles.writer(line["line_id"], number, prior)
        checkpoint = self.cycles.freeze(writer, number)
        review = self.cycles.review(checkpoint["checkpoint_id"], number)
        verdict = self.cycles.verdict(review, number, disposition) if disposition else None
        return checkpoint, review, verdict

    def matching(self, number, generation=None):
        return review_verdicts.matching(self.store, attempt_id=f"review-attempt-{number}",
                                        generation=number if generation is None else generation)

    def test_an_accepted_verdict_on_the_candidate_is_the_one_shown(self):
        line = self.cycles.line()
        checkpoint, review, verdict = self.round(line, 1, disposition="accepted")
        found = self.matching(1)
        self.assertEqual(found, {"disposition": "accepted", "verdict_id": verdict["verdict_id"],
                                 "attachment_id": review["attachment_id"], "attempt_id": "review-attempt-1",
                                 "checkpoint_id": checkpoint["checkpoint_id"], "line_id": line["line_id"],
                                 "base_object": checkpoint["evidence"]["base"],
                                 "head_object": checkpoint["evidence"]["head"],
                                 "tree_object": checkpoint["evidence"]["tree"], "importable": True})

    def test_a_MISSING_verdict_is_no_verdict(self):
        line = self.cycles.line()
        self.round(line, 1)
        self.assertIsNone(self.matching(1))

    def test_a_verdict_for_ANOTHER_CHECKPOINT_is_no_verdict(self):
        """Round one was changes-requested; round two's candidate is attached
        and not yet judged. Neither attempt reads as having a verdict on the
        current candidate, so nothing can produce REVIEW ACCEPTED -- until the
        second review is actually accepted, and then only for its own attempt."""
        line = self.cycles.line()
        first, _, rejected = self.round(line, 1, disposition="changes-requested")
        self.assertEqual(rejected["checkpoint_id"], first["checkpoint_id"])
        second, review, _ = self.round(line, 2, prior=first["checkpoint_id"])
        self.assertNotEqual(first["checkpoint_id"], second["checkpoint_id"])
        self.assertIsNone(self.matching(1), "round one's verdict is about an earlier checkpoint")
        self.assertIsNone(self.matching(2), "round two has no verdict yet")
        self.cycles.verdict(review, 2, "accepted")
        self.assertEqual(self.matching(2)["checkpoint_id"], second["checkpoint_id"])
        self.assertEqual(self.matching(2)["disposition"], "accepted")
        self.assertIs(self.matching(2)["importable"], True)
        self.assertIsNone(self.matching(1))

    def test_a_CHANGES_REQUESTED_verdict_on_the_candidate_is_never_importable(self):
        line = self.cycles.line()
        checkpoint, _, _ = self.round(line, 1, disposition="changes-requested")
        found = self.matching(1)
        self.assertEqual((found["disposition"], found["checkpoint_id"], found["importable"]),
                         ("changes-requested", checkpoint["checkpoint_id"], False))

    def test_another_attempt_generation_or_a_malformed_operand_is_no_verdict(self):
        line = self.cycles.line()
        self.round(line, 1, disposition="accepted")
        self.assertIsNone(self.matching(1, generation=2))
        self.assertIsNone(review_verdicts.matching(self.store, attempt_id="review-attempt-9", generation=1))
        for attempt, generation in ((None, 1), ("", 1), ("review-attempt-1", True), ("review-attempt-1", None), ("review-attempt-1", "1")):
            with self.subTest(attempt=attempt, generation=generation):
                self.assertIsNone(review_verdicts.matching(self.store, attempt_id=attempt, generation=generation))

    def test_the_STOPPED_MANAGER_read_surface_publishes_it_and_the_unobserved_one_does_not(self):
        line = self.cycles.line()
        checkpoint, _, _ = self.round(line, 1, disposition="accepted")
        stage = {"stage_id": "job-a/review", "kind": "review", "attempt_id": "review-attempt-1",
                 "runtime": {"assignment": {"generation": 1}}}
        implementation = dict(stage, stage_id="job-a/implementation", kind="implementation")
        self.cycles.store.close()
        with ControlStore.open_readonly(self.cycles.control_path, incarnation="status-reader",
                                        clock=lambda: cycles.NOW) as control:
            surface = reading._ReadOnly(control)
            found = surface.review_verdict(attempt_id="review-attempt-1", generation=1)
            self.assertEqual((found["disposition"], found["checkpoint_id"]), ("accepted", checkpoint["checkpoint_id"]))
            class Observed:
                def observe_exchange(self, *ignored, **named):
                    return None
            observing = reading._Observing(control, Observed())
            self.assertEqual(observing.review_verdict(attempt_id="review-attempt-1", generation=1), found)
        # The projection hook: a review stage gains the member through a surface that can read; an
        # implementation stage never does; `Unobserved` holds no control store and leaves it absent.
        class Reads:
            def review_verdict(self, *, attempt_id, generation):
                return {"attempt_id": attempt_id, "generation": generation}
        published = projection._with_review_verdict(_document(stage), Reads())
        self.assertEqual(published["review_verdict"], {"attempt_id": "review-attempt-1", "generation": 1})
        self.assertNotIn("review_verdict", projection._with_review_verdict(_document(implementation), Reads()))
        self.assertNotIn("review_verdict", projection._with_review_verdict(_document(stage), Unobserved()))
        self.store = ControlStore.open(self.cycles.control_path, incarnation="manager-1", clock=lambda: cycles.NOW)
        self.cycles.store = self.store


def _document(stage):
    """One stage.status document with this stage's identities and empty axes."""
    from baton_v12.job_manager import documents
    return documents.stage_status(
        stage_id=stage["stage_id"], job_id="job-a", kind=stage["kind"], state="completed", work_id="work-a",
        profile_name="profile", profile_digest="sha256:" + "0" * 64, episode=1, offer_id="offer-a",
        attempt_id=stage["attempt_id"], episodes=[], corrections=0, allocation=None, allocations=[],
        gates=[], receipts=[], deferral=None, runtime=stage["runtime"], exchange=None, artifacts=[])


if __name__ == "__main__":
    unittest.main()
