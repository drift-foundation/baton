"""Prove the new success rule bites: a run that produced nothing is held."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CASE = '''    def test_a_run_that_admitted_nothing_is_HELD_rather_than_settled(self):
        """The defect this rule closes, asserted rather than trusted.

        Review 2026-09-23T17:44:56Z drove an EMPTY serve and got `settled`
        with zero admissions and no verdicts, because "settled" had meant
        "nothing to complain about". Success is what the run produced.
        """
        import two_job_supervisor
        from baton_v12.job_manager import JobStore
        del JobStore
        module, job, control, composed, outcome, bounds = self.supervised()
        measured = module.supervise(
            job, control, composed, job_ids=("job-a", "job-b"),
            bounds=bounds, outcome_path=outcome,
            deployment_path=self.deployment_path(),
            clock=lambda: "1970-01-01T00:00:00.000Z",
            sleep=lambda _seconds: None,
            monotonic=self.monotonic_for({}))
        # NOTHING WAS SUBMITTED BY THIS PATH, so nothing could be admitted.
        self.assertEqual(measured["state"], "held")
        self.assertTrue(any("admitted" in one
                            for one in measured["held_because"]),
                        measured["held_because"])
        self.assertEqual(self.published(outcome)["state"], "held")
        del two_job_supervisor

'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    if "test_a_run_that_admitted_nothing_is_HELD" in body:
        print("already added")
        return 0
    anchor = "    def test_a_reserve_outside_the_total_is_refused(self):"
    body = body.replace(anchor, CASE + anchor, 1)
    # the empty-serve path must NOT submit, so `supervised` needs a flag
    body = body.replace(
        '''        job, control, composed = self.serving_two(**self.traversing())
        submit(job, self.both_jobs())''',
        '''        job, control, composed = self.serving_two(**self.traversing())
        if submitted:
            submit(job, self.both_jobs())''')
    body = body.replace(
        '''    def supervised(self, *, bounds=None, ticks=None, fail=False,
                   interrupt=False):''',
        '''    def supervised(self, *, bounds=None, ticks=None, fail=False,
                   interrupt=False, submitted=False):''')
    body = body.replace(
        '''        module, job, control, composed, outcome, bounds = self.supervised(
            **members)''',
        '''        module, job, control, composed, outcome, bounds = self.supervised(
            submitted=True, **members)''')
    place.write_text(body, encoding="utf-8")
    print("empty-run case added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
