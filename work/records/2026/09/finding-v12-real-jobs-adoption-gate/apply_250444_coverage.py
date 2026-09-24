"""Claim-250444: the post-serving region, covered where it was only claimed.

Review 2026-09-23T19:22:24Z: "The new interruption test raises inside the
guarded turn and reaches normal finalization: it does not test failures outside
that guard. Add focused main failure/deadline and post-serving-finalization
coverage rather than treating an inner-turn interruption as whole-lifecycle
proof."

That is exactly right, and it is why my lifecycle claim survived: the only
fault I ever injected was one `_guarded` was built to absorb, so the region
between `gate.stop()` and the publication was never entered in anger by any
check I wrote. Four cases now do, each with a RECORDING termination so no real
signal handler is touched:

  * a finalization step faults -> the handler is restored, the outcome exists,
    the failure is named in it, the state is held, and the fault is re-raised;
  * the FINAL CLOCK faults -- the reviewer's own injection -- and the run now
    finishes, publishes, records `finished_at: null` and restores;
  * the PUBLICATION faults -> the handler is still restored and the failure
    reaches the caller rather than being swallowed into a tidy return;
  * and through the command: the deadline arrives before any verdict.

The pre-execution distinction is made honest in the same pass: the case that
was named `test_MAIN_opens_the_stores_and_publishes_an_outcome` does NOT reach
a publication -- the composition refuses before `supervise` is entered -- and
the operator contract should say so rather than claiming every path publishes.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "test_two_jobs.py"

ANCHOR = "    def test_a_reserve_outside_the_total_is_refused(self):"

ADDED = '''    def recording_termination(self):
        """A Termination that records rather than touching a handler.

        The reviewer used exactly this shape, and it is the right one: what is
        under test is whether `supervise` restores what it installed, not
        whether `signal.signal` works.
        """
        class Recording:
            def __init__(self):
                self.received = []
                self.installed = self.deferred = self.restored = False

            def install(self):
                self.installed = True
                return self

            def defer(self):
                self.deferred = True

            def restore(self):
                self.restored = True

        return Recording()

    def faulting_run(self, *, at, failure):
        """One bounded run with a fault injected AFTER serving.

        `at` names a module attribute of the supervisor that the run calls
        during finalization; the wrapper raises instead. Injecting through a
        real step rather than a sentinel keeps the region under test the one
        an operator's run actually executes.
        """
        import two_job_supervisor
        from baton_v12.job_manager import submit
        module, job, control, composed, outcome, bounds = self.supervised()
        submit(job, self.both_jobs())
        held = {"job": job, "control": control, "composed": composed}
        termination = self.recording_termination()
        original = getattr(two_job_supervisor, at)

        def faulting(*arguments, **members):
            del arguments, members
            raise failure

        setattr(two_job_supervisor, at, faulting)
        try:
            caught = None
            try:
                module.supervise(
                    job, control, composed, job_ids=("job-a", "job-b"),
                    bounds=bounds, outcome_path=outcome,
                    deployment_path=self.deployment_path(),
                    clock=lambda: "1970-01-01T00:00:00.000Z",
                    sleep=lambda _seconds: None,
                    monotonic=self.monotonic_for({}),
                    termination=termination,
                    turns=self.turning(held))
            except BaseException as raised:                   # noqa: BLE001
                caught = raised
        finally:
            setattr(two_job_supervisor, at, original)
        return termination, outcome, caught

    def test_a_fault_AFTER_serving_still_restores_and_still_publishes(self):
        """The region my `finally` did not cover, entered deliberately.

        Review 2026-09-23T19:22:24Z injected a fault after serving and cleanup
        and measured `installed=True, restored=False, outcome_exists=False`.
        My `finally` surrounded `_publish` alone while the comment above it
        said it surrounded everything. This asserts all three of the values
        that reading produced, with the signs they should have.
        """
        failure = RuntimeError("the verdict read faulted")
        termination, outcome, caught = self.faulting_run(
            at="verdicts_of", failure=failure)
        self.assertTrue(termination.installed)
        # THE THREE VALUES THE REVIEWER MEASURED.
        self.assertTrue(termination.restored)
        self.assertTrue(os.path.exists(outcome))
        self.assertIs(caught, failure)
        published = self.published(outcome)
        # AND THE DOCUMENT SAYS WHAT HAPPENED rather than reading like a run
        # that finished with nothing to report.
        self.assertIn("the verdict read faulted",
                      published["finalization_failure"])
        self.assertEqual(published["state"], "held")
        self.assertTrue(any("faulted after serving" in one
                            for one in published["held_because"]),
                        published["held_because"])

    def test_the_FINAL_CLOCK_faulting_no_longer_costs_the_outcome(self):
        """The reviewer's exact injection, and what it should cost now.

        A finalizer that re-raises on the same call it exists to recover from
        protects nothing, so `_moment_of` answers None and the document says
        the instant was never taken. The run is otherwise unharmed: it still
        collected both verdicts, so it is still settled.
        """
        import two_job_supervisor
        from baton_v12.job_manager import submit
        module, job, control, composed, outcome, bounds = self.supervised()
        submit(job, self.both_jobs())
        held = {"job": job, "control": control, "composed": composed}
        termination = self.recording_termination()
        # THE CLOCK FAULTS ONLY ONCE FINALIZATION IS REACHED, signalled by the
        # real step that runs immediately before the final instant is taken.
        state = {"final": False}
        original = two_job_supervisor.verdicts_of

        def reached(*arguments, **members):
            answer = original(*arguments, **members)
            state["final"] = True
            return answer

        def clock():
            if state["final"]:
                raise RuntimeError("the clock faulted")
            return "1970-01-01T00:00:00.000Z"

        two_job_supervisor.verdicts_of = reached
        try:
            measured = module.supervise(
                job, control, composed, job_ids=("job-a", "job-b"),
                bounds=bounds, outcome_path=outcome,
                deployment_path=self.deployment_path(),
                clock=clock, sleep=lambda _seconds: None,
                monotonic=self.monotonic_for({}), termination=termination,
                turns=self.turning(held))
        finally:
            two_job_supervisor.verdicts_of = original
        self.assertTrue(termination.restored)
        self.assertTrue(os.path.exists(outcome))
        published = self.published(outcome)
        self.assertIsNone(published["finished_at"])
        self.assertIsNone(published["finalization_failure"])
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        self.assertEqual(sorted(measured["verdicts"]), ["job-a", "job-b"])

    def test_a_PUBLICATION_that_faults_still_restores_the_handler(self):
        """The worst ending this run has, and the one it must not hide.

        Nothing reaches disk, so an operator cannot read what happened. The
        failure therefore has to reach the caller -- a tidy return here would
        be a run reporting success for an outcome nobody can find -- and the
        handler still has to come off this process.
        """
        from baton_v12.job_manager import submit
        module, job, control, composed, outcome, bounds = self.supervised()
        submit(job, self.both_jobs())
        held = {"job": job, "control": control, "composed": composed}
        termination = self.recording_termination()
        failure = OSError("the outcome could not be written")

        def publishing(*arguments, **members):
            del arguments, members
            raise failure

        original = module.baseline._publish                   # noqa: SLF001
        module.baseline._publish = publishing                 # noqa: SLF001
        try:
            with self.assertRaises(OSError) as caught:
                module.supervise(
                    job, control, composed, job_ids=("job-a", "job-b"),
                    bounds=bounds, outcome_path=outcome,
                    deployment_path=self.deployment_path(),
                    clock=lambda: "1970-01-01T00:00:00.000Z",
                    sleep=lambda _seconds: None,
                    monotonic=self.monotonic_for({}),
                    termination=termination, turns=self.turning(held))
        finally:
            module.baseline._publish = original               # noqa: SLF001
        self.assertIs(caught.exception, failure)
        self.assertTrue(termination.restored)
        self.assertFalse(os.path.exists(outcome))

'''

OLD_PREEXEC = '''    def test_MAIN_opens_the_stores_and_publishes_an_outcome(self):
        """The entrypoint, invoked -- not described.'''

NEW_PREEXEC = '''    def test_MAIN_refuses_BEFORE_it_can_owe_an_outcome(self):
        """The entrypoint, invoked -- not described. AND IT PUBLISHES NOTHING.

        Review 2026-09-23T19:22:24Z: "Main composition/submission failures
        still precede supervise and have no outcome path; either implement the
        existing requested failure guarantee or precisely distinguish
        pre-execution refusal in the operator contract, without claiming every
        path publishes." This case is that distinction, and its old name --
        `..._publishes_an_outcome` -- claimed the opposite of what it asserts.

        THE LINE IS WHERE `supervise` IS ENTERED. Before it, nothing has been
        admitted, no runtime exists and there is no account to render; the
        command refuses and writes no outcome. After it, every path publishes.
        A packet that promised an outcome for a refusal would be promising a
        document about a run that never began.'''

OLD_PREEXEC_TAIL = '''        # AND BOTH STORES EXIST, which is what "it opened them" means.
        for name in ("jobs.sqlite3", "control.sqlite3"):
            with self.subTest(store=name):
                self.assertTrue(os.path.exists(os.path.join(into, name)))'''

NEW_PREEXEC_TAIL = '''        # AND BOTH STORES EXIST, which is what "it opened them" means.
        for name in ("jobs.sqlite3", "control.sqlite3"):
            with self.subTest(store=name):
                self.assertTrue(os.path.exists(os.path.join(into, name)))
        # AND NO OUTCOME WAS WRITTEN, which is the contract this case now
        # states: the refusal precedes `supervise`, so there is nothing for an
        # outcome to account for.
        self.assertFalse(os.path.exists(outcome))'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "def faulting_run(self" in body:
        raise SystemExit("REFUSED: the post-serving cases are already present")
    body = swap(body, ANCHOR, ADDED + ANCHOR, "the reserve-case anchor")
    body = swap(body, OLD_PREEXEC, NEW_PREEXEC, "the pre-execution case")
    body = swap(body, OLD_PREEXEC_TAIL, NEW_PREEXEC_TAIL,
                "the pre-execution assertions")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    if "test_MAIN_opens_the_stores_and_publishes_an_outcome" in written:
        raise SystemExit("REFUSED: the misnamed case survives in the file")
    for present in ("def faulting_run(self",
                    "test_a_fault_AFTER_serving_still_restores",
                    "test_the_FINAL_CLOCK_faulting_no_longer_costs",
                    "test_a_PUBLICATION_that_faults_still_restores",
                    "test_MAIN_refuses_BEFORE_it_can_owe_an_outcome"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("post-serving coverage added, parsed and verified on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
