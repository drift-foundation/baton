"""ONE reviewer, actually admitted and ended, over real coordination.

Owner reroute 247663 item 1, and review 2026-09-23T11:56:42Z R3b before it:
"The new `Serving` fixture deliberately defers every admission and starts no
runtime ... no-progress with an accountable attempt, actual cancellation,
cleanup uncertainty/interruption with an outstanding attempt, completed review
and real frozen-result collection remain unexercised."

WHAT IS REAL HERE. A real `JobStore` and `ControlStore`; the real composition
through `stage_execution.operations_from`; the real `AdmissionGate`; a real
line, writer and FROZEN CHECKPOINT produced by W239528's accepted baseline run;
a real review attachment; a real frozen review output; and
`review_supervisor.supervise` driving all of it to an outcome.

WHAT IS SIMULATED, labelled rather than implied: the PROVIDER. The turn is the
fixture's deterministic worker turn -- the same one W239528's accepted suite
and the product's own `ManagedSessionResume` use -- not a container and not a
live model. Every receipt it produces is minted by the real manager from that
turn; none is fabricated here.

THE TWO PHASES SHARE ONE CONTROL STORE, which is the whole arrangement
`attachment.py` describes: phase one is W239528's implementation run, leaving a
`review-ready` line with a frozen checkpoint, and phase two is this Job's
review over those same records with its own Job identity, submission, stage,
attempt and outcome.
"""

import json
import os
import sys
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SIBLING = os.path.join(os.path.dirname(HERE),
                       "finding-v12-single-implementation-proof")
for one in (HERE, SIBLING):
    if one not in sys.path:                                  # pragma: no cover
        sys.path.insert(0, one)

from baton_v12.contracts import job_input_identity
from tests.job_manager import fixtures
from tools import stage_execution

import baseline
import review_supervisor
from test_baseline import BaselineCase

REVIEW_JOB = "job-independent-review-239533"
# The file name `claude_agent` reads the report back from, mirrored rather than
# imported: `claude_agent` runs inside the image on its own import path.
REVIEW_REPORT = "review-report.json"
# `findings` IS NON-EMPTY TEXT, NOT A LIST. Both fixture reports carried a list
# and the turn answered `unable` for exactly that reason -- review
# 2026-09-23T12:57:02Z found it: `claude_agent._review_report` requires
# `type(findings) is str` and non-blank, and a malformed report is deliberately
# NOT a verdict ("an exit status is not a decision and this adapter will not
# map one into a verdict"). The adapter was right and the fixture was wrong.
ACCEPTED = {"schema": "baton.review-report/1", "verdict": "accepted",
            "findings": "Ran python3 harness.py: it prints READY and exits 0. "
                        "Only harness.py changed."}
CHANGES_REQUESTED = {
    "schema": "baton.review-report/1", "verdict": "changes-requested",
    "findings": "Ran python3 harness.py: it prints READY and exits 0, but the "
                "change also leaves a trailing blank line the requirement "
                "does not ask for."}


