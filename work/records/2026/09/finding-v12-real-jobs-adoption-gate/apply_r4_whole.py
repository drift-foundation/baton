"""R4: the whole bounded path, driven over the real two-Job deployment."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CASES = '''class TheBoundedTwoJobRunStopsAndAccountsForItself(ArrangedCase):
    """R4's whole path: serve, stop, close, cancel, clean up, publish.

    DRIVEN OVER THE REAL COMPOSED DEPLOYMENT -- this arrangement's own `/2`
    document, the accepted fixture's stores and its deterministic turn -- so
    what is measured is the supervisor's behaviour rather than a recorder's.
    The clock is injected, which is how a 600-second bound is proved in
    milliseconds without pretending the arithmetic is different.
    """

    def supervised(self, *, bounds=None, ticks=None, fail=False,
                   interrupt=False):
        import two_job_supervisor
        from baton_v12.job_manager import submit
        job, control, composed = self.serving_two(**self.traversing())
        submit(job, self.both_jobs())
        moments = iter(ticks or range(0, 10_000, 5))

        def monotonic():
            try:
                return float(next(moments))
            except StopIteration:                            # pragma: no cover
                return 1e9

        held = composed
        if fail or interrupt:
            failing = RuntimeError("the serving loop faulted")
            stopping = KeyboardInterrupt("an operator asked it to stop")

            class Faulting:
                def __init__(self, inner):
                    self._inner = inner
                    self._ticks = 0

                def admit(self, stage, job):
                    self._ticks += 1
                    if self._ticks > 1:
                        raise stopping if interrupt else failing
                    return self._inner.admit(stage, job)

                def __getattr__(self, name):
                    return getattr(self._inner, name)

            held = Faulting(composed)
        outcome = os.path.join(self.packet_root(), "outcome.json")
        return two_job_supervisor, job, control, held, outcome, bounds or {
            "total_seconds": 600, "cleanup_seconds": 60}

    def packet_root(self):
        held = os.path.join(self.root, "supervised")
        os.makedirs(held, exist_ok=True)
        return held

    def deployment_path(self):
        """A document carrying this run's retention policy, for the journal."""
        place = os.path.join(self.packet_root(), "deployment.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(self.composed_document(**self.two_jobs()), handle,
                      indent=2, sort_keys=True)
        return place

    def run(self, **members):
        module, job, control, composed, outcome, bounds = self.supervised(
            **members)
        return module, module.supervise(
            job, control, composed, job_ids=("job-a", "job-b"),
            bounds=bounds, outcome_path=outcome,
            deployment_path=self.deployment_path(),
            clock=lambda: "1970-01-01T00:00:00.000Z",
            sleep=lambda _seconds: None,
            monotonic=self.monotonic_for(members)), outcome

    def monotonic_for(self, members):
        held = iter(members.get("ticks") or range(0, 10_000, 5))

        def monotonic():
            try:
                return float(next(held))
            except StopIteration:                            # pragma: no cover
                return 1e9

        return monotonic

    def published(self, outcome):
        with open(outcome, encoding="utf-8") as handle:
            return json.load(handle)

    def test_the_run_stops_at_total_minus_cleanup_and_publishes(self):
        _module, measured, outcome = self.run()
        self.assertEqual(measured["serving_bound_seconds"], 540)
        self.assertEqual(measured["stopped"], "serving-bound-exceeded")
        self.assertEqual(self.published(outcome)["schema"],
                         "baton.v12.two-job-outcome/1")
        self.assertEqual(measured["caps"], {"implementation": 2, "review": 2})

    def test_admission_is_closed_before_anything_is_cancelled(self):
        _module, measured, _outcome = self.run()
        self.assertTrue(measured["admission_closed_before_cancellation"])
        self.assertLessEqual(sum(measured["admissions"].values()), 4)

    def test_the_cleanup_window_is_inside_the_total(self):
        _module, measured, _outcome = self.run()
        self.assertGreaterEqual(measured["cleanup_window_seconds"], 0)
        self.assertLessEqual(measured["cleanup_window_seconds"],
                             measured["bounds"]["cleanup_seconds"])

    def test_a_serving_failure_still_publishes_an_outcome(self):
        _module, measured, outcome = self.run(fail=True)
        self.assertEqual(measured["stopped"], "serving-failed")
        self.assertIsNotNone(measured["serving_failure"])
        self.assertEqual(measured["state"], "held")
        self.assertTrue(self.published(outcome)["held_because"])

    def test_an_interruption_publishes_the_outcome_and_still_raises(self):
        import two_job_supervisor
        with self.assertRaises(baseline_interrupted()) as caught:
            self.run(interrupt=True)
        del caught, two_job_supervisor
        # THE OUTCOME IS ON DISK EVEN THOUGH THE CALL RAISED.
        outcome = os.path.join(self.packet_root(), "outcome.json")
        self.assertTrue(os.path.exists(outcome))
        self.assertEqual(self.published(outcome)["stopped"], "interrupted")

    def test_a_reserve_outside_the_total_is_refused(self):
        import two_job_supervisor
        module, job, control, composed, outcome, _bounds = self.supervised()
        with self.assertRaises(two_job_supervisor.SupervisorRefusal):
            module.supervise(job, control, composed,
                             job_ids=("job-a", "job-b"),
                             bounds={"total_seconds": 60,
                                     "cleanup_seconds": 60},
                             outcome_path=outcome,
                             deployment_path=self.deployment_path())


def baseline_interrupted():
    import two_job_supervisor
    return two_job_supervisor.baseline.SupervisorInterrupted


def load_tests(loader, standard, pattern):'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    if "TheBoundedTwoJobRunStopsAndAccountsForItself" in body:
        print("already added")
        return 0
    body = body.replace("def load_tests(loader, standard, pattern):",
                        CASES, 1)
    place.write_text(body, encoding="utf-8")
    print("R4 whole-path cases added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
