"""Claim-249945: the supervised success — four attempts, two frozen verdicts."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

CASE = '''    def turning(self, held):
        """The deterministic worker turn, where the container would be.

        One callback, invoked each serving tick with the gate. For every
        attempt the gate has launched and not yet answered, it runs the
        fixture's own turn -- the same one every accepted v12 lifecycle case
        uses -- writing an implementation body or a review report by kind.
        """
        answered = set()

        def turns(gate):
            for attempt_id, kind in sorted(gate.launched.items()):
                if attempt_id in answered:
                    continue
                mounted = self.mounted_at(held["composed"], attempt_id)
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
                self.turn(held["control"], kind, attempt_id, mounted,
                          edits=edits)
                answered.add(attempt_id)

        return turns

    def test_the_SUPERVISED_run_reaches_four_attempts_and_two_verdicts(self):
        """R4's success: the whole bounded run, over the composed deployment.

        The supervisor serves, the deterministic turn answers where a
        container would, both Jobs reach their own reviewers, both verdicts
        are DERIVED from their own frozen results, and every runtime this run
        launched has a positive cleanup.
        """
        import two_job_supervisor
        from baton_v12.job_manager import submit
        job, control, composed = self.serving_two(**self.traversing())
        submit(job, self.both_jobs())
        held = {"job": job, "control": control, "composed": composed}
        outcome = os.path.join(self.packet_root(), "supervised-outcome.json")
        measured = two_job_supervisor.supervise(
            job, control, composed, job_ids=("job-a", "job-b"),
            bounds={"total_seconds": 600, "cleanup_seconds": 60},
            outcome_path=outcome, deployment_path=self.deployment_path(),
            clock=lambda: "1970-01-01T00:00:00.000Z",
            sleep=lambda _seconds: None,
            monotonic=self.monotonic_for({}),
            turns=self.turning(held))
        self.assertEqual(sum(measured["admissions"].values()), 4,
                         measured["admissions"])
        self.assertEqual(sorted(measured["verdicts"]), ["job-a", "job-b"])
        for job_id, verdict in measured["verdicts"].items():
            with self.subTest(job=job_id):
                self.assertEqual(verdict["verdict"], "accepted")
        self.assertEqual(measured["outstanding_cleanup"], [])
        self.assertEqual(measured["state"], "settled", measured["held_because"])
        with open(outcome, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["state"], "settled")

'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    if "test_the_SUPERVISED_run_reaches_four_attempts" in body:
        print("already present")
        return 0
    if "import copy" not in body:
        body = body.replace("import json\n", "import copy\nimport json\n", 1)
    anchor = "    def test_a_serving_failure_still_publishes_an_outcome(self):"
    if anchor not in body:
        raise SystemExit("REFUSED: the anchor case is not in the file")
    place.write_text(body.replace(anchor, CASE + anchor, 1), encoding="utf-8")
    if "test_the_SUPERVISED_run_reaches_four_attempts" not in \
            place.read_text(encoding="utf-8"):
        raise SystemExit("REFUSED: the case is not in the file")
    print("supervised success case added, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