class ReviewLifecycleCase(BaselineCase):
    """W239528's fixture, carried one phase further.

    `BaselineCase` is subclassed for its FIXTURE -- the disposable Authority,
    the stores, the deterministic turn, the composition and the engine -- and
    `load_tests` below keeps its cases from running under this dossier's name.
    """

    def produced(self):
        """PHASE ONE: the accepted implementation run, to its frozen
        checkpoint.

        Driven through W239528's own `baseline.supervise` rather than
        reproduced here, so what phase two reviews is a checkpoint that Job's
        accepted program actually made.
        """
        composed, outcome, job, control = self.supervised()
        self.assertEqual(outcome["state"], "settled", outcome["held_because"])
        self.producer_outcome = outcome
        composed.close()
        self._job, self._control = job, control
        return job, control

    def review_submission(self, place, *, stalling=False):
        """The review Job, optionally with a stage that cannot advance.

        `stalling` adds an `integration` stage to THIS Job that depends on a
        stage in a SECOND Job which never runs. It is the state the no-progress
        detector exists for and the only one that satisfies all four of its
        conditions at once: the review attempt is accountable, its cleanup is
        positively COMMITTED, the Job is still not terminal because that second
        stage is blocked, and the observation therefore stops changing.

        The blocked stage never reaches admission, so the gate refuses nothing
        -- a cap refusal would end the run for a different reason and prove
        nothing about the detector.
        """
        if stalling:
            return self.stalling_submission(place)
        held = {
            "schema": "baton.v12.job-submission/2",
            "submission_id": "independent-review-submission",
            "jobs": [dict(
                fixtures.job(
                    # THE WORKER'S OWN MANIFEST, not the fixture constant.
                    # The reproduction that found this is worth keeping: the
                    # review stage stayed `queued` for a whole run and the
                    # deferral said why -- "no worker this deployment
                    # configures for the 'review' stage can serve Job ...:
                    # {'review-worker': ['the submitted input']}". Assembly
                    # supplies coherent operands rather than reserving a
                    # worker that must then refuse them.
                    REVIEW_JOB,
                    input_digest=job_input_identity(self.manifest),
                    policy_digest=fixtures.POLICY_DIGEST,
                    stages=[fixtures.stage("review", self.work)]),
                execution_limits={"provider_turn_seconds": 180})]}
        Path(place).write_text(json.dumps(held, sort_keys=True),
                               encoding="utf-8")
        return held

    def stalling_submission(self, place):
        blocker = "job-never-runs"
        held = {
            "schema": "baton.v12.job-submission/2",
            "submission_id": "independent-review-submission",
            "jobs": [
                dict(fixtures.job(
                    blocker, input_digest=job_input_identity(self.manifest),
                    policy_digest=fixtures.POLICY_DIGEST,
                    stages=[fixtures.stage("implementation", self.work)]),
                    execution_limits={"provider_turn_seconds": 180}),
                dict(fixtures.job(
                    REVIEW_JOB,
                    input_digest=job_input_identity(self.manifest),
                    policy_digest=fixtures.POLICY_DIGEST,
                    stages=[
                        fixtures.stage("review", self.work),
                        fixtures.stage(
                            "integration", self.work,
                            depends_on=[{"job_id": blocker,
                                         "kind": "implementation"}])]),
                    execution_limits={"provider_turn_seconds": 180})]}
        Path(place).write_text(json.dumps(held, sort_keys=True),
                               encoding="utf-8")
        return held

    def review_deployment(self, place):
        """The SAME composed deployment, declining the correction round.

        Not a second configuration: phase two must reach the same line, and
        `create_line` derives that from the Authority and Work the deployment
        names. What differs is `correction_policy`, which is the boundary
        owner selection 247421 added.
        """
        document = dict(self.composed_document(line_declared_base=self.base),
                        correction_policy=stage_execution.DECLINE_CORRECTION)
        Path(place).write_text(json.dumps(document, sort_keys=True, indent=2),
                               encoding="utf-8")
        return document

    def review_packet(self, root, **overrides):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        submission = root / "submission.json"
        deployment = root / "deployment.json"
        self.review_submission(str(submission),
                               stalling=overrides.pop("stalling", False))
        self.review_deployment(str(deployment))
        held = {
            "schema": review_supervisor.PACKET_SCHEMA,
            "run_id": "independent-review-239533-deterministic",
            "work": "W239533", "claim": 247757,
            "note": "one deterministic managed review",
            "subject": self.subject(),
            "producer_run_root": str(root),
            "producer_control_store": str(Path(self.root) / "control.sqlite3"),
            "worker_image": {"reference": "r", "config_digest": "d",
                             "worker_files": {}},
            "manager_runtime": {"path": str(root), "executable_sha256": "e",
                                "build_commit": "f" * 40},
            "manager_source": {"path": str(root), "packages": [],
                               "file_count": 0, "files": {}},
            "supervisor": {"path": str(Path(HERE) / "review_supervisor.py"),
                           "sha256": baseline._digest_of_file(
                               str(Path(HERE) / "review_supervisor.py"))},
            "code_boundary": str(root),
            "deployment": {
                "config_path": str(deployment),
                "config_sha256": baseline._digest_of_file(str(deployment)),
                "job_store": str(Path(self.root) / "jobs.sqlite3"),
                "control_store": str(Path(self.root) / "control.sqlite3"),
                "authority_store": str(self.authority_path),
                "authority_uuid": self.config["authority_uuid"],
                "state_root": str(self.root)},
            "context": {"storage_path": str(self.context_root),
                        "excluded_roots": [], "runtime_uid": os.getuid(),
                        "profile_path": None, "profile_sha256": None,
                        "profile_digest": None, "job_id": REVIEW_JOB},
            "submission": {"path": str(submission),
                           "sha256": baseline._digest_of_file(str(submission)),
                           "job_id": REVIEW_JOB},
            "criteria": {"path": str(submission), "sha256": "unused",
                         "content_digest": "unused"},
            "bounds": {"turn_seconds": 180, "total_seconds": 60,
                       "cleanup_seconds": 20, "review_invocations": 1,
                       "retry": False},
            "outcome_path": str(root / "review-outcome.json")}
        held.update(overrides)
        return held

    def subject(self):
        """The frozen checkpoint phase one really left, read back."""
        from baton_v12.worker_manager import checkpoint_of, line_of, writer_of

        attribution = self.producer_outcome["workload"]["attribution"][0]
        line = line_of(self._control, attribution["line_id"])
        checkpoint = checkpoint_of(self._control,
                                   line["current_checkpoint_id"])
        writer = writer_of(self._control, checkpoint["writer_id"])
        return {
            "schema": "baton.independent-review-subject/2",
            "line_id": line["line_id"],
            "checkpoint_id": checkpoint["checkpoint_id"],
            "authority_uuid": line["authority_uuid"],
            "work_id": line["work_id"],
            "declared_base": line["declared_base"],
            "base_object": checkpoint["base_object"],
            "head_object": checkpoint["head_object"],
            "tree_object": checkpoint["tree_object"],
            "checkpoint_digest": checkpoint["checkpoint_digest"],
            "producer": {"writer_id": writer["writer_id"],
                         "worker_id": writer["worker_id"],
                         "participant": writer["participant"],
                         "principal": writer["principal"]}}

    def states(self, job, composed):
        """THIS Job's stages, selected by identity rather than by position.

        The inherited helper reads `projected["jobs"][0]`, which is the FIRST
        projected Job -- correct for a one-Job fixture and wrong the moment a
        second Job exists. Under the stalling submission it answered the
        blocker Job's stages, so the driver never saw `review` reach
        `waiting`, never took the turn, and the attempt ended `exceptional`.
        Review 2026-09-23T13:41:04Z found it with an instance-only public
        status selector; this is the same selection, in the fixture that
        needed it.
        """
        from baton_v12.job_manager import status as projected_status

        projected = projected_status(job, composed, observed_at=fixtures.NOW)
        for one in projected["jobs"]:
            if one["job_id"] == REVIEW_JOB:
                return {stage["kind"]: stage["state"]
                        for stage in one["stages"]}
        # PHASE ONE HAS NO REVIEW JOB, and it is the inherited fixture's own
        # one-Job run -- so the first projected Job is the right answer there.
        # An override that answered nothing for it stopped the producer's turn
        # being taken at all, which is the same positional assumption failing
        # from the other side.
        return {stage["kind"]: stage["state"]
                for stage in projected["jobs"][0]["stages"]} \
            if projected["jobs"] else {}

    def recording_gate(self):
        """The real imported gate, with every act stamped with its own state.

        Review 2026-09-23T13:04:00Z: "Gate-order test checks only final
        counts; that cannot establish gate closed before cancellation in a
        single-stage Job." It cannot -- a count is the end of the run, and the
        question is about an instant during it. This subclasses
        `baseline.AdmissionGate` and records `(act, self.stopped)` at the call,
        so the order is read off the trace rather than inferred.

        IT PATCHES `review_supervisor.AdmissionGate`, NOT `baseline`'s. The
        name this module under test resolves is the seam; W239528's module is
        untouched and `test_review_supervisor` still parses this program to
        hold it to that.
        """
        trace = []

        class Recording(baseline.AdmissionGate):
            def __init__(self, operations, **operands):
                super().__init__(operations, **operands)
                # THE INSTANCE ITSELF, so a case can ask its state at the
                # moment the COMPOSITION is called. `_cancel_active` is handed
                # the composition rather than the gate, so the cancellation's
                # order cannot be read off the gate's own calls -- it has to be
                # read by asking the gate while the composition acts.
                trace.append(("gate", self))

            def admit(self, stage, job):
                trace.append(("admit", self.stopped))
                return super().admit(stage, job)

            def claim(self, stage):
                trace.append(("claim", self.stopped))
                return super().claim(stage)

            def launch(self, attempt, job):
                trace.append(("launch", self.stopped))
                return super().launch(attempt, job)

        return Recording, trace

    def watched_cancellation(self, composed, trace, *, interrupt=False):
        """Stamp the GATE's state onto the composition's cancellation.

        `interrupt` raises there instead of cancelling, which is the shutdown
        point review 2026-09-23T13:10:01Z asked to have OBSERVED rather than
        inferred: the gate is already closed, the attempt is already
        outstanding, and the interrupt lands inside the shutdown accounting.
        """
        held = composed.cancel_attempt

        def cancelling(**operands):
            gate = next((one for name, one in trace if name == "gate"), None)
            stopped = None if gate is None else gate.stopped
            trace.append(("cancel_attempt", stopped))
            self.shutdown_reached = stopped
            if interrupt:
                raise KeyboardInterrupt("operator stopped during shutdown")
            return held(**operands)

        composed.cancel_attempt = cancelling
        return composed

    def reviewing(self, *, packet, **operands):
        """PHASE TWO: the review Job, over the same stores."""
        job, control = self._job, self._control
        composed = stage_execution.operations_from(
            json.loads(Path(packet["deployment"]["config_path"]).read_text(
                encoding="utf-8")),
            job, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        # THE FIXTURE'S `turn` REACHES `composed_for`, WHICH ANSWERS
        # `self._composed` -- phase one's object unless this says otherwise,
        # and phase two's composition is the one holding the prepared review
        # attempt. Leaving it answered a KeyError for the attempt that had
        # just been admitted.
        self._composed = composed
        # ONE SECOND PER READ, so a bound is exercised by arithmetic rather
        # than waited for, and `served_seconds` is a tick count the case can
        # assert against the packet's own numbers. EVERY READ IS RECORDED, so
        # a case can say WHEN on this clock the serving stop, the cancellation
        # and each cleanup action happened -- `served_seconds` alone is
        # measured before cancellation and cleanup and cannot speak for them.
        self.clock_reads = []
        counter = iter(range(0, 100000))

        def monotonic():
            held = float(next(counter))
            self.clock_reads.append(held)
            return held

        ticks = None
        gate, self.gate_trace = self.recording_gate()
        self.shutdown_reached = None
        self.watched_cancellation(
            composed, self.gate_trace,
            interrupt=operands.pop("interrupt_in_shutdown", False))
        from unittest import mock

        with mock.patch.object(review_supervisor, "AdmissionGate", gate):
            return composed, review_supervisor.supervise(
                job, control, composed, packet,
                clock=lambda: fixtures.NOW,
                sleep=self.review_driver(job, control, composed, **operands),
                monotonic=monotonic)

    def review_driver(self, job, control, composed, *, report=None,
                      expect=0, interrupt_at=None, fail_at=None,
                      withhold=False):
        """The injected wait, and the ONE place the turn is taken.

        `withhold` is the seam review 2026-09-23T13:10:01Z asked for: the
        stage is admitted and then the turn is NEVER TAKEN, so the loop runs
        to its deadline instead of completing early. The previous "cannot
        finish" cases passed `report=None`, which falls back to ACCEPTED, and
        `expect=None`, which only disables the status assertion -- so both of
        them completed successfully and proved nothing about a bound. The
        reviewer reproduced that independently and was right.
        """
        seen = {"turns": 0, "ran": False}
        self.driver_seen = seen

        def wait(seconds):
            del seconds
            seen["turns"] += 1
            if interrupt_at is not None and seen["turns"] >= interrupt_at:
                raise KeyboardInterrupt("operator stopped the review")
            if fail_at is not None and seen["turns"] >= fail_at:
                raise RuntimeError("the composition failed mid-review")
            if withhold:
                return None
            if self.states(job, composed).get("review") != "waiting":
                return None
            attempt = self.pending(composed, "review")
            if attempt is None:
                return None
            self.turned.add(attempt)
            # THE REPORT IS WRITTEN BY THE PROVIDER, into its own cwd, which
            # is what `claude_agent._review_report(room)` reads back. The
            # fixture's `edits` seam is exactly that write, so the report
            # travels the way a real reviewer's would rather than being
            # planted in an output the manager reads.
            status = self.turn(control, "review", attempt,
                               self.mounted(composed, "review", attempt),
                               edits={REVIEW_REPORT: json.dumps(
                                   report or ACCEPTED, sort_keys=True)})
            if expect is not None:
                self.assertEqual(status, expect)
            seen["ran"] = True
            return status

        return wait


class OneReviewerIsAdmittedAndEnded(ReviewLifecycleCase):
    """The whole path, settled: admitted, attributed, stopped, cleaned up."""

    def settled(self, **operands):
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        composed, outcome = self.reviewing(packet=packet, **operands)
        return packet, composed, outcome

    def test_it_settles_with_one_attributed_verdict_and_positive_cleanup(self):
        packet, _composed, outcome = self.settled()
        self.assertEqual(outcome["state"], "settled", outcome["held_because"])
        self.assertEqual(outcome["stopped"], "completed")
        self.assertEqual(outcome["stage_states"], {"review": "completed"})
        self.assertEqual(outcome["admissions"], {"review": 1})
        self.assertEqual(len(outcome["admitted_attempts"]), 1)
        self.assertEqual(outcome["held_because"], [])
        self.assertEqual(outcome["outstanding_cleanup"], [])
        self.assertEqual(outcome["uncertainty"], [])
        self.assertIs(outcome["final_canonical_read"], True)

        # THE VERDICT IS THE REVIEWER'S OWN, READ FROM ITS FROZEN OUTPUT, and
        # bound to the checkpoint the packet named.
        verdicts = outcome["workload"]["verdicts"]
        self.assertEqual(len(verdicts), 1)
        held = verdicts[0]
        self.assertEqual(held["verdict"], "accepted")
        self.assertEqual(held["checkpoint_id"],
                         packet["subject"]["checkpoint_id"])
        self.assertEqual(held["base"], packet["subject"]["base_object"])
        self.assertEqual(held["head"], packet["subject"]["head_object"])
        self.assertEqual(held["tree"], packet["subject"]["tree_object"])
        self.assertTrue(held["result_id"])
        self.assertTrue(held["result_digest"].startswith("sha256:"))
        self.assertEqual(outcome["workload"]["shortfalls"], [])

    def test_the_runtime_is_stopped_and_its_cleanup_is_positive(self):
        _packet, _composed, outcome = self.settled()
        for attempt, said in sorted(outcome["cancellation"].items()):
            with self.subTest(attempt=attempt):
                self.assertTrue(said["requested"])
                self.assertEqual(said["execution_runtime"], "destroyed")
        for attempt, said in sorted(outcome["cleanup"].items()):
            with self.subTest(attempt=attempt):
                self.assertIn(said["cleanup"], baseline.POSITIVE_CLEANUP)

    def test_the_reviewer_is_independent_of_the_producer(self):
        """`attach_review` decides this, and the outcome carries both sides."""
        packet, _composed, outcome = self.settled()
        producer = packet["subject"]["producer"]
        attachment = outcome["workload"]["attachments"][0]
        from baton_v12.worker_manager import review_of

        held = review_of(self._control, attachment["attachment_id"])
        for axis, mine, theirs in (
                ("worker", held["reviewer_worker_id"],
                 producer["worker_id"]),
                ("participant", held["reviewer_participant"],
                 producer["participant"]),
                ("principal", held["reviewer_principal"],
                 producer["principal"])):
            with self.subTest(axis=axis):
                self.assertNotEqual(mine, theirs)


class AChangesRequestedReviewIsAValidOutcome(ReviewLifecycleCase):
    """And it opens NO correction round, which is the selected contract.

    This is the case owner reroute 247663 item 2 names in as many words:
    "Prove changes-requested is a valid review outcome with zero correction
    rounds and zero implementation admission."
    """

    def test_it_settles_with_zero_correction_rounds_and_no_implementation(self):
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        _composed, outcome = self.reviewing(packet=packet,
                                            report=CHANGES_REQUESTED)
        self.assertEqual(outcome["state"], "settled", outcome["held_because"])
        self.assertEqual(outcome["stopped"], "completed")
        self.assertEqual(
            [one["verdict"] for one in outcome["workload"]["verdicts"]],
            ["changes-requested"])
        # NO ROUND, AND NO CONTAINER. The first is the product change owner
        # selection 247421 made; the second is the admission gate's only cap.
        self.assertEqual(outcome["correction_rounds_opened"], [])
        self.assertEqual(outcome["correction_containers_started"], [])
        self.assertEqual(outcome["admissions"], {"review": 1})
        self.assertEqual(outcome["workload"]["shortfalls"], [])
        self.assertEqual(outcome["held_because"], [])

    def test_the_declining_deployment_is_what_the_run_actually_used(self):
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        written = json.loads(
            Path(packet["deployment"]["config_path"]).read_text(
                encoding="utf-8"))
        self.assertEqual(written["correction_policy"],
                         stage_execution.DECLINE_CORRECTION)


class AnAdmittedAttemptIsAccountedForWhenTheRunDoesNotFinish(
        ReviewLifecycleCase):
    """Item 3: the paths that only exist once something IS admitted."""

    def held(self, **operands):
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        return packet, self.reviewing(packet=packet, **operands)[1]

    def test_an_interruption_mid_review_still_publishes_and_accounts(self):
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        with self.assertRaises(
                review_supervisor.SupervisorInterrupted) as got:
            self.reviewing(packet=packet, interrupt_at=2)
        outcome = got.exception.outcome
        self.assertIn("KeyboardInterrupt", outcome["interrupted"])
        self.assertEqual(outcome["state"], "held")
        # THE ATTEMPT IT ADMITTED IS STILL ACCOUNTED FOR, which is the whole
        # difference from an interruption that admitted nothing.
        self.assertEqual(len(outcome["admitted_attempts"]), 1)
        self.assertTrue(outcome["cancellation"])
        self.assertTrue(os.path.exists(packet["outcome_path"]))

    def test_a_composition_failure_mid_review_holds_with_the_attempt_named(
            self):
        packet, outcome = self.held(fail_at=2)
        self.assertEqual(outcome["stopped"], "serving-failed")
        self.assertEqual(len(outcome["admitted_attempts"]), 1)
        self.assertTrue(any("did not end cleanly" in one
                            for one in outcome["held_because"]))
        self.assertTrue(os.path.exists(packet["outcome_path"]))

    def test_admission_closes_before_cancellation_and_nothing_is_admitted_after(
            self):
        _packet, outcome = self.held(fail_at=2)
        # The gate closed, so the cleanup window admitted nothing new.
        self.assertEqual(outcome["unexpected_attempts"], [])
        self.assertEqual(outcome["admissions"], {"review": 1})
        self.assertEqual(outcome["foreign_admissions"], [])


class TheGateIsClosedBeforeAnythingIsCancelled(ReviewLifecycleCase):
    """The ORDER, read off a trace taken at each act.

    Review 2026-09-23T13:04:00Z: final counts cannot establish this in a
    single-stage Job, and it is right. The gate stamps its own `stopped` state
    onto every act it performs, so "admission closed first" is a fact about
    the sequence rather than an inference from the totals.
    """

    def test_every_admitting_act_happened_while_the_gate_was_open(self):
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        _composed, outcome = self.reviewing(packet=packet)
        self.assertEqual(outcome["state"], "settled", outcome["held_because"])
        admitting = [one for one in self.gate_trace
                     if one[0] in ("admit", "claim", "launch")]
        self.assertTrue(admitting, self.gate_trace)
        for act, stopped in admitting:
            with self.subTest(act=act):
                self.assertFalse(stopped, self.gate_trace)

    def test_cancellation_is_asked_for_only_after_the_gate_closed(self):
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        _composed, outcome = self.reviewing(packet=packet, fail_at=2)
        cancelled = [one for one in self.gate_trace
                     if one[0] == "cancel_attempt"]
        self.assertTrue(cancelled, self.gate_trace)
        for _act, stopped in cancelled:
            self.assertTrue(stopped, self.gate_trace)
        # AND NOTHING ADMITTING FOLLOWED IT.
        after = self.gate_trace[self.gate_trace.index(cancelled[0]):]
        self.assertFalse([one for one in after
                          if one[0] in ("admit", "claim", "launch")], after)

    def test_a_closed_gate_refuses_an_admission_it_is_offered(self):
        """Not just "none arrived" -- one is offered and refused."""
        from baton_v12.contracts import ContractRefusal

        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        composed, _outcome = self.reviewing(packet=packet)
        gate, _trace = self.recording_gate()
        held = gate(composed, caps={"review": 1},
                    job_id=packet["submission"]["job_id"])
        held.stop()
        with self.assertRaises(ContractRefusal):
            held.admit({"kind": "review", "stage_id": "s",
                        "job_id": packet["submission"]["job_id"]}, None)


class TheTotalBoundHoldsWhenTheRunCannotFinish(ReviewLifecycleCase):
    """A run that is ADMITTED and then never takes its turn.

    Review 2026-09-23T13:10:01Z reproduced the previous pair and found both
    completed successfully -- `report=None` fell back to ACCEPTED and
    `expect=None` only disabled a status assertion -- so neither reached a
    deadline. `withhold=True` is the seam that does: the stage is admitted,
    the turn is never taken, and the loop stops on arithmetic.
    """

    SMALL = {"turn_seconds": 180, "total_seconds": 30, "cleanup_seconds": 10,
             "review_invocations": 1, "retry": False}

    def withheld(self):
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"),
                                    bounds=dict(self.SMALL))
        _composed, outcome = self.reviewing(packet=packet, withhold=True)
        return packet, outcome

    def test_it_stops_at_the_serving_deadline_rather_than_completing(self):
        packet, outcome = self.withheld()
        self.assertEqual(outcome["stopped"], "overall-bound-exceeded")
        self.assertNotEqual(outcome["stage_states"].get("review"), "completed")
        self.assertEqual(outcome["state"], "held")
        # AND IT REALLY WAS ADMITTED. A run that admitted nothing would reach
        # the same stop reason for an entirely different reason.
        self.assertEqual(outcome["admissions"], {"review": 1})
        self.assertEqual(len(outcome["admitted_attempts"]), 1)

    def test_serving_stops_at_total_minus_cleanup(self):
        packet, outcome = self.withheld()
        bounds = packet["bounds"]
        self.assertEqual(outcome["serving_bound_seconds"],
                         bounds["total_seconds"] - bounds["cleanup_seconds"])
        self.assertGreaterEqual(outcome["served_seconds"],
                                outcome["serving_bound_seconds"])
        self.assertLess(outcome["served_seconds"], bounds["total_seconds"])

    def test_no_cleanup_action_starts_after_the_total_deadline(self):
        """The whole run, on the controlled clock -- not `served_seconds`.

        `served_seconds` is measured BEFORE cancellation and cleanup, so it
        cannot speak for them. Every read of the injected clock is recorded,
        so the LAST one is when the run's final act happened; the cleanup
        window's own guard is what keeps it inside the total.
        """
        packet, outcome = self.withheld()
        bounds = packet["bounds"]
        self.assertTrue(self.clock_reads)
        self.assertLessEqual(max(self.clock_reads), bounds["total_seconds"],
                             f"the run read the clock past its own total: "
                             f"{self.clock_reads[-5:]}")

    def test_removing_the_deadline_check_would_change_this_answer(self):
        """The case is sensitive to the thing it claims to test.

        With the same operands and a total bound raised far above the tick
        budget, the run does NOT stop on the deadline -- so the previous case
        is measuring the deadline rather than something that would hold
        anyway.
        """
        self.produced()
        packet = self.review_packet(
            os.path.join(self.root, "review"),
            bounds=dict(self.SMALL, total_seconds=100000,
                        cleanup_seconds=10))
        _composed, outcome = self.reviewing(packet=packet, withhold=True,
                                            fail_at=40)
        self.assertNotEqual(outcome["stopped"], "overall-bound-exceeded")


