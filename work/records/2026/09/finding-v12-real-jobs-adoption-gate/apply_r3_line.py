"""R3: read each line's state through the reader the witness already uses."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

NEW = '''    def test_no_correction_round_opened_for_either_job(self):
        """`correction_policy: "decline"` is composed; this is it holding.

        `line_of` rather than `line_status`: the latter answers an operator's
        whole report and needs a storage-usage operand this witness has no
        business supplying. The line's own recorded state is the fact.
        """
        from baton_v12.worker_manager import line_of
        held = self.both()
        for job_id in ("job-a", "job-b"):
            with self.subTest(job=job_id):
                states = self.states_for(held.job, held.composed, job_id)
                self.assertEqual(states["review"], "completed")
                line = self.line_of(held.composed, job_id)["line_id"]
                self.assertEqual(line_of(held.control, line)["state"],
                                 "accepted")
'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    start = body.index(
        "    def test_no_correction_round_opened_for_either_job(self):")
    end = body.index("def load_tests(loader, standard, pattern):")
    body = body[:start] + NEW + "\n\n" + body[end:]
    place.write_text(body, encoding="utf-8")
    print("line-state reader corrected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
