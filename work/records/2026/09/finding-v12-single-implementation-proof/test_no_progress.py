"""A run that cannot finish stops when it stops moving. W239528.

Owner pass 243171, after the successful baseline run: "prevent a terminal
non-progressing condition from waiting for the overall 900-second bound...
Correct interruption reporting to retain the outcome and print its location
clearly. Reproduce with deterministic tests through actual composition,
preserving context integrity and no-false-success checks."

WHAT IS REPRODUCED, and it is the live failure rather than an invented one.
`live-success-243174/` holds a run in which the real provider completed, the
adapter published an attributed proposal, the runtime was destroyed and its
cleanup committed -- and the composed stage then held its ending because the
provider context could not be sealed, so the stage projected `answering` and
could never leave it.

THE CAUSE IS DIRECTORY MODES, established in the claim-243174 FINDING entry.
`context_delivery._private` refuses any custody directory carrying group or
other bits, and the real CLI created seven of them at `0o755` under the
ordinary process umask. The fixture's fake provider has always chmodded its
two state parents to `0o700`, which is exactly why no deterministic test ever
saw this. `ACustodyModeTheRealProviderProduces` stops compensating: it leaves
the state directory as a real CLI leaves it, and the real
`finalize_context_use` refuses for the real reason.

WHAT IS ASSERTED BESIDES THE STOP. Context integrity -- the use is HELD and
never becomes `ready` -- and no false success: the run is `held`, and the
proposal it really did produce is reported rather than being turned into a
settled outcome by a supervisor that gave up waiting.
"""
import json
import os
from pathlib import Path
import unittest

from baton_v12.worker_manager import provider_context as context
from tests.job_manager import fixtures

import baseline
from test_baseline import BaselineCase, IMPLEMENTATION_EDITS

HERE = Path(__file__).resolve().parent
MODES = HERE / "live-success-243174" / "context-home" / "modes.json"


class MainEntrypointCase(BaselineCase):
    """Shared: make the packet's OWN bound source the one this process
    imports, for the run of one test.

    `verify_imported_sources` refuses before anything opens unless the bound
    packages resolve inside the bound tree. Each case builds its own temporary
    tree under its own packet root, so a `boundpkg` left in `sys.modules` by
    an earlier case resolves to ANOTHER case's directory and the check refuses
    -- correctly, and for a reason that has nothing to do with what these
    cases are about.
    """

    def bind_source(self, sys):
        path = self.packet["manager_source"]["path"]
        sys.path.insert(0, path)
        self.addCleanup(sys.path.remove, path)
        for name in list(self.packet["manager_source"]["packages"]):
            sys.modules.pop(name, None)
            self.addCleanup(sys.modules.pop, name, None)