class AnOutstandingAdmittedAttemptIsNamedExactly(ReviewLifecycleCase):
    """Item 3's uncertainty half: WHICH attempt, not how many."""

    def admitted_attempt(self, outcome):
        self.assertEqual(len(outcome["admitted_attempts"]), 1,
                         outcome["admitted_attempts"])
        return outcome["admitted_attempts"][0]

    def test_a_failure_before_the_ending_leaves_that_attempt_outstanding(self):
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        _composed, outcome = self.reviewing(packet=packet, fail_at=2)
        attempt = self.admitted_attempt(outcome)
        self.assertEqual(outcome["outstanding_cleanup"], [attempt])
        self.assertIn(attempt, outcome["cleanup"])
        self.assertIsNone(outcome["cleanup"][attempt]["cleanup"])
        self.assertTrue(any(attempt in one for one in
                            outcome["held_because"]), outcome["held_because"])

    def test_an_interruption_INSIDE_THE_SHUTDOWN_is_observed_not_inferred(
            self):
        """The injected point is asserted to have been reached.

        Review 2026-09-23T13:10:01Z: an interruption during serving "does not
        substitute for a deliberately observed interruption in shutdown", and
        the failure-before-ending path already supplies the reachable state --
        an exact outstanding attempt, with the gate closed. So the interrupt
        is injected AT the composition's cancellation, and the case asserts
        that it fired there with the gate already `stopped` rather than
        inferring the phase from the outcome.
        """
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        with self.assertRaises(
                review_supervisor.SupervisorInterrupted) as got:
            self.reviewing(packet=packet, fail_at=2,
                           interrupt_in_shutdown=True)
        # THE INJECTED POINT WAS REACHED, and the gate was closed when it was.
        self.assertIs(self.shutdown_reached, True,
                      "the shutdown interrupt never fired")
        outcome = got.exception.outcome
        self.assertIn("KeyboardInterrupt", str(outcome["uncertainty"])
                      + str(outcome["interrupted"]))
        attempt = self.admitted_attempt(outcome)
        self.assertEqual(outcome["outstanding_cleanup"], [attempt])
        # THE OUTCOME AND ITS UNCERTAINTY ARE ON DISK BEFORE THE RAISE.
        self.assertTrue(os.path.exists(packet["outcome_path"]))
        with open(packet["outcome_path"], encoding="utf-8") as handle:
            published = json.load(handle)
        self.assertEqual(published["outstanding_cleanup"], [attempt])
        self.assertTrue(published["uncertainty"])

    def test_an_interruption_with_that_attempt_outstanding_still_accounts(
            self):
        """And the cleanup WINDOW is not where it lands, which is worth
        saying rather than pretending.

        A settled run leaves nothing outstanding, so the window breaks before
        it sleeps and an interrupt injected through `sleep` never reaches it.
        What IS reachable -- and is the property that matters -- is an
        interruption while an admitted attempt is still outstanding, which is
        this: the accounting runs, the attempt is named, and the outcome is on
        disk before the interrupt is re-raised.
        """
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"))
        with self.assertRaises(
                review_supervisor.SupervisorInterrupted) as got:
            self.reviewing(packet=packet, interrupt_at=2)
        outcome = got.exception.outcome
        self.assertIn("KeyboardInterrupt", outcome["interrupted"])
        attempt = self.admitted_attempt(outcome)
        self.assertEqual(outcome["outstanding_cleanup"], [attempt])
        self.assertTrue(os.path.exists(packet["outcome_path"]))
        self.assertIs(outcome["final_canonical_read"], True)


