"""R3: both Jobs' frozen attributed verdicts, read back from the store."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CASES = '''class EachJobCollectsItsOwnFROZENAttributedVerdict(ArrangedCase):
    """R3 in full: two verdicts, each DERIVED from its own frozen result.

    Reaching two reviewers is not collecting two verdicts, and the previous
    claim said so rather than implying otherwise. This drives both review
    turns to completion and then reads each verdict back the way the manager
    itself does -- `review_driver.review_verdict_from_result`, which refuses
    unless the frozen result belongs to this attachment's attempt, its
    retained manifest names the same result and the same assignment at the
    same generation, and the base, head and tree the reviewer reports are the
    ones the checkpoint's own evidence records.
    """

    def verdict_for(self, held, job_id):
        """One Job's attachment and the verdict derived from its own result."""
        from baton_v12.job_manager import review_driver
        from baton_v12.worker_manager import review_cycles
        line = self.line_of(held.composed, job_id)["line_id"]
        checkpoint = review_cycles.integration_checkpoint(held.control, line)
        self.assertIsNotNone(checkpoint,
                             f"{job_id} froze no reviewed checkpoint")
        attachment = review_cycles.review_for_attempt(
            held.control, self.reviewed_attempt(held, job_id))
        self.assertIsNotNone(attachment,
                             f"{job_id} has no review attachment")
        return attachment, review_driver.review_verdict_from_result(
            held.control, attachment_id=attachment["attachment_id"])

    def reviewed_attempt(self, held, job_id):
        return (held.first_review if job_id == "job-a"
                else held.second_review)

    def both(self):
        return self.both_accepted()

    def test_both_verdicts_are_derived_from_their_own_frozen_results(self):
        held = self.both()
        held_verdicts = {}
        for job_id in ("job-a", "job-b"):
            with self.subTest(job=job_id):
                attachment, verdict = self.verdict_for(held, job_id)
                self.assertEqual(verdict["verdict"], "accepted")
                self.assertEqual(verdict["attempt_id"],
                                 attachment["runtime_attempt_id"])
                held_verdicts[job_id] = verdict
        # TWO VERDICTS, NOT ONE COUNTED TWICE.
        self.assertNotEqual(held_verdicts["job-a"]["attachment_id"],
                            held_verdicts["job-b"]["attachment_id"])
        self.assertNotEqual(held_verdicts["job-a"]["result_id"],
                            held_verdicts["job-b"]["result_id"])

    def test_each_verdict_is_bound_to_its_own_checkpoint_and_objects(self):
        """The cross-binding, which is what makes a claim a verdict."""
        from baton_v12.worker_manager import checkpoint_of
        held = self.both()
        for job_id in ("job-a", "job-b"):
            with self.subTest(job=job_id):
                attachment, verdict = self.verdict_for(held, job_id)
                self.assertEqual(verdict["checkpoint_id"],
                                 attachment["checkpoint_id"])
                held_checkpoint = checkpoint_of(held.control,
                                                verdict["checkpoint_id"])
                evidence = held_checkpoint.get("evidence") or {}
                for name in ("base", "head", "tree"):
                    if evidence.get(name) is not None:
                        self.assertEqual(verdict[name], evidence[name])

    def test_each_reviewer_is_the_one_configured_for_that_job(self):
        """Independence, read from the retained attachment rows."""
        held = self.both()
        identities = {}
        for job_id, worker in (("job-a", "review-worker"),
                               ("job-b", "review-worker-b")):
            attachment, _verdict = self.verdict_for(held, job_id)
            identities[job_id] = attachment["reviewer_worker_id"]
            with self.subTest(job=job_id):
                self.assertEqual(attachment["reviewer_worker_id"], worker)
        self.assertNotEqual(identities["job-a"], identities["job-b"])

    def test_no_correction_round_opened_for_either_job(self):
        """`correction_policy: "decline"` is composed; this is it holding."""
        from baton_v12.worker_manager import review_cycles
        held = self.both()
        for job_id in ("job-a", "job-b"):
            with self.subTest(job=job_id):
                states = self.states_for(held.job, held.composed, job_id)
                self.assertEqual(states["review"], "completed")
                line = self.line_of(held.composed, job_id)["line_id"]
                self.assertEqual(review_cycles.line_status(
                    held.control, line)["state"], "accepted")


def load_tests(loader, standard, pattern):'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    if "EachJobCollectsItsOwnFROZENAttributedVerdict" in body:
        print("already added")
        return 0
    body = body.replace("def load_tests(loader, standard, pattern):",
                        CASES, 1)
    place.write_text(body, encoding="utf-8")
    print("R3 cases added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