class ACustodyModeTheRealProviderProduces(BaselineCase):
    """The fixture stops compensating for the umask."""

    def umasked_context(self):
        """Leave the context home as a real CLI leaves it.

        AFTER THE TURN, WHICH IS THE LIVE ORDERING. The real provider created
        these directories with the process umask WHILE it ran, and the adapter
        published its receipt over them without complaint -- the live run's
        terminal is `completed`. What refused was the MANAGER, later, sealing
        the generation. Doing this between the turn and the sweep reproduces
        that ordering; doing it inside the provider call would break the
        adapter instead, which is a different failure.
        """
        for use in (Path(self.context_root)).glob(
                "context-*/uses/context-use-*/home"):
            state = use / ".claude" / "projects" / "-output"
            if state.is_dir():
                (state / "memory").mkdir(mode=0o755, exist_ok=True)
                state.chmod(0o755)

    def supervised_stall(self, **overrides):
        packet = dict(self.packet, **overrides) if overrides else self.packet
        job, control, composed = self.serving(packet=packet)
        ticks = iter(range(0, 100000))

        def wait(seconds):
            del seconds
            if self.states(job, composed).get("implementation") != "waiting":
                return None
            attempt = self.pending(composed, "implementation")
            if attempt is None:
                return None
            self.turned.add(attempt)
            status = self.turn(
                control, "implementation", attempt,
                self.mounted(composed, "implementation", attempt),
                edits=dict(IMPLEMENTATION_EDITS))
            self.umasked_context()
            return status

        outcome = baseline.supervise(
            job, control, composed, packet, clock=lambda: fixtures.NOW,
            sleep=wait, monotonic=lambda: float(next(ticks)))
        return outcome, job, control

    # -- the live shape, reproduced ------------------------------------------

    def test_the_stage_cannot_advance_and_the_run_says_so(self):
        outcome, _job, _control = self.supervised_stall()
        self.assertEqual(outcome["stopped"], "no-progress")
        self.assertEqual(outcome["stage_states"],
                         {"implementation": "answering"})
        self.assertEqual(outcome["stalled_ticks"], baseline.STALLED_TICKS)

    def test_it_stops_long_before_the_overall_bound(self):
        """The whole point. The live run spent 443 seconds of 900 before an
        operator interrupted it."""
        outcome, _job, _control = self.supervised_stall()
        self.assertNotEqual(outcome["stopped"], "overall-bound-exceeded")
        self.assertLess(outcome["served_seconds"],
                        self.packet["bounds"]["total_seconds"] / 10)

    def test_context_integrity_is_preserved(self):
        """The use is HELD and never becomes ready. Stopping sooner must not
        become a reason to accept a generation nobody could seal."""
        outcome, _job, control = self.supervised_stall()
        attempt = outcome["admitted_attempts"][0]
        self.assertNotEqual(
            context.context_use_of(control, attempt)["status"], "ready")

    def test_nothing_reads_as_success(self):
        outcome, _job, _control = self.supervised_stall()
        self.assertEqual(outcome["state"], "held")
        self.assertTrue(any("nothing changed for" in one
                            for one in outcome["held_because"]),
                        outcome["held_because"])

    def test_the_proposal_it_really_produced_is_still_reported(self):
        """A supervisor that gave up waiting must not also lose what the run
        achieved. This turn DID publish an attributed proposal."""
        outcome, _job, _control = self.supervised_stall()
        self.assertEqual(
            [one["disposition"]
             for one in outcome["workload"]["dispositions"]], ["completed"])
        said = outcome["workload"]["attribution"][0]
        self.assertEqual(said["author"],
                         f"{baseline.COMMIT_NAME} <{baseline.COMMIT_EMAIL}>")
        self.assertEqual(said["parents"], [self.base])
        self.assertEqual(outcome["outstanding_cleanup"], [])

    def test_the_live_run_had_exactly_this_shape(self):
        """The evidence this reproduction is of, pinned."""
        outcome = json.loads(
            (HERE / "live-success-243174" / "outcome.json").read_text(
                encoding="utf-8"))
        self.assertEqual(outcome["stage_states"],
                         {"implementation": "answering"})
        self.assertEqual(outcome["outstanding_cleanup"], [])
        self.assertEqual(outcome["stopped"], "interrupted")
        self.assertGreater(outcome["served_seconds"], 400)
        # AND THE MODES THAT CAUSED IT.
        modes = json.loads(MODES.read_text(encoding="utf-8"))["entries"]
        offending = sorted(one for one, held in modes.items()
                           if held["kind"] == "dir" and not held["private"])
        self.assertEqual(len(offending), 7, offending)
        self.assertIn(".claude/projects/-output", offending)
        self.assertIn(".claude/projects/-output/memory", offending)