class ARunThatStopsMovingSaysSoRatherThanWaitingItsBoundOut(
        ReviewLifecycleCase):
    """The admitted no-progress case, with all four conditions really met.

    An accountable attempt whose cleanup is positively COMMITTED, a Job that
    is not terminal because a blocked stage cannot advance, and an observation
    that stops changing for six consecutive ticks.

    It took four claims to reach because three of the four kept holding while
    the fourth did not, and the last obstacle was a defect in this supervisor
    rather than in the fixture: serving counted an identity as accountable
    that the shutdown classified `unallocated` and excluded, so the outstanding
    set never emptied and the rule could not fire. Review
    2026-09-23T13:46:58Z traced it over 42 real cleanup reads.
    """

    STALLING = {"turn_seconds": 180, "total_seconds": 300,
                "cleanup_seconds": 60, "review_invocations": 1,
                "retry": False}

    def stalled(self, **operands):
        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"),
                                    stalling=True, bounds=dict(self.STALLING))
        return packet, self.reviewing(packet=packet, **operands)[1]

    def test_it_stops_on_no_progress_with_an_admitted_attempt(self):
        packet, outcome = self.stalled()
        self.assertEqual(outcome["stopped"], "no-progress")
        self.assertEqual(outcome["stalled_ticks"], baseline.STALLED_TICKS)
        # ALL FOUR CONDITIONS, each asserted rather than assumed.
        self.assertEqual(outcome["admissions"], {"review": 1})
        self.assertEqual(len(outcome["admitted_attempts"]), 1)
        self.assertEqual(outcome["outstanding_cleanup"], [])
        self.assertEqual(outcome["stage_states"],
                         {"review": "completed", "integration": "blocked"})
        for attempt, said in sorted(outcome["cleanup"].items()):
            with self.subTest(attempt=attempt):
                self.assertIn(said["cleanup"], baseline.POSITIVE_CLEANUP)
        # AND IT STOPPED LONG BEFORE ITS BOUND, which is the whole point of
        # reporting a stall rather than waiting the backstop out.
        self.assertLess(outcome["served_seconds"],
                        packet["bounds"]["total_seconds"] / 4)
        self.assertTrue(any("nothing changed for" in one
                            for one in outcome["held_because"]),
                        outcome["held_because"])

    def test_the_excluded_identity_is_named_as_unallocated(self):
        """Excluded, not ignored: the outcome says which and why."""
        _packet, outcome = self.stalled()
        self.assertTrue(outcome["unallocated_attempts"],
                        "the blocked stage's identity was not reported")
        for one in outcome["unallocated_attempts"]:
            with self.subTest(attempt=one):
                self.assertNotIn(one, outcome["admitted_attempts"])
                self.assertIn(one, outcome["observed_attempts"])

    def test_a_GENUINELY_outstanding_runtime_is_never_dropped(self):
        """The fail-closed half, and the reason the fix is not just a filter.

        A run whose ending never settles has a real runtime with real
        outstanding cleanup. If the serving classification dropped identities
        on uncertainty it would empty the outstanding set here too and report
        a stall -- inventing the quiet. It must not: this attempt stays
        outstanding and no-progress must NOT fire.
        """
        _packet, outcome = self.stalled(fail_at=2)
        self.assertEqual(len(outcome["admitted_attempts"]), 1)
        self.assertEqual(outcome["outstanding_cleanup"],
                         outcome["admitted_attempts"])
        self.assertNotEqual(outcome["stopped"], "no-progress")
        self.assertEqual(outcome["stalled_ticks"], 0)


