"""Claim-250287: the SUCCESS through the documented command, ASSERTED.

Review 2026-09-23T19:04:38Z: "Finish these corrections plus live-composition
status capture, asserted main success/negatives/lifecycle protection/generation
distinction..." Until now the only success through `main` lived in a diagnostic
that asserts nothing, so a regression in the command would have been read by a
human or not at all -- which is exactly how the shadowed callback survived two
corrections.

Three cases are added to the class that owns the command:

  * the whole run, asserted -- four admissions, two derived verdicts, positive
    cleanup, the REAL assignment generations, and a supported `status` read
    taken while the composition is open;
  * the lifecycle: an interruption inside the turn still publishes the outcome
    and still raises;
  * and the existing no-turn case, corrected -- its docstring claimed a
    success through `main` was unproved, which is no longer true, and it now
    asserts `held` rather than accepting either state.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "test_two_jobs.py"

ANCHOR = "    def answering(self):"

ADDED = '''    def commanded(self, *, total=600, cleanup=60, wrap=None):
        """One whole run of the DOCUMENTED command, and what it read.

        THE CLOCK IS CONTROLLED. `main` serves on the real wall clock by
        default, and it should; a witness that had to wait out 540 real
        seconds would be a witness nobody runs. The monotonic seam steps five
        seconds a tick, so the serving bound is reached after a fixed number
        of ticks and this case is deterministic.

        THE STATUS READ IS TAKEN FROM INSIDE THE TURN, where `operations` is
        open. `projection.status` asks the composition whether the canonical
        store was read at all -- that is what its `canonical` member reports
        -- so a read taken after the command returns has nothing to ask and
        raises. Every earlier receipt printed that AttributeError instead of
        stage states.
        """
        import two_job_supervisor
        from baton_v12.job_manager.projection import status as projected
        from tests.job_manager import fixtures
        argv, outcome, into = self.entrypoint(total=total, cleanup=cleanup)
        inner = self.answering()
        captured = []

        def turns(gate, context):
            if wrap is not None:
                wrap(gate, context)
            inner(gate, context)
            captured.append({
                "canonical": projected(context["job"], context["operations"],
                                       observed_at=fixtures.NOW)["canonical"],
                "jobs": {one["job_id"]: {two["kind"]: two["state"]
                                         for two in one["stages"]}
                         for one in projected(
                             context["job"], context["operations"],
                             observed_at=fixtures.NOW)["jobs"]}})

        moments = iter(range(0, 10_000, 5))
        status = two_job_supervisor.main(
            argv, turns=turns, monotonic=lambda: float(next(moments)),
            sleep=lambda _seconds: None, **self.disposable(into))
        with open(outcome, encoding="utf-8") as handle:
            return status, json.load(handle), captured, into

    def test_the_DOCUMENTED_COMMAND_reaches_four_attempts_and_two_verdicts(
            self):
        """R4's success through the COMMAND, not through `supervise`.

        The command opens both stores, composes the deployment `two_jobs.py`
        wrote, submits, serves bounded, stops, cleans up and publishes. What
        this asserts is what it PRODUCED: four admissions, two verdicts each
        derived from its own frozen result, and no runtime left without a
        positive cleanup.

        This was observed once and not asserted, and then not reproduced --
        because `answering` had been shadowed by a second definition that
        never set the composed handle, so every turn raised and no
        implementation completed. An observation nothing asserts is how that
        survived.
        """
        status, published, captured, into = self.commanded()
        del into
        self.assertEqual(published["schema"], "baton.v12.two-job-outcome/1")
        self.assertEqual(published["job_ids"], ["job-a", "job-b"])
        self.assertEqual(published["admissions"],
                         {"implementation": 2, "review": 2})
        self.assertEqual(sorted(published["verdicts"]), ["job-a", "job-b"])
        for job_id, verdict in sorted(published["verdicts"].items()):
            with self.subTest(job=job_id):
                self.assertEqual(verdict["verdict"], "accepted")
        self.assertEqual(published["outstanding_cleanup"], [])
        self.assertEqual(published["uncertainty"], [])
        self.assertEqual(published["gate_refusals"], [])
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        self.assertEqual(published["held_because"], [])
        self.assertEqual(published["stopped"], "serving-bound-exceeded")
        # AND THE COMMAND'S OWN EXIT STATUS SAYS SO. An operator reads that
        # before reading any document.
        self.assertEqual(status, 0)
        self.assertTrue(captured, "no tick took a status read")

    def test_the_COMMAND_reports_a_SUPPORTED_status_with_a_live_composition(
            self):
        """The read an operator takes while the run is up.

        ADOPTION-247941.md step 7 tells an operator to ask what is running.
        Every diagnostic receipt before this one answered that question with
        `AttributeError: 'NoneType' object has no attribute 'canonical'`,
        because it asked after the command had closed the composition. This
        asks during, which is the supported way, and asserts both ends of the
        run: every stage offered before any turn answered, and every stage
        completed by the last tick.
        """
        _status, published, captured, _into = self.commanded()
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        for one in (captured[0], captured[-1]):
            with self.subTest(read=captured.index(one)):
                # THE CANONICAL STORE WAS READ, which is the difference
                # between "nothing is running" and "nobody looked".
                self.assertIs(one["canonical"], True)
                self.assertEqual(sorted(one["jobs"]), ["job-a", "job-b"])
                for job_id, stages in sorted(one["jobs"].items()):
                    self.assertEqual(sorted(stages),
                                     ["implementation", "review"], job_id)
        self.assertEqual(
            {job_id: stages["implementation"]
             for job_id, stages in captured[0]["jobs"].items()},
            {"job-a": "offered", "job-b": "offered"})
        self.assertEqual(
            captured[-1]["jobs"],
            {"job-a": {"implementation": "completed", "review": "completed"},
             "job-b": {"implementation": "completed", "review": "completed"}})

    def test_the_COMMAND_records_the_REAL_assignment_generations(self):
        """The ASSIGNMENT axis, through the command, from the store it wrote.

        `allocation.generation` is the POOL generation, and the two axes
        sharing the value 1 is the easiest false pass available here -- which
        is why this reads `attempts.assignment_of` back out of the control
        store the command left behind and compares it to what the run
        published, attempt by attempt.
        """
        from baton_v12.worker_manager import ControlStore
        from baton_v12.worker_manager import attempts as attempt_rows
        _status, published, _captured, into = self.commanded()
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        self.assertEqual(len(published["admitted_attempts"]), 4)
        control = ControlStore.open_readonly(
            os.path.join(into, "control.sqlite3"),
            incarnation="assignment-readback",
            clock=lambda: "1970-01-01T00:00:00.000Z")
        try:
            for attempt_id in published["admitted_attempts"]:
                with self.subTest(attempt=attempt_id):
                    recorded = published["generations"].get(attempt_id)
                    self.assertIsNotNone(recorded)
                    self.assertEqual(
                        attempt_rows.assignment_of(
                            control, attempt_id)["generation"], recorded)
        finally:
            control.close()

    def test_an_INTERRUPTION_through_the_command_publishes_and_still_raises(
            self):
        """The whole lifecycle is protected, not just the serving loop.

        A SIGTERM arriving mid-run is owed an outcome: the operator who sent
        it has to be able to read what the run left behind. This raises from
        inside the turn, where a container would be, and asserts that the
        command still wrote the document and still let the interruption
        through rather than swallowing it into a tidy exit status.
        """
        def interrupting(_gate, _context):
            raise KeyboardInterrupt("the operator stopped this run")

        with self.assertRaises(baseline_interrupted()):
            self.commanded(wrap=interrupting)
        # THE DOCUMENT IS ON DISK EVEN THOUGH THE COMMAND RAISED.
        outcome = os.path.join(self.packet_root(), "run", "outcome.json")
        self.assertTrue(os.path.exists(outcome))
        with open(outcome, encoding="utf-8") as handle:
            published = json.load(handle)
        self.assertEqual(published["stopped"], "interrupted")
        self.assertEqual(published["state"], "held")
        self.assertTrue(published["interruptions"])

'''

OLD_NOTURN = '''        WHAT IT DOES NOT PROVE is four attempts and two verdicts THROUGH
        `main`. The turn callback here answers nothing, because a turn needs
        the mounted attempt path and `main` does not hand one out -- so the
        run reports `held` with `serving-bound-exceeded`, which is the honest
        outcome for a run whose workers never answered. The success is proved
        on `supervise` and the gap is named rather than papered over.
        """'''

NEW_NOTURN = '''        THIS ONE IS THE NEGATIVE, and it is deliberately still here now that
        the success is asserted beside it: a callback that answers nothing
        leaves both implementations unfinished, so the run collects no verdict
        and reports `held`. Success has to be what the run PRODUCED, and the
        way to show that is a run that produced nothing and says so.
        """'''

OLD_TAIL = '''        self.assertEqual(published["schema"], "baton.v12.two-job-outcome/1")
        self.assertIn(status, (0, 1))
        self.assertEqual(published["job_ids"], ["job-a", "job-b"])'''

NEW_TAIL = '''        self.assertEqual(published["schema"], "baton.v12.two-job-outcome/1")
        self.assertEqual(published["job_ids"], ["job-a", "job-b"])
        # HELD, NOT "either" -- a run whose workers never answered has not
        # done its work, and accepting `0` here would accept the defect the
        # shadowed callback produced.
        self.assertEqual(status, 1)
        self.assertEqual(published["state"], "held")
        self.assertEqual(published["verdicts"], {})
        self.assertTrue(any("no attributed verdict" in one
                            for one in published["held_because"]),
                        published["held_because"])
        self.assertTrue(held.get("gate"), "the turn was never invoked")'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "def commanded(self" in body:
        raise SystemExit("REFUSED: the command cases are already present")
    body = swap(body, ANCHOR, ADDED + ANCHOR, "the callback anchor")
    body = swap(body, OLD_NOTURN, NEW_NOTURN, "the no-turn docstring")
    body = swap(body, OLD_TAIL, NEW_TAIL, "the no-turn assertions")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for present in (
            "def commanded(self",
            "test_the_DOCUMENTED_COMMAND_reaches_four_attempts",
            "test_the_COMMAND_reports_a_SUPPORTED_status_with_a_live",
            "test_the_COMMAND_records_the_REAL_assignment_generations",
            "test_an_INTERRUPTION_through_the_command_publishes"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("the command cases are added, parsed and verified on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
