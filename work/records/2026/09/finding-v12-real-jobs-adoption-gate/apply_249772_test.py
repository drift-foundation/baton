"""A check that `main` actually opens stores, over disposable documents."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

CASE = '''    def test_MAIN_opens_the_stores_and_publishes_an_outcome(self):
        """The entrypoint, invoked -- not described.

        Review 2026-09-23T17:56:23Z: `main` omitted the REQUIRED `clock` at
        both openers, so the one command this packet tells an operator to type
        could not open a store at all. Nothing short of calling it catches
        that, so this calls it.

        The documents are the ones the composer wrote for this fixture, the
        stores are fresh paths under the disposable root, and the bounds are
        small because the arithmetic is proved separately on a controlled
        clock.
        """
        import two_job_supervisor
        answer, into = self.composed_packet()
        self.assertEqual(answer.returncode, 0, answer.stderr)
        outcome = os.path.join(into, "outcome.json")
        status = two_job_supervisor.main([
            "--deployment", os.path.join(into, "deployment.json"),
            "--submission", os.path.join(into, "submission.json"),
            "--job-store", os.path.join(into, "jobs.sqlite3"),
            "--control-store", os.path.join(into, "control.sqlite3"),
            "--incarnation", "two-job-entrypoint",
            "--outcome", outcome,
            "--total-seconds", "12", "--cleanup-seconds", "4"])
        # THE STORES OPENED AND THE RUN PUBLISHED. `held` is the honest answer
        # for a run whose workers never start -- no engine is reached here --
        # and it is exit 1 rather than 0.
        self.assertIn(status, (0, 1))
        self.assertTrue(os.path.exists(outcome), "main published no outcome")
        with open(outcome, encoding="utf-8") as handle:
            published = json.load(handle)
        self.assertEqual(published["schema"], "baton.v12.two-job-outcome/1")
        self.assertEqual(published["job_ids"], ["job-a", "job-b"])
        self.assertIn("cleanup_sweeps", published)

'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    if "test_MAIN_opens_the_stores_and_publishes_an_outcome" in body:
        print("already present")
        return 0
    anchor = "    def test_an_unresolved_template_is_refused_by_name(self):"
    if anchor not in body:
        raise SystemExit("REFUSED: the anchor case is not in the file")
    place.write_text(body.replace(anchor, CASE + anchor, 1), encoding="utf-8")
    if "test_MAIN_opens_the_stores" not in place.read_text(encoding="utf-8"):
        raise SystemExit("REFUSED: the case is not in the file")
    print("entrypoint case added, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