class TheSERVINGOriginReadDoesNotSwallowAnInterrupt(ReviewLifecycleCase):
    """The regression for a defect I reintroduced, in its own place.

    `_serving_origin` first used `_guarded(..., interrupted=[])`. `_guarded`
    catches `BaseException` and appends the interruption to the list it is
    given, and a DISPOSABLE list discards it -- so a `KeyboardInterrupt` raised
    while classifying an origin was swallowed and serving could continue after
    an operator asked the run to stop. W239528's review 2026-09-23T00:50:59Z R1
    found that shape in the progress read; review 2026-09-23T13:52:06Z found it
    here.

    The interrupt is injected INSIDE the origin read, which is a different
    branch from the `sleep` the other interruption cases use.
    """

    STALLING = {"turn_seconds": 180, "total_seconds": 300,
                "cleanup_seconds": 60, "review_invocations": 1,
                "retry": False}

    def driven(self, breaking):
        from unittest import mock

        self.produced()
        packet = self.review_packet(os.path.join(self.root, "review"),
                                    stalling=True, bounds=dict(self.STALLING))
        held = review_supervisor._origin
        seen = {"reads": 0}

        def reading(control, attempt_id, launched, uncertainty):
            seen["reads"] += 1
            # LET THE RUN GET GOING FIRST. Breaking the very first read would
            # test a startup path rather than a serving one.
            if seen["reads"] > 3:
                raise breaking
            return held(control, attempt_id, launched, uncertainty)

        with mock.patch.object(review_supervisor, "_origin", reading):
            try:
                return packet, self.reviewing(packet=packet)[1], None
            except review_supervisor.SupervisorInterrupted as stopped:
                return packet, stopped.outcome, stopped

    def test_an_interrupt_in_the_origin_read_stops_and_publishes(self):
        packet, outcome, stopped = self.driven(
            KeyboardInterrupt("operator stopped during the origin read"))
        self.assertIsNotNone(stopped, "the interrupt was swallowed and "
                                      "serving continued")
        self.assertIn("KeyboardInterrupt", outcome["interrupted"])
        # ADMISSION CLOSED, THE OUTCOME PUBLISHED, AND THE ATTEMPT ACCOUNTED.
        self.assertEqual(outcome["state"], "held")
        # TWO, NOT ONE, AND THAT IS THE FAIL-CLOSED RULE VISIBLE. With the
        # origin read broken, the blocked stage's identity can no longer be
        # classified `unallocated`, so it is NOT dropped -- it keeps its
        # cleanup obligation. Asserting exactly one here would have been
        # asserting that uncertainty silently shrinks the accountable set.
        self.assertGreaterEqual(len(outcome["admitted_attempts"]), 1,
                                outcome["admitted_attempts"])
        self.assertEqual(outcome["admissions"], {"review": 1})
        self.assertTrue(os.path.exists(packet["outcome_path"]))
        with open(packet["outcome_path"], encoding="utf-8") as handle:
            self.assertIn("KeyboardInterrupt",
                          json.load(handle)["interrupted"])

    def test_an_ordinary_failure_in_the_origin_read_keeps_it_accountable(self):
        """Fail closed: `FOREIGN` is not excluded, so nothing leaves the set.

        A different branch from the `sleep` failure the other cases inject --
        this one is inside the classification itself.
        """
        _packet, outcome, stopped = self.driven(
            RuntimeError("the origin read did not complete"))
        self.assertIsNone(stopped)
        self.assertTrue(any("did not complete" in one
                            for one in outcome["uncertainty"]),
                        outcome["uncertainty"])
        # NOTHING WAS DROPPED ON UNCERTAINTY, so the run cannot report the
        # quiet it would otherwise have invented.
        self.assertNotEqual(outcome["stopped"], "no-progress")


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only the cases DEFINED HERE, not the ones inherited.

    `BaselineCase` is subclassed for its fixture, and that fixture's ancestors
    carry their own `test_` methods -- so excluding the base class by name was
    not enough: the three classes below inherited W239528's and the product
    suite's cases and ran twelve of them under this dossier's name. The filter
    is each class's OWN `__dict__`, which is the only set this module wrote.
    """
    del standard, pattern
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if not (isinstance(value, type)
                and issubclass(value, unittest.TestCase)
                and value.__module__ == __name__
                and name != "ReviewLifecycleCase"):
            continue
        for method in sorted(one for one in vars(value)
                             if one.startswith("test_")):
            suite.addTest(value(method))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
