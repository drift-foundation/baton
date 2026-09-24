"""R3: read the generation from the preparation record the worker holds."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

NEW = '''    def generation_of(self, held, attempt_id):
        """The assignment generation this attempt was prepared at.

        Taken from the PREPARATION RECORD the worker that prepared this
        attempt holds -- the same fact `preparing` uses to answer which worker
        that was -- rather than from a store reader this build does not
        export. `review_for_attempt` fences an attachment to one activated
        generation, so this is the operand it needs.
        """
        _worker, prepared = self.preparing(held.composed, attempt_id)
        return prepared["generation"]
'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    start = body.index("    def generation_of(self, held, attempt_id):")
    end = body.index("    def reviewed_attempt(self, held, job_id):")
    body = body[:start] + NEW + "\n" + body[end:]
    place.write_text(body, encoding="utf-8")
    print("generation lookup corrected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
