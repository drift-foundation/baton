"""R3 fix: find each attachment by attempt and generation, as the reader asks."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

NEW = '''    def verdict_for(self, held, job_id):
        """One Job's attachment and the verdict derived from its own result.

        `review_for_attempt(store, *, attempt_id, generation)` -- the
        generation is not optional, because an attempt may be offered more
        than once and an attachment belongs to ONE of those assignments.
        """
        from baton_v12.job_manager import review_driver
        from baton_v12.worker_manager import review_cycles
        attempt = self.reviewed_attempt(held, job_id)
        attachment = review_cycles.review_for_attempt(
            held.control, attempt_id=attempt,
            generation=self.generation_of(held, attempt))
        self.assertIsNotNone(attachment,
                             f"{job_id} has no review attachment")
        return attachment, review_driver.review_verdict_from_result(
            held.control, attachment_id=attachment["attachment_id"])

    def generation_of(self, held, attempt_id):
        """The assignment generation this attempt's review was attached at."""
        from baton_v12.worker_manager import attempt_of
        held_attempt = attempt_of(held.control, attempt_id)
        for name in ("assignment_generation", "generation"):
            if held_attempt.get(name) is not None:
                return held_attempt[name]
        raise AssertionError(
            f"{attempt_id} records no assignment generation: "
            f"{sorted(held_attempt)}")
'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    start = body.index("    def verdict_for(self, held, job_id):")
    end = body.index("    def reviewed_attempt(self, held, job_id):")
    body = body[:start] + NEW + "\n" + body[end:]
    place.write_text(body, encoding="utf-8")
    print("R3 attachment lookup corrected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