class AProgressingRunIsNeverStoppedEarly(BaselineCase):
    """The rule must not fire on a run that is working."""

    def test_the_ordinary_successful_run_still_settles(self):
        _composed, outcome, _job, _control = self.supervised()
        self.assertEqual(outcome["state"], "settled", outcome["held_because"])
        self.assertEqual(outcome["stopped"], "completed")
        self.assertEqual(outcome["stalled_ticks"], 0)

    def test_an_unreadable_progress_read_never_invents_a_stall(self):
        """Failing towards keeping the run alive. An unreadable journal is not
        evidence that nothing is happening."""
        from unittest import mock

        real, failures = baseline._cleanups, []

        def unreadable(*arguments, **operands):
            # THE FIRST PROGRESS READS FAIL AND THE ACCOUNTING READS DO
            # NOT. Only the predicate's early reads are made to fail;
            # breaking the cleanup accounting as well would be testing a
            # different thing, and the shutdown's own read is unguarded by
            # design because a run that cannot read its journal must not
            # report a clean ending.
            if len(failures) < 2:
                failures.append(1)
                raise RuntimeError("journal unreadable")
            return real(*arguments, **operands)

        with mock.patch.object(baseline, "_cleanups", unreadable):
            _composed, outcome, _job, _control = self.supervised()
        self.assertTrue(failures, "the progress read was never exercised")
        self.assertNotEqual(outcome["stopped"], "no-progress")
        self.assertEqual(outcome["stalled_ticks"], 0)

    def test_a_run_with_outstanding_cleanup_is_not_called_stalled(self):
        """An ending still owing a destroy is a run with something left to do,
        however still its stage states look."""
        held = {"cleanup": {"a": {"cleanup": None}}, "outstanding": ["a"]}
        from unittest import mock

        with mock.patch.object(baseline, "_cleanups", return_value=held):
            _composed, outcome, _job, _control = self.supervised()
        self.assertNotEqual(outcome["stopped"], "no-progress")

    def test_the_observation_changes_when_the_cleanup_axis_moves(self):
        """What `unchanged` means, at the boundary itself."""
        first = baseline._observation(
            {"implementation": "answering"}, ["a"],
            {"a": {"cleanup": None}})
        same = baseline._observation(
            {"implementation": "answering"}, ["a"],
            {"a": {"cleanup": None}})
        moved = baseline._observation(
            {"implementation": "answering"}, ["a"],
            {"a": {"cleanup": "retained"}})
        admitted = baseline._observation(
            {"implementation": "answering"}, ["a", "b"],
            {"a": {"cleanup": None}})
        self.assertEqual(first, same)
        self.assertNotEqual(first, moved)
        self.assertNotEqual(first, admitted)


class AnInterruptedRunSaysWhereItsOutcomeIs(MainEntrypointCase):
    """Owner pass 243171: the outcome WAS retained; `main` never said so."""

    def test_main_retains_the_outcome_and_names_its_path(self):
        import io
        from unittest import mock

        composed_holder = []

        def composing(packet, job, control, stream):
            del packet, stream
            from tools import stage_execution
            composed = stage_execution.operations_from(
                self.composed_document(line_declared_base=self.base),
                job, control, engine_run=self.engine,
                credential_provider=lambda provider, reference: self.secret,
                clock=lambda: fixtures.NOW, checkout=self.checkout)
            self.addCleanup(composed.close)
            composed_holder.append(composed)
            return composed

        self.engine = self.quiescing()
        stream = io.StringIO()
        # THE PACKET BINDS ITS OWN SOURCE TREE, so `verify_imported_sources`
        # has to be able to import it -- that check runs before anything else
        # in `main` and refusing there would never reach the interruption.
        import sys
        self.bind_source(sys)

        def interrupting(seconds):
            del seconds
            raise KeyboardInterrupt("signal 2")

        with mock.patch.object(baseline.time, "sleep", interrupting):
            status = baseline.main(
                ["--packet", self.packet_path,
                 "--incarnation", "interrupted-main"],
                stream=stream, compose=composing,
                image_inspect=mock.Mock(return_value={
                    "Id": self.packet["worker_image"]["config_digest"]}))
        said = stream.getvalue()
        # THE INTERRUPT IS HONOURED, and it is not a success.
        self.assertEqual(status, 130)
        # AND THE OPERATOR IS TOLD WHERE THE OUTCOME IS, by path.
        self.assertIn("interrupted:", said)
        self.assertIn("the outcome WAS retained at", said)
        self.assertIn(self.packet["outcome_path"], said)
        # AND IT REALLY IS THERE, read from the file rather than inferred.
        retained = json.loads(
            Path(self.packet["outcome_path"]).read_text(encoding="utf-8"))
        self.assertEqual(retained["stopped"], "interrupted")
        self.assertIn("KeyboardInterrupt", retained["interrupted"])
        del composed_holder

    def test_a_settled_run_exits_zero_and_a_held_one_does_not(self):
        """The exit statuses an operator scripts against, unchanged by the
        interruption path being added beside them."""
        _composed, outcome, _job, _control = self.supervised()
        self.assertEqual(outcome["state"], "settled", outcome["held_because"])


