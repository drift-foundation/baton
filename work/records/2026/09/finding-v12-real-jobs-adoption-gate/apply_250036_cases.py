"""Claim-250036: the turn takes a context; `main` reaches a real success."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

SUCCESS = '''    def answering(self):
        """The deterministic turn, driven from the RUNTIME CONTEXT.

        The supervisor hands each tick's callback the composed operations, so
        the turn can reach the attempt's mounted workspace -- which is what a
        container would be writing into. Without that context the callback
        could do no work, which is exactly why the first entry-point case
        proved nothing.
        """
        answered = set()

        def turns(gate, context):
            for attempt_id, kind in sorted(gate.launched.items()):
                if attempt_id in answered:
                    continue
                mounted = self.mounted_at(context["operations"], attempt_id)
                if not mounted:
                    continue
                if kind == "implementation":
                    edits = {"harness.py": "print('answered')\\n"}
                    if gate.job_of(attempt_id) == "job-b":
                        edits = {"feature.py": self.B_FEATURE,
                                 "feature_check.py": self.B_CHECK}
                else:
                    report = copy.deepcopy(self.REPORT)
                    report["verdict"] = "accepted"
                    edits = {"review-report.json": json.dumps(report)}
                self.turn(context["control"], kind, attempt_id, mounted,
                          edits=edits)
                answered.add(attempt_id)

        return turns

    def test_MAIN_reaches_four_attempts_two_verdicts_and_settles(self):
        """R4's success THROUGH THE DOCUMENTED COMMAND.

        The clock is injected -- `monotonic` and `sleep` are operands with
        PRODUCTION DEFAULTS, so an operator's invocation is unchanged and this
        witness does not spend eight real seconds proving arithmetic that is
        proved on a controlled clock elsewhere.
        """
        import two_job_supervisor
        argv, outcome, _into = self.entrypoint(total=600, cleanup=60)
        moments = iter(range(0, 10_000, 5))
        status = two_job_supervisor.main(
            argv, turns=self.answering(),
            monotonic=lambda: float(next(moments)),
            sleep=lambda _seconds: None,
            **self.disposable(_into))
        with open(outcome, encoding="utf-8") as handle:
            published = json.load(handle)
        self.assertEqual(published["admissions"],
                         {"implementation": 2, "review": 2})
        self.assertEqual(sorted(published["verdicts"]), ["job-a", "job-b"])
        for job_id, verdict in published["verdicts"].items():
            with self.subTest(job=job_id):
                self.assertEqual(verdict["verdict"], "accepted")
        self.assertEqual(published["outstanding_cleanup"], [])
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        self.assertEqual(status, 0)

'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    # the supervisor case's callback now takes the context too
    body = body.replace("        def turns(gate):\n",
                        "        def turns(gate, context):\n")
    body = body.replace(
        '                mounted = self.mounted_at(held["composed"], attempt_id)',
        '                mounted = self.mounted_at(context["operations"],\n'
        '                                          attempt_id)')
    if "test_MAIN_reaches_four_attempts_two_verdicts_and_settles" not in body:
        anchor = "    def test_an_unresolved_template_is_refused_by_name(self):"
        if anchor not in body:
            raise SystemExit("REFUSED: the anchor case is not in the file")
        body = body.replace(anchor, SUCCESS + anchor, 1)
    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    if "def turns(gate):" in written:
        raise SystemExit("REFUSED: a context-less callback survives")
    for present in ("def answering(self):",
                    "test_MAIN_reaches_four_attempts_two_verdicts_and_settles"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("context callbacks and the main success case added, verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
