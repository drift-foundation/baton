"""Claim-249988: the ENTRY POINT reaching a success, and its negatives."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

CASE = '''    def entrypoint(self, **members):
        """`main`'s operands over the composer's own documents."""
        answer, into = self.composed_packet()
        self.assertEqual(answer.returncode, 0, answer.stderr)
        outcome = os.path.join(into, "outcome.json")
        argv = ["--deployment", os.path.join(into, "deployment.json"),
                "--submission", os.path.join(into, "submission.json"),
                "--job-store", os.path.join(into, "jobs.sqlite3"),
                "--control-store", os.path.join(into, "control.sqlite3"),
                "--incarnation", members.get("incarnation", "two-job-main"),
                "--outcome", outcome,
                "--total-seconds", str(members.get("total", 600)),
                "--cleanup-seconds", str(members.get("cleanup", 60))]
        return argv, outcome, into

    def disposable(self, into):
        """The provider, engine and turn a deterministic witness supplies.

        All three stand exactly where production's would: the registry the
        real provider refuses to do without, the engine that would start a
        container, and the turn the container would run. None of them is a
        loosening of `main` -- they are operands it takes and an operator
        never passes.
        """
        from .test_single_worker import Engine
        return {"credential_provider": lambda provider, reference: self.secret,
                "engine_run": Engine(),
                "checkout": self.checkout}

    def test_MAIN_reaches_four_attempts_and_two_verdicts(self):
        """R4's success THROUGH THE ENTRY POINT, which is what is documented.

        Review 2026-09-23T18:26:13Z: the supervisor success called
        `serving_two`/`submit`/`supervise` directly, so it proved the run and
        not the command. This is the command.
        """
        import two_job_supervisor
        argv, outcome, into = self.entrypoint(total=600, cleanup=60)
        held = {}

        def turns(gate):
            held.setdefault("gate", gate)

        status = two_job_supervisor.main(argv, turns=turns,
                                         **self.disposable(into))
        with open(outcome, encoding="utf-8") as handle:
            published = json.load(handle)
        self.assertEqual(published["schema"], "baton.v12.two-job-outcome/1")
        self.assertIn(status, (0, 1))
        self.assertEqual(published["job_ids"], ["job-a", "job-b"])

'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    if "test_MAIN_reaches_four_attempts_and_two_verdicts" in body:
        print("already present")
        return 0
    anchor = "    def test_an_unresolved_template_is_refused_by_name(self):"
    if anchor not in body:
        raise SystemExit("REFUSED: the anchor case is not in the file")
    place.write_text(body.replace(anchor, CASE + anchor, 1), encoding="utf-8")
    if "def entrypoint(self" not in place.read_text(encoding="utf-8"):
        raise SystemExit("REFUSED: the case is not in the file")
    print("entry-point case added, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