class AnInterruptionAtTheProgressReadStopsServing(MainEntrypointCase):
    """Review 2026-09-23T00:50:59Z R1, at the exact boundary it names.

    The first version of the progress read used `_guarded` with disposable
    `uncertainty` and `interrupted` lists. `_guarded` catches `BaseException`,
    so a `KeyboardInterrupt` arriving inside that read was swallowed, the
    predicate returned True, and ORDINARY SERVING RESUMED -- the reviewer's
    probe injected SIGINT before any provider turn and then watched a whole
    turn execute, and a direct `KeyboardInterrupt` vanished into a `settled`
    outcome.

    Both shapes are covered here: the signal the installed handler turns into
    a `KeyboardInterrupt`, and a direct one. Each asserts the three things
    that were wrong -- no further provider turn, a retained interrupted
    outcome, and a non-zero status out of `main`.
    """

    def interrupting_read(self, raiser):
        """Make the FIRST progress read raise, and count provider turns.

        The read is `baseline._cleanups` called from the predicate. The
        shutdown calls it too, so only the first call is made to raise; every
        later one is the real function, which is what lets the run still
        account for itself.
        """
        real, calls = baseline._cleanups, []

        def reading(*arguments, **operands):
            calls.append(1)
            if len(calls) == 1:
                raiser()
            return real(*arguments, **operands)
        return reading

    def supervised_interrupted(self, raiser):
        from unittest import mock

        job, control, composed = self.serving()
        ticks = iter(range(0, 100000))
        turns = []

        def wait(seconds):
            del seconds
            if self.states(job, composed).get("implementation") != "waiting":
                return None
            attempt = self.pending(composed, "implementation")
            if attempt is None:
                return None
            self.turned.add(attempt)
            turns.append(attempt)
            return self.turn(control, "implementation", attempt,
                             self.mounted(composed, "implementation", attempt),
                             edits=dict(IMPLEMENTATION_EDITS))

        raised = None
        with mock.patch.object(baseline, "_cleanups",
                               self.interrupting_read(raiser)):
            try:
                outcome = baseline.supervise(
                    job, control, composed, self.packet,
                    clock=lambda: fixtures.NOW, sleep=wait,
                    monotonic=lambda: float(next(ticks)))
            except baseline.SupervisorInterrupted as stopped:
                raised, outcome = stopped, stopped.outcome
        return outcome, raised, turns

    def test_a_signal_at_the_progress_read_ends_the_run(self):
        outcome, raised, turns = self.supervised_interrupted(
            lambda: (_ for _ in ()).throw(KeyboardInterrupt("signal 2")))
        self.assertIsNotNone(raised, "the interruption was swallowed")
        # NO FURTHER ORDINARY SERVING. The probe's finding was a whole
        # provider turn running after the operator asked the run to stop.
        self.assertEqual(turns, [], "a provider turn ran after the interrupt")
        self.assertEqual(outcome["stopped"], "interrupted")
        self.assertIn("KeyboardInterrupt", outcome["interrupted"])
        self.assertEqual(outcome["state"], "held")
        self.assertNotEqual(outcome["stopped"], "completed")

    def test_a_direct_interruption_is_not_discarded_into_success(self):
        """The sharper half: it used to leave no trace at all."""
        outcome, raised, turns = self.supervised_interrupted(
            lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
        self.assertIsNotNone(raised)
        self.assertEqual(turns, [])
        self.assertNotEqual(outcome["state"], "settled")
        self.assertIsNotNone(outcome["interrupted"])

    def test_an_ordinary_read_failure_still_only_resets_the_counter(self):
        """The other direction, unchanged: an unreadable journal is not an
        interruption and must not end the run."""
        outcome, raised, turns = self.supervised_interrupted(
            lambda: (_ for _ in ()).throw(RuntimeError("journal unreadable")))
        self.assertIsNone(raised)
        self.assertEqual(len(turns), 1, "the run should have kept serving")
        self.assertEqual(outcome["stopped"], "completed")
        self.assertEqual(outcome["stalled_ticks"], 0)
        # AND THE DIAGNOSTIC IS KEPT rather than discarded, which is the other
        # half of R1: the first version threw the record away.
        self.assertTrue(any("the progress read did not complete" in one
                            for one in outcome["uncertainty"]),
                        outcome["uncertainty"])

    def test_main_exits_nonzero_when_the_progress_read_is_interrupted(self):
        import io
        import sys
        from unittest import mock
        from tools import stage_execution

        self.engine = self.quiescing()
        self.bind_source(sys)
        stream, turns = io.StringIO(), []

        def composing(packet, job, control, out):
            del packet, out
            composed = stage_execution.operations_from(
                self.composed_document(line_declared_base=self.base),
                job, control, engine_run=self.engine,
                credential_provider=lambda provider, reference: self.secret,
                clock=lambda: fixtures.NOW, checkout=self.checkout)
            self.addCleanup(composed.close)
            return composed

        def waiting(seconds):
            del seconds
            turns.append(1)
            return None

        with mock.patch.object(baseline.time, "sleep", waiting), \
                mock.patch.object(
                    baseline, "_cleanups",
                    self.interrupting_read(
                        lambda: (_ for _ in ()).throw(
                            KeyboardInterrupt("signal 2")))):
            status = baseline.main(
                ["--packet", self.packet_path,
                 "--incarnation", "progress-interrupted"],
                stream=stream, compose=composing,
                image_inspect=mock.Mock(return_value={
                    "Id": self.packet["worker_image"]["config_digest"]}))
        self.assertEqual(status, 130)
        said = stream.getvalue()
        self.assertIn("the outcome WAS retained at", said)
        retained = json.loads(
            Path(self.packet["outcome_path"]).read_text(encoding="utf-8"))
        self.assertEqual(retained["stopped"], "interrupted")


class TheRealLayoutIsCompliantBecauseOfTheMaskNotARepair(BaselineCase):
    """Owner 2026-09-23T03:06:11Z, the positive half of the custody decision.

    "Reproduce the real directory layout deterministically without
    fixture-only permission repairs, preserving negative custody coverage."

    THE FIXTURE NO LONGER REPAIRS ANYTHING. Its child used to chmod its two
    state parents to `0o700` -- which is exactly why no deterministic test ever
    saw the live failure -- and it now creates `memory`, `backups`,
    `shell-snapshots`, `sessions` and `session-env` the way a real CLI does and
    chmods none of them. What makes them private is
    `claude_agent.PROVIDER_UMASK` on the provider child.

    So this case is a proof about the CORRECTION rather than about the fixture:
    if the mask were removed, every assertion below would fail on a layout the
    fixture itself never touches.
    """

    def ran(self):
        _composed, outcome, _job, control = self.supervised()
        self.assertEqual(outcome["state"], "settled", outcome["held_because"])
        homes = sorted(Path(self.context_root).glob(
            "context-*/uses/context-use-*/home"))
        self.assertEqual(len(homes), 1, homes)
        return outcome, control, homes[0]

    def test_every_directory_the_provider_created_is_private(self):
        import stat

        _outcome, _control, home = self.ran()
        seen = []
        for base, dirs, _names in os.walk(home):
            for name in sorted(dirs):
                place = os.path.join(base, name)
                mode = stat.S_IMODE(os.lstat(place).st_mode)
                seen.append(os.path.relpath(place, home))
                with self.subTest(entry=seen[-1]):
                    self.assertEqual(mode & 0o077, 0, oct(mode))
        # THE OBSERVED LAYOUT, not a convenient subset: the directories the
        # live run left behind are the ones created here.
        for name in (".claude/projects/-output", ".claude/projects/-output/memory",
                     ".claude/backups", ".claude/shell-snapshots",
                     ".claude/sessions", ".claude/session-env"):
            with self.subTest(entry=name):
                self.assertIn(name, seen)

    def test_the_managers_own_measurement_accepts_that_home(self):
        """`_state` is the function that refused the live run. It is
        unchanged, and it now has nothing to refuse."""
        from baton_v12.worker_manager import context_delivery as delivery
        from baton_v12.worker_manager import provider_context as ctx

        outcome, control, home = self.ran()
        attempt = outcome["admitted_attempts"][0]
        binding = ctx.context_invocation_of(control, attempt)
        profile = dict(
            ctx.context_profile_of(
                control,
                ctx._use(control, attempt)[1]["payload"]["profile_digest"]))
        profile["state_paths"] = [
            one.replace("{conversation_id}", binding["conversation_id"])
            for one in profile["state_paths"]]
        fd = os.open(str(home), os.O_RDONLY | os.O_DIRECTORY)
        try:
            entries = delivery._state(fd, profile)
        finally:
            os.close(fd)
        self.assertTrue(entries)

    def test_the_context_generation_really_sealed(self):
        """The end of the chain the live run could not reach."""
        from baton_v12.worker_manager import provider_context as ctx

        outcome, control, _home = self.ran()
        attempt = outcome["admitted_attempts"][0]
        self.assertEqual(ctx.context_use_of(control, attempt)["status"],
                         "ready")

    def test_a_home_the_provider_made_readable_is_still_refused(self):
        """THE NEGATIVE COVERAGE, PRESERVED. A mask cannot stop an explicit
        `chmod`, and the manager's check is what catches that -- which is why
        the check is not weakened. `ACustodyModeTheRealProviderProduces` drives
        the same shape through a whole run; this is the measurement itself."""
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import context_delivery as delivery
        from baton_v12.worker_manager import provider_context as ctx

        outcome, control, home = self.ran()
        attempt = outcome["admitted_attempts"][0]
        binding = ctx.context_invocation_of(control, attempt)
        profile = dict(
            ctx.context_profile_of(
                control,
                ctx._use(control, attempt)[1]["payload"]["profile_digest"]))
        profile["state_paths"] = [
            one.replace("{conversation_id}", binding["conversation_id"])
            for one in profile["state_paths"]]
        (home / ".claude" / "projects" / "-output").chmod(0o755)
        fd = os.open(str(home), os.O_RDONLY | os.O_DIRECTORY)
        try:
            with self.assertRaises(ContractRefusal) as caught:
                delivery._state(fd, profile)
        finally:
            os.close(fd)
        self.assertIn("protected custody owner or mode changed",
                      str(caught.exception))


def load_tests(loader, tests, pattern):
    del tests, pattern, loader
    suite = unittest.TestSuite()
    for case in (ACustodyModeTheRealProviderProduces,
                 TheRealLayoutIsCompliantBecauseOfTheMaskNotARepair,
                 AProgressingRunIsNeverStoppedEarly,
                 AnInterruptionAtTheProgressReadStopsServing,
                 AnInterruptedRunSaysWhereItsOutcomeIs):
        for name in sorted(one for one in vars(case)
                           if one.startswith("test")):
            suite.addTest(case(name))
    return suite


