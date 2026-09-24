"""The composed abandonment, CALLED -- through the accepted faulted fixture.

Owner 255356: "First deliver and run a focused fixture invoking actual composed
abandonment and replay through fake engine/provider boundaries; use its
failures to correct the implementation. Do not substitute broad suites that
never call the new operation."

Five claims of mine returned with guards corrected and nothing calling them.
This calls them.

THE FIXTURE IS THE PRODUCT'S OWN.
`AFaultedTerminalSurvivesTheContainerThatWroteIt` drives a REAL correlated
faulted terminal -- the real `baton_worker` over the
real exchange with an agent that fails its turn -- and then exits the container
unasked. That is exactly the state the live two-Job run left behind: runtime
started, worker never answered, `fault_code: agent`, no receipt. The engine is
that fixture's fake CLI runner, so no container, image, provider or network is
reached.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from baton_v12.worker_manager import custody                  # noqa: E402
from tests.tools.test_single_worker import (                  # noqa: E402
    AFaultedTerminalSurvivesTheContainerThatWroteIt)


def intake_cleanup(control, attempt_id, digest):
    """The committed abandonment cleanup for one attempt and one policy."""
    from baton_v12.worker_manager import intake

    return intake.abandonment_cleanup_of(
        control, attempt_id=attempt_id, retention_policy_digest=digest)


class TheComposedAbandonmentIsCalled(
        AFaultedTerminalSurvivesTheContainerThatWroteIt):
    """The capability, invoked over a genuinely faulted attempt."""

    REASON = "the two-Job run stopped and this attempt never answered"

    class Removing(AFaultedTerminalSurvivesTheContainerThatWroteIt.Exiting):
        """The fixture's engine, plus what a REMOVAL does to it.

        The base answers `inspect` with `State.Running: True` forever, so a
        force-removal is followed by an observation that still reports the
        runtime present and the abandonment settles `failed`. A real engine
        answers a missing container by failing the inspect, and positive
        absence is what `destroy_abandoned` is owed -- so this models it.

        NOTHING IS WEAKENED: the manager still has to ASK, and it still has to
        get absence rather than assume it.
        """

        def __init__(self):
            super().__init__()
            self.removed = False

        @staticmethod
        def custodian(argv):
            """The mount and verb of a CUSTODY act, or `None`.

            IDENTITY-BOUND, like the absence below. A custody helper is a
            `run` whose derived name carries `CUSTODY_NAME` and whose one
            bind lands on `CUSTODY_ROOT`; anything else is a runtime start
            and is answered as one. The constants come from the product so a
            build that moved either makes this stop matching rather than
            silently answering for something else.
            """
            if len(argv) < 2 or argv[1] != "run":
                return None
            named = source = None
            for index, operand in enumerate(argv[:-1]):
                if operand == "--name":
                    named = argv[index + 1]
                elif operand == "--mount":
                    parts = dict(part.split("=", 1) for part
                                 in argv[index + 1].split(",") if "=" in part)
                    if parts.get("target") == custody.CUSTODY_ROOT:
                        source = parts.get("source")
            if named is None or not named.startswith(custody.CUSTODY_NAME):
                return None
            return source, argv[-1]

        def acting(self, argv, mount, verb):
            """What the custodian PROGRAM prints, over the real directory.

            Review 2026-09-24T08:59:44Z sent me to the typed answer, and it
            said `the act printed no document this manager could read`: the
            base fake answered the helper's `run` like a runtime start --
            status 0, stdout `runtime-single-1` -- so a correct product
            refused to record an act it could not account for. It also
            RE-ASSIGNED the attempt's runtime id, resurrecting a runtime the
            removal had just made absent.

            So the fake answers as the custodian, and it answers ABOUT THE
            DIRECTORY THE MANAGER SELECTED: the counts are a walk of the
            mount source. NOTHING IS CREATED -- a missing mount answers the
            custodian's own typed refusal, which is accountable and is not
            `ok`, so the manager still refuses. The product's rule that an
            act it cannot account for is not recorded is untouched.
            """
            self.vectors.append(list(argv))
            if mount is None or not os.path.isdir(mount):
                return self.answer(status=2, stdout=json.dumps(
                    {"custody": "refused",
                     "why": f"no directory is mounted at "
                            f"{custody.CUSTODY_ROOT}"}))
            entries = sum(len(directories) + len(files) for _current,
                          directories, files in os.walk(mount))
            if verb == "discard":
                document = {"custody": "discard", "removed": entries,
                            "kept": 0}
            else:
                document = {"custody": verb, "entries": entries,
                            "not_ours": 0}
            document["running_as"] = [os.getuid(), os.getgid()]
            return self.answer(stdout=json.dumps(document) + "\n")

        def __call__(self, argv, *, seconds=None):
            acting = self.custodian(argv)
            if acting is not None:
                # BEFORE THE `run` BRANCH, deliberately: the base one would
                # take this helper for the attempt's own runtime.
                return self.acting(argv, *acting)
            if len(argv) > 1 and argv[1] == "rm":
                self.removed = True
                self.vectors.append(list(argv))
                return self.answer()
            if self.removed and len(argv) > 1 and argv[1] == "ps":
                # AN EMPTY LIST IS ABSENCE; a non-zero status is an engine
                # that could not be asked, which the manager reads as
                # uncertainty rather than as absence. The first version of
                # this fake answered non-zero and the manager said so:
                # "the engine could not list runtimes".
                self.vectors.append(list(argv))
                return self.answer()
            if (self.removed and len(argv) > 1 and argv[1] == "inspect"
                    and self.runtime_id in argv):
                # ASKED ABOUT *THIS* RUNTIME. An absence answered to whatever
                # was inspected would also answer for a custody helper's own
                # reconciliation, which is a different identity and a
                # different fact.
                # IDENTITY-BOUND ABSENCE. Review 2026-09-24T08:55:48Z: a bare
                # "no such container" leaves the cleanup UNCERTAIN, because
                # `oci` answers absent only when the engine names the EXACT
                # runtime it was asked about -- "No such container: runtime-2;
                # request was for runtime-1" is a different fact. The real
                # daemon names it, so this does.
                self.vectors.append(list(argv))
                return self.answer(
                    status=1,
                    stderr=f"Error response from daemon: No such container: "
                           f"{self.runtime_id}")
            return super().__call__(argv, seconds=seconds)

    def faulted_with_stage(self, incarnation):
        """The accepted driver, plus the stage document the call needs.

        `faulted` does not return the stage, and the capability binds on it,
        so this re-reads the commanded stage for the same attempt rather than
        composing a second one.
        """
        # CAPTURED FROM THE DRIVE, not re-derived. `commanded` ticks the
        # pipeline until a worker is commanded and fails if it cannot reach
        # one -- which it cannot a second time, because the attempt has
        # already faulted. So this records the answer the accepted driver
        # itself used rather than asking for another.
        # THE ENGINE THAT ANSWERS A REMOVAL, swapped in for the accepted one.
        held_engine = self.Exiting
        # EVERY ENGINE THE DRIVE BUILDS, recorded. `faulted` constructs its
        # own and keeps it local, so a case that has to change the engine's
        # posture mid-test has no other way to reach it.
        self.engines = engines = []

        class Recorded(self.Removing):
            def __init__(inner):
                super().__init__()
                engines.append(inner)

        self.Exiting = Recorded
        self.addCleanup(setattr, self, "Exiting", held_engine)
        seen = {}
        original = self.commanded

        def recording(job, operations):
            answer = original(job, operations)
            seen.setdefault("answer", answer)
            return answer

        self.commanded = recording
        try:
            held = self.faulted(incarnation)
        finally:
            self.commanded = original
        # CLOSED WHEN THE CASE ENDS. The base closes the two stores it opens;
        # the composed operations hold their own handles, and the accepted
        # cases close them explicitly -- without it these cases leak a
        # connection per drive and say so as a ResourceWarning.
        self.addCleanup(held[2].close)
        attempt_id = held[5]
        stage = seen["answer"]["jobs"][0]["stages"][0]
        if stage["attempt_id"] != attempt_id:
            self.fail(f"the commanded stage names {stage['attempt_id']!r} "
                      f"and the faulted attempt is {attempt_id!r}")
        return held, stage

    def test_a_faulted_attempt_reaches_a_positive_cleanup(self):
        """The whole point: a receiptless fault ends with a cleanup record.

        `retained` is positive cleanup in the accepted vocabulary. A successful
        CALL is not the assertion -- the committed record is.
        """
        from baton_v12.worker_manager import intake
        held, stage = self.faulted_with_stage("abandon-1")
        control, operations, attempt_id = held[1], held[2], held[5]
        answered = operations.abandon_attempt(
            attempt_id=attempt_id, reason=self.REASON, stage=stage)
        self.assertTrue(answered["fenced"].get("fenced"))
        self.assertEqual(answered["intent"].get("reason"), self.REASON)
        settled = intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id,
            retention_policy_digest=self.config["retention_policy_digest"])
        self.assertIsNotNone(settled, "no committed abandonment cleanup")
        # THE SETTLEMENT CARRIES THE CLEANUP; the mode is inside it. My first
        # two rounds read `settled["cleanup"]` as the mode and compared a
        # document to a string, which is why this failed after the operation
        # had already succeeded.
        cleanup = settled["cleanup"]
        self.assertEqual(cleanup.get("cleanup"), "retained")
        self.assertEqual(cleanup.get("state"), "absent")
        # BOTH ROOTS ACCOUNTED FOR, quoting the custodian's own document --
        # which is the property the custody act exists to provide and the one
        # an unaccountable act correctly refused to record.
        custody_records = cleanup["directory_custody"]
        self.assertEqual(sorted(custody_records), ["result", "workspace"])
        for root, record in custody_records.items():
            self.assertEqual(record["verb"], "normalize")
            self.assertEqual(record["root"], root)
            self.assertEqual(json.loads(record["account"])["custody"],
                             "normalize")

    def test_the_abandoned_gate_is_discharged_and_the_receipt_replays(self):
        """THE GATE THE ACT INSTALLED, carried -- and carried only once.

        The fence and `runtime-quiescence:<generation>` commit together, and
        an abandonment has no ordinary ending in its future to discharge
        them; for two claims this was an expected failure recording that
        nothing carried it. It is composed now, so the expectation is an
        ordinary one -- and a second abandonment replays the SAME receipt
        rather than discharging a gate twice.
        """
        from baton_v12.worker_manager import intake
        held, stage = self.faulted_with_stage("abandon-6")
        control, operations, attempt_id = held[1], held[2], held[5]
        answered = operations.abandon_attempt(
            attempt_id=attempt_id, reason=self.REASON, stage=stage)
        discharge = intake.abandoned_gate_discharge_of(control, attempt_id)
        self.assertIsNotNone(discharge, "no committed abandoned gate "
                                        "discharge")
        # THE GATE THIS ACT FENCED, not a gate named anywhere else.
        self.assertEqual(discharge.get("gate"),
                         answered["fenced"].get("gate"))
        operations.abandon_attempt(attempt_id=attempt_id, reason=self.REASON,
                                   stage=stage)
        self.assertEqual(
            intake.abandoned_gate_discharge_of(control, attempt_id), discharge)

    def test_a_discharge_is_not_claimed_over_an_unsettled_cleanup(self):
        """The gate is discharged on a committed abandonment or not at all.

        The interrupted settlement journals no cleanup, and a discharge
        recorded over one would be this manager claiming an absence proof it
        never committed.
        """
        from baton_v12.worker_manager import intake
        self.Removing = self.Wavering
        held, stage = self.faulted_with_stage("abandon-8")
        control, operations, attempt_id = held[1], held[2], held[5]
        operations.abandon_attempt(attempt_id=attempt_id, reason=self.REASON,
                                   stage=stage)
        self.assertIsNone(
            intake.abandonment_cleanup_of(
                control, attempt_id=attempt_id,
                retention_policy_digest=self.config[
                    "retention_policy_digest"]))
        self.assertIsNone(
            intake.abandoned_gate_discharge_of(control, attempt_id),
            "a gate discharge was claimed over a cleanup nobody committed")

    def test_a_repeat_is_a_replay_and_not_a_second_ending(self):
        """The core owns replay; this proves the wrapper lets it."""
        from baton_v12.worker_manager import intake
        held, stage = self.faulted_with_stage("abandon-2")
        control, operations, attempt_id = held[1], held[2], held[5]
        first = operations.abandon_attempt(
            attempt_id=attempt_id, reason=self.REASON, stage=stage)
        # WHAT THE WORLD WAS ASKED TO DO, counted before the replay. Review
        # 2026-09-24T09:12:54Z: comparing operation identities is not evidence
        # that nothing was destroyed twice. A removal, a custody act and a
        # credential materialization are the three effects that must not
        # repeat, so each is counted at the boundary that performs it.
        before = self.effects()
        # AND THE COUNTS ARE NOT ZERO, or the comparison below would pass over
        # a fixture that never performed the acts it claims not to repeat.
        self.assertGreaterEqual(before["removals"], 1)
        self.assertGreaterEqual(before["custody_acts"], 2)
        again = operations.abandon_attempt(
            attempt_id=attempt_id, reason=self.REASON, stage=stage)
        self.assertEqual(again["cleanup"].get("cleanup"),
                         first["cleanup"].get("cleanup"))
        self.assertEqual(again["cleanup"]["operation"],
                         first["cleanup"]["operation"])
        self.assertEqual(self.effects(), before,
                         "the replay repeated a destructive effect")
        settled = intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id,
            retention_policy_digest=self.config["retention_policy_digest"])
        self.assertEqual(settled["cleanup"].get("cleanup"), "retained")

    class Wavering(Removing):
        """Removed, and then an engine that cannot be asked -- once.

        THE INTERRUPTED SETTLEMENT, which is a DIFFERENT case from replay.
        `abandon_attempt` journals nothing when the observation is not an
        ending: "nothing is journalled, so a retry runs the removal again --
        which is safe, because force-removal of an already absent exact
        identity answers absent". The repeat case above proves the OTHER
        thing, that a committed cleanup replays. Review 2026-09-24T08:55:48Z
        said these are two cases; this is the first of them.
        """

        def __init__(self):
            super().__init__()
            self.wavering = True

        def __call__(self, argv, *, seconds=None):
            if (self.wavering and self.removed and len(argv) > 1
                    and argv[1] in ("ps", "inspect")):
                # THE ENGINE COULD NOT BE ASKED. Not absence, and the manager
                # must not read it as one.
                self.vectors.append(list(argv))
                return self.answer(status=1, stderr="Cannot connect to the "
                                                    "Docker daemon")
            return super().__call__(argv, seconds=seconds)

    def test_an_interrupted_settlement_journals_nothing_and_the_retry_ends_it(
            self):
        """Uncertainty first, absence second: one ending, committed once."""
        from baton_v12.worker_manager import intake
        self.Removing = self.Wavering
        held, stage = self.faulted_with_stage("abandon-7")
        control, operations, attempt_id = held[1], held[2], held[5]
        engine = held[0] if hasattr(held[0], "vectors") else None
        first = operations.abandon_attempt(
            attempt_id=attempt_id, reason=self.REASON, stage=stage)
        self.assertNotEqual(first["cleanup"].get("cleanup"), "retained")
        self.assertIsNone(
            intake.abandonment_cleanup_of(
                control, attempt_id=attempt_id,
                retention_policy_digest=self.config[
                    "retention_policy_digest"]),
            "an unsettled cleanup was journalled anyway")
        del engine
        for one in self.engines:
            one.wavering = False
        again = operations.abandon_attempt(
            attempt_id=attempt_id, reason=self.REASON, stage=stage)
        self.assertEqual(again["cleanup"].get("cleanup"), "retained")
        settled = intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id,
            retention_policy_digest=self.config["retention_policy_digest"])
        self.assertEqual(settled["cleanup"].get("cleanup"), "retained")

    def effects(self):
        """Every irreversible thing the engine and the homes were ASKED for.

        Counted from the engine's own recorded vectors and from the credential
        home's own state, not from what an answer says happened.
        """
        removals = customs = 0
        for engine in self.engines:
            for vector in engine.vectors:
                if len(vector) < 2:
                    continue
                if vector[1] == "rm":
                    removals += 1
                elif engine.custodian(vector) is not None:
                    customs += 1
        return {"removals": removals, "custody_acts": customs,
                "credential_roots": sorted(
                    os.listdir(self.config["credential_home"]))
                if os.path.isdir(self.config["credential_home"]) else []}

    def mount_roots(self, attempt_id):
        """The two manager-owned mount sources this attempt's container got.

        The same two derivations `TheFailedStartEndingCommitsWithItsNaming`
        reads, because they are the two roots an ending has to let go of and
        a fake custody report says nothing about either.
        """
        from tools import single_worker

        return (os.path.join(os.path.realpath(self.config["launch_home"]),
                             attempt_id),
                single_worker.credentials.CredentialHome(
                    self.config["credential_home"]).volatile_root(attempt_id))

    def test_the_credential_and_launch_roots_are_let_go(self):
        """POSITIVE ABSENCE ON THE FILESYSTEM, asked of the filesystem.

        Review 2026-09-24T09:29:06Z: "the fake custody report is deliberately
        not a filesystem-normalization proof". These two roots are real
        directories this deployment created, so whether they are gone is a
        question `lexists` answers.
        """
        from tools import single_worker

        held, stage = self.faulted_with_stage("abandon-9")
        control, operations, attempt_id = held[1], held[2], held[5]
        launch_root, credential_root = self.mount_roots(attempt_id)
        # THEY REALLY WERE THERE, or the absence below proves nothing.
        self.assertTrue(os.path.lexists(launch_root), launch_root)
        self.assertTrue(os.path.lexists(credential_root), credential_root)
        operations.abandon_attempt(attempt_id=attempt_id, reason=self.REASON,
                                   stage=stage)
        self.assertFalse(os.path.lexists(credential_root),
                         "the credential root survived the ending")
        self.assertIsNone(
            single_worker.credentials.CredentialHome(
                self.config["credential_home"]).read_state(attempt_id),
            "the credential lifecycle record survived the ending")
        self.assertFalse(os.path.lexists(launch_root),
                         "the launch root survived the ending")
        del control

    def test_a_failed_discharge_keeps_the_cleanup_and_the_retry_finishes(self):
        """The lost receipt, which is a crash boundary and not a restart.

        The cleanup commits first and the discharge second; a failure between
        them must leave the committed ending alone and must not re-run any
        destructive act when the retry completes the discharge.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage("abandon-10")
        control, operations, attempt_id = held[1], held[2], held[5]
        original = intake.discharge_abandoned_quiescence_gate

        def failing(*arguments, **operands):
            del arguments, operands
            raise ContractRefusal("refused", "precondition",
                                  "the fixture severed the discharge")

        intake.discharge_abandoned_quiescence_gate = failing
        self.addCleanup(setattr, intake,
                        "discharge_abandoned_quiescence_gate", original)
        with self.assertRaises(ContractRefusal):
            operations.abandon_attempt(attempt_id=attempt_id,
                                       reason=self.REASON, stage=stage)
        digest = self.config["retention_policy_digest"]
        settled = intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest)
        self.assertIsNotNone(settled, "the refused discharge lost the "
                                      "committed cleanup")
        self.assertEqual(settled["cleanup"].get("cleanup"), "retained")
        self.assertIsNone(
            intake.abandoned_gate_discharge_of(control, attempt_id))

        before = self.effects()
        intake.discharge_abandoned_quiescence_gate = original
        operations.abandon_attempt(attempt_id=attempt_id, reason=self.REASON,
                                   stage=stage)
        self.assertIsNotNone(
            intake.abandoned_gate_discharge_of(control, attempt_id),
            "the retry never discharged the gate")
        self.assertEqual(self.effects(), before,
                         "the retry repeated a destructive effect")

    def test_a_second_declaration_naming_another_reason_is_refused(self):
        """One identity carries one act, and a changed operand changes nothing.

        The retention policy is the deployment's and a caller cannot vary it
        through this composition; the REASON is the one operand a second
        declaration could differ in, and it does.
        """
        from baton_v12.contracts import ContractRefusal

        held, stage = self.faulted_with_stage("abandon-11")
        operations, attempt_id = held[2], held[5]
        operations.abandon_attempt(attempt_id=attempt_id, reason=self.REASON,
                                   stage=stage)
        before = self.effects()
        with self.assertRaises(ContractRefusal) as caught:
            operations.abandon_attempt(
                attempt_id=attempt_id,
                reason="a different account of the same attempt", stage=stage)
        self.assertEqual(self.effects(), before,
                         "a refused declaration still changed the world")
        del caught

    def test_an_engine_that_cannot_act_refuses_and_journals_nothing(self):
        """An ADAPTER REFUSAL is not an ending, and leaves no record.

        The engine boundary raising is the case a manager must not settle
        anything on: nothing is journalled, and a later retry over a working
        engine reaches the ordinary ending.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage("abandon-12")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        for engine in self.engines:
            engine.raising = RuntimeError("the fixture severed the engine")
        with self.assertRaises((ContractRefusal, RuntimeError)):
            operations.abandon_attempt(attempt_id=attempt_id,
                                       reason=self.REASON, stage=stage)
        self.assertIsNone(
            intake.abandonment_cleanup_of(
                control, attempt_id=attempt_id,
                retention_policy_digest=digest),
            "a cleanup was journalled over an engine that could not act")
        self.assertIsNone(
            intake.abandoned_gate_discharge_of(control, attempt_id))
        for engine in self.engines:
            engine.raising = None
        answered = operations.abandon_attempt(
            attempt_id=attempt_id, reason=self.REASON, stage=stage)
        self.assertEqual(answered["cleanup"].get("cleanup"), "retained")

    def test_a_prior_cancellation_is_recovered_by_replaying_its_fence(self):
        """POSITIVE PRIOR-FENCE RECOVERY -- owner selection 255814.

        Before the correction this refused: the abandonment derived its own
        Authority identity, and a generation the cancellation had already
        ended could not be fenced a second time. It now REPLAYS the
        cancellation's own operation, with that operation's own reason and
        this attempt's exact fixed assignment, and acts only on the
        Authority's validated answer.

        THE DECLARATION STAYS ITS OWN. The abandonment's reason is what the
        intent records and what every later reader sees; only the FENCE
        borrows the cancellation's identity and reason, because the Authority
        signs a cancel over `{expect, reason}` and anything else would collide
        rather than replay.
        """
        from baton_v12.worker_manager import attempt_runtime_of, intake

        held, stage = self.faulted_with_stage("abandon-13")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        stopped = "the supervisor stopped this attempt"
        operations.cancel_attempt(attempt_id=attempt_id, reason=stopped)
        self.assertEqual(
            attempt_runtime_of(control, attempt_id)["execution_runtime"],
            "cancel-requested")

        answered = operations.abandon_attempt(attempt_id=attempt_id,
                                              reason=self.REASON, stage=stage)
        self.assertTrue(answered["fenced"].get("fenced"))
        # THE DECLARATION IS THE ABANDONMENT'S, and the fence is the
        # cancellation's -- both true at once, which is the whole design.
        self.assertEqual(answered["intent"]["reason"], self.REASON)
        self.assertTrue(answered["intent"]["authority_operation_id"]
                        .startswith("authority.attempt.cancel:"))
        cleanup = answered["cleanup"]
        self.assertEqual(cleanup.get("cleanup"), "retained")
        self.assertEqual(cleanup.get("state"), "absent")
        settled = intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest)
        self.assertEqual(settled["cleanup"].get("cleanup"), "retained")
        self.assertIsNotNone(
            intake.abandoned_gate_discharge_of(control, attempt_id),
            "the recovered ending left its gate undischarged")
        # AND IT IS ONE ENDING. A repeat replays without removing or
        # normalizing anything a second time.
        before = self.effects()
        again = operations.abandon_attempt(attempt_id=attempt_id,
                                           reason=self.REASON, stage=stage)
        self.assertEqual(again["cleanup"]["operation"],
                         cleanup["operation"])
        self.assertEqual(self.effects(), before,
                         "the replay repeated a destructive effect")

    def declared_then_severed(self, incarnation):
        """A committed declaration whose call never reached the fence.

        THE OLDER PERSISTED SHAPE, written the way the build wrote it before
        this correction: the declaration commits under the abandonment's OWN
        fence identity, and then the call dies. Review 2026-09-24T10:11:35Z
        asked for exactly this history rather than only declarations created
        after a cancellation.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage(incarnation)
        operations, attempt_id = held[2], held[5]
        original = intake.abandon_attempt

        def declaring(store, port, adapter, *, attempt_id, reason,
                      retention_policy_digest, seconds=None, reclaim=None):
            del port, adapter, retention_policy_digest, seconds, reclaim
            attempt = intake._attempt_of(store._connection, attempt_id)
            expect = intake._require_assignment(attempt, attempt_id)
            intake._abandon_intent(
                store, attempt, attempt_id, expect, reason,
                intake._abandon_fence_operation_id(attempt))
            raise ContractRefusal("refused", "precondition",
                                  "the fixture severed the fence")

        intake.abandon_attempt = declaring
        try:
            with self.assertRaises(ContractRefusal):
                operations.abandon_attempt(attempt_id=attempt_id,
                                           reason=self.REASON, stage=stage)
        finally:
            intake.abandon_attempt = original
        return held, stage

    def test_an_interrupted_declaration_cancelled_after_it_still_ends(self):
        """RESUMED OLD INTENT, and this is the review's P1 closed positively.

        The first cut of this correction chose the declaration's fence operand
        from the world as it stands now, so this history -- declare, die,
        cancel, retry -- refused at §4.2 with the cleanup still absent. A
        passing refusal test characterized the gap; it was not the selected
        outcome.

        Now the RECORD decides the operand and the WORLD decides the fence:
        the old declaration's bytes are reused exactly as written, and the
        generation is fenced by replaying the cancellation this manager
        validated. Both facts, separately.
        """
        from baton_v12.worker_manager import intake

        held, stage = self.declared_then_severed("abandon-17")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        attempt = intake._attempt_of(control._connection, attempt_id)
        # THE BYTES AS WRITTEN, captured before the cancellation exists.
        before_record = control.operation_record(
            intake._abandon_operation_id(attempt))
        declared = json.loads(before_record["result"])
        self.assertEqual(declared["authority_operation_id"],
                         intake._abandon_fence_operation_id(attempt))

        operations.cancel_attempt(attempt_id=attempt_id, reason="interrupted")
        answered = operations.abandon_attempt(attempt_id=attempt_id,
                                              reason=self.REASON, stage=stage)
        self.assertTrue(answered["fenced"].get("fenced"))
        self.assertEqual(answered["cleanup"].get("cleanup"), "retained")
        self.assertEqual(answered["cleanup"].get("state"), "absent")
        self.assertIsNotNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))
        self.assertIsNotNone(
            intake.abandoned_gate_discharge_of(control, attempt_id),
            "the resumed ending left its gate undischarged")
        # THE OLD JOURNAL BYTES ARE UNTOUCHED -- same record, same digest,
        # same declared fence operand, same reason.
        after_record = control.operation_record(
            intake._abandon_operation_id(attempt))
        self.assertEqual(after_record["result"], before_record["result"])
        self.assertEqual(after_record["signature"],
                         before_record["signature"])
        self.assertEqual(answered["intent"], declared)
        # AND IT IS ONE ENDING.
        effects = self.effects()
        again = operations.abandon_attempt(attempt_id=attempt_id,
                                           reason=self.REASON, stage=stage)
        self.assertEqual(again["cleanup"]["operation"],
                         answered["cleanup"]["operation"])
        self.assertEqual(self.effects(), effects,
                         "the resumed replay repeated a destructive effect")

    def test_a_resumed_declaration_naming_another_reason_still_refuses(self):
        """The signature check is not weakened by resumption.

        The operand is taken from the record; the REASON is still the
        caller's, and a resumed call naming a different one is a different
        declaration at one identity.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import intake

        held, stage = self.declared_then_severed("abandon-20")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        operations.cancel_attempt(attempt_id=attempt_id, reason="interrupted")
        before = self.effects()
        with self.assertRaises(ContractRefusal) as caught:
            operations.abandon_attempt(
                attempt_id=attempt_id,
                reason="a different account of the same attempt", stage=stage)
        self.assertIn("different kind or signature", caught.exception.message)
        self.assertIsNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))
        self.assertEqual(self.effects(), before,
                         "the refused declaration still changed the world")

    def test_the_preserved_runs_shape_now_has_exactly_one_door(self):
        """THE RECOVERY SUBJECT, and which ending is the one that serves it.

        Under claim 255665 this proved all THREE doors shut and that was the
        P1. Owner selection 255814 opened the right one. It asserts both
        halves: the abandonment recovers this shape, and the other two still
        decline for their own unchanged reasons -- which is why this ending
        belongs here rather than a relaxation of either.

        The shape is the preserved two-Job run's, read from its own control
        store: `quiescent`, `cleanup: pending`, no intake receipt, a committed
        cancellation, and a deadline pin whose policy is null.

        RESTORED under claim 255893: an edit this claim sliced from one case
        name to another and took this one with it. It is real coverage and it
        does not disappear because a slice was careless.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.job_manager import reconcile
        from baton_v12.worker_manager import (attempt_runtime_of, deadlines,
                                              intake, workspaces)
        from tests.job_manager import fixtures

        held, stage = self.faulted_with_stage("abandon-14")
        job, control, operations, attempt_id = (held[0], held[1], held[2],
                                                held[5])
        digest = self.config["retention_policy_digest"]
        operations.cancel_attempt(attempt_id=attempt_id, reason="interrupted")
        for _ in range(4):
            reconcile(job, operations, now=fixtures.NOW)
        state = attempt_runtime_of(control, attempt_id)
        self.assertEqual(state["execution_runtime"], "quiescent")
        self.assertEqual(state["cleanup"], "pending")
        self.assertIsNone(intake.intake_receipt_of(control, attempt_id))
        pin = deadlines.deadline_of(control, attempt_id=attempt_id)
        self.assertIsNotNone(pin, "no deadline pin was committed at start")
        self.assertIsNone(pin["policy"])

        worker = operations._worker
        roots = workspaces.adopted_assignment_workspace(
            worker.given["workspace_storage"], attempt_id)
        # THE ORDINARY ENDING still answers BLOCKED ON INTAKE -- no refusal,
        # no adapter call, no cleanup record -- because it is authorized by a
        # receipt this attempt never produced.
        blocked = intake.authorize_cleanup(
            control, worker.port, worker._adapter(roots, None, None, None),
            attempt_id=attempt_id, retention_policy_digest=digest)
        self.assertIn("intake receipt", blocked["why"])
        self.assertIsNone(intake.cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))
        # THE DEADLINE OWNER still refuses, because the pin carries no policy.
        with self.assertRaises(ContractRefusal):
            deadlines.advance_deadline(
                control, worker.port, None, None,
                attempt_id=attempt_id, retention_policy_digest=digest)

        # AND THE ABANDONMENT RECOVERS IT.
        answered = operations.abandon_attempt(attempt_id=attempt_id,
                                              reason=self.REASON, stage=stage)
        self.assertEqual(answered["cleanup"].get("cleanup"), "retained")
        self.assertEqual(answered["cleanup"].get("state"), "absent")
        self.assertIsNotNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))
        self.assertIsNotNone(
            intake.abandoned_gate_discharge_of(control, attempt_id))

    def test_a_cancellation_record_this_attempt_did_not_write_is_refused(self):
        """FAIL CLOSED on the evidence the new fence replay rests on.

        The correction fences by replaying a cancellation, so the record that
        authorizes that replay has to be provably this attempt's. A row at the
        derived key whose document or signature this attempt's own operands do
        not produce must refuse -- not be ignored, because ignoring it would
        fence under a second identity over a generation that may be ended.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import attempts, intake

        held, stage = self.faulted_with_stage("abandon-18")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        operations.cancel_attempt(attempt_id=attempt_id, reason="interrupted")
        attempt = intake._attempt_of(control._connection, attempt_id)
        operation_id = attempts._cancel_operation_id(attempt)
        row = control._connection.execute(
            "SELECT result FROM operations WHERE operation_id = ?",
            (operation_id,)).fetchone()
        tampered = json.loads(row["result"])
        tampered["attempt_id"] = "attempt-" + "5" * 64
        control._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps(tampered, sort_keys=True), operation_id))
        control._connection.commit()

        before = self.effects()
        with self.assertRaises(ContractRefusal) as caught:
            operations.abandon_attempt(attempt_id=attempt_id,
                                       reason=self.REASON, stage=stage)
        self.assertIn("evidence about the attempt", caught.exception.message)
        self.assertIsNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))
        self.assertEqual(self.effects(), before,
                         "a refused cancellation record still changed the "
                         "world")

    def test_a_discharge_committed_remotely_replays_after_a_lost_receipt(self):
        """The OTHER interruption: the remote act landed, the receipt did not.

        Review 2026-09-24T09:12:54Z drew this distinction and I kept the
        weaker case labelled honestly meanwhile. Here the Authority really
        performs the discharge and the LOCAL journal write fails, which is the
        crash a severed call cannot model. The retry must replay the
        Authority's own answer and commit the receipt, removing nothing again.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage("abandon-19")
        control, operations, attempt_id = held[1], held[2], held[5]
        original = type(control).transact

        def losing(store, operation_id, kind, signature, action):
            if kind == intake.ABANDONED_GATE_DISCHARGE_KIND:
                # THE REMOTE ACT HAS ALREADY HAPPENED by the time this runs --
                # `discharge_abandoned_quiescence_gate` calls the Authority
                # and journals afterwards, deliberately, "because a crash
                # between them leaves the authority's own replay to make the
                # next attempt idempotent".
                raise ContractRefusal("refused", "precondition",
                                      "the fixture lost the local receipt")
            return original(store, operation_id, kind, signature, action)

        type(control).transact = losing
        self.addCleanup(setattr, type(control), "transact", original)
        with self.assertRaises(ContractRefusal):
            operations.abandon_attempt(attempt_id=attempt_id,
                                       reason=self.REASON, stage=stage)
        self.assertIsNone(
            intake.abandoned_gate_discharge_of(control, attempt_id),
            "a receipt survived the write that failed")
        before = self.effects()
        type(control).transact = original
        operations.abandon_attempt(attempt_id=attempt_id, reason=self.REASON,
                                   stage=stage)
        self.assertIsNotNone(
            intake.abandoned_gate_discharge_of(control, attempt_id),
            "the retry never replayed the remote discharge")
        self.assertEqual(self.effects(), before,
                         "the retry repeated a destructive effect")

    def test_an_altered_stage_context_is_measured_and_not_assumed(self):
        """The stage IS a caller operand; this records what each member does.

        Review 2026-09-24T09:35:15Z corrected me: a caller supplies the whole
        document, so saying the context "cannot vary" was wrong. MEASURED here
        over the UNPOOLED composition:

          * an altered `job_id` REFUSES -- "stage rows name Job … and this
            store holds no such Job", from the adoption that reads it;
          * an altered `stage_id`, `episode` or `kind` is ACCEPTED, because
            this composition binds `attempt_id` and has no durable stage
            record to bind the rest against.

        CORRECTED under claim 255929, and this docstring said the opposite
        until then. I claimed acceptance was "a real hazard" because `kind`
        decides mounts. IT DOES NOT: `StageComposition._prepare` branches on
        its own `self.role` and `_recovered` reads the attempt's durable grant
        by attempt id, so no altered member here diverts a tree --
        `test_routed_abandonment` pins that at the worker itself. In THIS
        composition `self.stage` is `None`, so the stage-mount branch is not
        even reached and root recovery is keyed on the attempt alone.

        What the accepted members are, then, is inert context. The routed
        binding in `stage_execution.abandon_attempt` stays as operand hygiene
        -- a wrong context should stop before a worker -- and not as the thing
        that keeps the tree correct.
        """
        from baton_v12.contracts import ContractRefusal

        held, stage = self.faulted_with_stage("abandon-15")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        with self.assertRaises(ContractRefusal) as caught:
            operations.abandon_attempt(
                attempt_id=attempt_id, reason=self.REASON,
                stage=dict(stage, job_id="job-somebody-else"))
        self.assertIn("no such Job", caught.exception.message)
        self.assertIsNone(intake_cleanup(control, attempt_id, digest),
                          "the refused context still settled an ending")
        # THE ACCEPTED ONES SETTLE EXACTLY ONE ENDING BETWEEN THEM, which is
        # the property that keeps this from being a second ending per label.
        operations.abandon_attempt(attempt_id=attempt_id, reason=self.REASON,
                                   stage=dict(stage, stage_id="job-a:review"))
        first = intake_cleanup(control, attempt_id, digest)
        self.assertIsNotNone(first)
        before = self.effects()
        for one in (dict(stage, episode=(stage.get("episode") or 0) + 7),
                    dict(stage, kind="review")):
            operations.abandon_attempt(attempt_id=attempt_id,
                                       reason=self.REASON, stage=one)
        self.assertEqual(intake_cleanup(control, attempt_id, digest), first)
        self.assertEqual(self.effects(), before,
                         "an altered context repeated a destructive effect")

    def test_a_restart_changing_the_retention_policy_is_refused(self):
        """The policy is deployment-bound, and a restart can carry another.

        A second composition over the same stores with a DIFFERENT retention
        policy digest must not be handed the first one's committed ending, and
        must not settle a second one.
        """
        from baton_v12.contracts import ContractRefusal

        held, stage = self.faulted_with_stage("abandon-16")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        operations.abandon_attempt(attempt_id=attempt_id, reason=self.REASON,
                                   stage=stage)
        before = self.effects()
        held_digest = operations._worker.given["retention_policy_digest"]
        operations._worker.given["retention_policy_digest"] = (
            "sha256:" + "4" * 64)
        self.addCleanup(operations._worker.given.__setitem__,
                        "retention_policy_digest", held_digest)
        with self.assertRaises(ContractRefusal):
            operations.abandon_attempt(attempt_id=attempt_id,
                                       reason=self.REASON, stage=stage)
        self.assertEqual(self.effects(), before,
                         "the changed policy still changed the world")
        # AND THE FIRST POLICY'S ENDING IS UNTOUCHED.
        self.assertIsNotNone(intake_cleanup(control, attempt_id, digest))
        self.assertIsNone(intake_cleanup(control, attempt_id,
                                         "sha256:" + "4" * 64))

    def test_the_supervisors_shutdown_declaration_is_eligible_only(self):
        """The supervisor's step, CALLED -- and its eligibility rule with it.

        W247941. `two_job_supervisor._declare_abandonment` is what ends a
        runtime the bounded cleanup sweeps could not settle. Review
        2026-09-24T10:23:12Z: "outstanding alone is not eligibility", and
        "report failed abandonment honestly". Both are asserted here over the
        real stores rather than described.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage("abandon-21")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        operations.cancel_attempt(attempt_id=attempt_id, reason="interrupted")

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        # ONE ELIGIBLE ATTEMPT, one this store has never heard of, and one
        # whose stage document was never recorded.
        stranger = "attempt-" + "6" * 64
        Gate.launched_stage[stranger] = dict(stage, attempt_id=stranger)
        declared = two_job_supervisor._declare_abandonment(
            operations, control, Gate,
            [attempt_id, stranger, "attempt-" + "7" * 64],
            reason="the supervisor stopped this run", policy=digest)

        self.assertTrue(declared[attempt_id]["declared"], declared)
        self.assertEqual(declared[attempt_id]["cleanup"], "retained")
        self.assertTrue(declared[attempt_id]["gate_discharged"])
        self.assertIsNotNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))
        # THE TWO THAT WERE NOT DECLARED SAY WHY, in their own words.
        for other in (stranger, "attempt-" + "7" * 64):
            with self.subTest(attempt=other):
                self.assertFalse(declared[other]["declared"])
                self.assertTrue(declared[other]["why"])

    def test_a_declaration_stops_when_the_run_bound_is_exhausted(self):
        """R1: no NEW ending work starts after the selected total is gone.

        The declaration may fence, remove, normalize custody and discharge.
        It used to begin after the reserved window had already expired; it now
        asks what is left before each attempt and records every one from that
        point on as unresolved, with the runtime untouched.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage("abandon-23")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        operations.cancel_attempt(attempt_id=attempt_id, reason="interrupted")

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        before = self.effects()
        declared = two_job_supervisor._declare_abandonment(
            operations, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest,
            remaining=lambda: 0)
        self.assertFalse(declared[attempt_id]["declared"])
        self.assertIn("reserve this shutdown keeps",
                      declared[attempt_id]["why"])
        self.assertEqual(self.effects(), before,
                         "an expired bound still touched the world")
        self.assertIsNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))
        # AND WITH TIME LEFT IT DOES THE WORK, so the bound is what stopped it
        # rather than something else about this attempt.
        declared = two_job_supervisor._declare_abandonment(
            operations, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest,
            remaining=lambda: two_job_supervisor.ABANDONMENT_RESERVE_SECONDS
            + 60)
        self.assertTrue(declared[attempt_id]["declared"], declared)
        self.assertEqual(declared[attempt_id]["cleanup"], "retained")

    def test_one_allowance_decreases_across_the_whole_ending(self):
        """THE BUDGET, MEASURED at every boundary it crosses.

        Owner 256143: "Carry one monotonic decreasing allowance across
        complete abandonment, including observation, fence, removal, custody,
        discharge and readback." The admission check alone could not show
        this; a DELAYED boundary can. Every engine vector consumes time from
        the same budget, so what each one is allowed must fall, and none may
        exceed the package's own ceiling for that vector.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import custody as custody_module

        held, stage = self.faulted_with_stage("abandon-29")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        # A DELIBERATELY SLOW BOUNDARY, on a clock this test owns. Nothing
        # sleeps: each vector simply costs a second of the budget.
        spent = [0]
        asked = []
        for engine in self.engines:
            held_call = engine.__class__.__call__

            def costing(one, argv, *, seconds=None, _held=held_call):
                # THE BUDGET AS IT STOOD WHEN THIS VECTOR WAS COMPOSED, kept
                # beside the allowance it was given: the invariant is about
                # the pair, not about the allowance alone.
                asked.append((argv[1] if len(argv) > 1 else None, seconds,
                              spent[0]))
                spent[0] += 1
                return _held(one, argv, seconds=seconds)

            engine.__class__.__call__ = costing
            self.addCleanup(setattr, engine.__class__, "__call__", held_call)

        declared = two_job_supervisor._declare_abandonment(
            operations, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest,
            remaining=lambda: (two_job_supervisor.ABANDONMENT_RESERVE_SECONDS
                               + 600 - spent[0]))
        self.assertTrue(declared[attempt_id]["declared"], declared)
        self.assertEqual(declared[attempt_id]["cleanup"], "retained")

        # EVERY VECTOR WAS BOUNDED, and none was handed the unbounded `None`
        # an unbounded caller would produce.
        bounded = [one for one in asked if one[1] is not None]
        self.assertTrue(bounded, "no vector carried an allowance at all")
        self.assertEqual(len(bounded), len(asked),
                         f"a vector ran unbounded inside a bounded ending: "
                         f"{asked}")
        # THE INVARIANT IS THE PAIR, not the allowance alone. Each vector is
        # `min(what was left, its own ceiling)`, and the ceilings DIFFER --
        # a removal's is 300 and a custody act's is 2100 -- so the allowances
        # are not a falling sequence and asserting that they were tested the
        # wrong thing. What must hold is that no vector was ever allowed more
        # than the budget standing when it was composed.
        whole = two_job_supervisor.ABANDONMENT_RESERVE_SECONDS + 600
        for verb, seconds, before in bounded:
            with self.subTest(verb=verb):
                self.assertLessEqual(
                    seconds + before, whole,
                    f"{verb} was allowed {seconds} with {whole - before} left")
        # AND THE BUDGET ITSELF FELL, which is what makes it one allowance
        # rather than one value copied per act.
        self.assertLess(bounded[0][2], bounded[-1][2])
        # NO VECTOR EXCEEDED THE PACKAGE'S OWN CEILING for a custody act,
        # which is the largest this ending uses.
        self.assertLessEqual(max(one[1] for one in bounded),
                             custody_module.CUSTODY_ACT_SECONDS)

    def test_every_vector_of_a_bounded_ending_carries_the_allowance(self):
        """CLOSED under claim 256232, and it was an expected failure before.

        Measured under claim 256145 with a costing boundary, a bounded ending
        asked `[60, None, None, 57, None, 55, 54, 53, 52]` -- three vectors
        the allowance did not reach: the label listing and the observation
        inside `recover_credentials`, and the observation `_removed` takes
        after its removal. All three carry it now, so this case reports the
        property rather than the gap.
        """
        import two_job_supervisor

        held, stage = self.faulted_with_stage("abandon-31")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        asked = []
        for engine in self.engines:
            held_call = engine.__class__.__call__

            def watching(one, argv, *, seconds=None, _held=held_call):
                asked.append(seconds)
                return _held(one, argv, seconds=seconds)

            engine.__class__.__call__ = watching
            self.addCleanup(setattr, engine.__class__, "__call__", held_call)

        two_job_supervisor._declare_abandonment(
            operations, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest,
            remaining=lambda: (two_job_supervisor.ABANDONMENT_RESERVE_SECONDS
                               + 600))
        self.assertTrue(asked)
        self.assertNotIn(None, asked,
                         f"vectors ran unbounded inside a bounded ending: "
                         f"{asked}")

    def test_an_unbounded_ending_is_byte_for_byte_what_it_was(self):
        """`None` PRESERVES EXISTING CALLERS, asserted rather than asserted of.

        Every vector of an unbounded abandonment carries exactly what it
        carried before the allowance existed: the package's own value, or
        `None` where there never was one.
        """
        held, stage = self.faulted_with_stage("abandon-30")
        operations, attempt_id = held[2], held[5]
        asked = []
        for engine in self.engines:
            held_call = engine.__class__.__call__

            def watching(one, argv, *, seconds=None, _held=held_call):
                asked.append((argv[1] if len(argv) > 1 else None, seconds))
                return _held(one, argv, seconds=seconds)

            engine.__class__.__call__ = watching
            self.addCleanup(setattr, engine.__class__, "__call__", held_call)

        operations.abandon_attempt(attempt_id=attempt_id, reason=self.REASON,
                                   stage=stage)
        self.assertTrue(asked)
        # THE REMOVAL AND THE INSPECTION ARE UNBOUNDED, as they always were --
        # the new ceilings are clamps for a bounded caller and not new waits.
        #
        # `ps` IS NOT IN THIS LIST AND THAT IS THE PRODUCT'S OWN FACT: the
        # custody act's reclamation has carried `CUSTODY_RECLAIM_SECONDS` for
        # as long as it has existed, so asserting `None` for it would be
        # asserting against a bound this Work did not introduce. Measured
        # rather than assumed -- my first version of this case did assert it
        # and was wrong.
        for verb, seconds in asked:
            if verb in ("rm", "inspect"):
                with self.subTest(verb=verb):
                    self.assertIsNone(seconds)

    def test_the_reserve_is_withheld_from_what_the_work_may_spend(self):
        """The margin is SUBTRACTED, not merely a floor on admission.

        Review 2026-09-24T11:10:32Z: my first version refused below 30 seconds
        and then handed the operation the unchanged remaining callable, so an
        admitted act could spend the reserve too. The work allowance is
        `remaining - reserve` now, so what the boundaries see is already net
        of the margin -- measured here at the vectors rather than read off the
        code.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import custody as custody_module

        held, stage = self.faulted_with_stage("abandon-32")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        reserve = two_job_supervisor.ABANDONMENT_RESERVE_SECONDS

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        asked = []
        for engine in self.engines:
            held_call = engine.__class__.__call__

            def watching(one, argv, *, seconds=None, _held=held_call):
                asked.append((argv[1] if len(argv) > 1 else None, seconds))
                return _held(one, argv, seconds=seconds)

            engine.__class__.__call__ = watching
            self.addCleanup(setattr, engine.__class__, "__call__", held_call)

        whole = reserve + 600
        declared = two_job_supervisor._declare_abandonment(
            operations, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest,
            remaining=lambda: whole)
        self.assertTrue(declared[attempt_id]["declared"], declared)
        bounded = [(verb, one) for verb, one in asked if one is not None]
        self.assertTrue(bounded)
        # THE WORK NEVER SEES THE RESERVE. Review 2026-09-24T13:29:10Z also
        # required the RECLAMATION to be able to spend it, so the two budgets
        # are asserted apart rather than together: the acts and the removal
        # are the work, and they are capped at the whole minus the margin.
        work = [one for verb, one in bounded if verb in ("run", "rm")]
        self.assertTrue(work, asked)
        self.assertLessEqual(max(work), whole - reserve)
        self.assertLess(max(work), whole)
        # AND NOTHING ANYWHERE EXCEEDS THE WHOLE.
        self.assertLessEqual(max(one for _verb, one in bounded), whole)
        del custody_module

    def test_the_reserve_is_the_admission_rule_too(self):
        """One subtraction decides both, so they cannot drift apart."""
        import two_job_supervisor

        held, stage = self.faulted_with_stage("abandon-33")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        reserve = two_job_supervisor.ABANDONMENT_RESERVE_SECONDS

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        before = self.effects()
        # EXACTLY THE RESERVE LEFT IS NOT ENOUGH: the work allowance is zero.
        declared = two_job_supervisor._declare_abandonment(
            operations, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest,
            remaining=lambda: reserve)
        self.assertFalse(declared[attempt_id]["declared"])
        self.assertIn("reserve this shutdown keeps",
                      declared[attempt_id]["why"])
        self.assertEqual(self.effects(), before)

    def test_an_ordinary_run_can_still_abandon(self):
        """THE POSITIVE PATH, in a run the size this deployment actually uses.

        My previous claim derived the reserve from the worst case, made it
        1200s, and so disabled abandonment inside an ordinary 600s run --
        review 2026-09-24T13:43:14Z: "maxima are ceilings not minimum
        grants", and truthful accounting was what had been asked for rather
        than guaranteed completion. The reserve is a bounded ALLOCATION now,
        and this is the case that would have caught the over-correction.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage("abandon-34")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        # THE WHOLE BUDGET OF THE TWO-JOB RUN, not a number chosen to pass.
        declared = two_job_supervisor._declare_abandonment(
            operations, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest,
            remaining=lambda: 600)
        self.assertTrue(declared[attempt_id]["declared"], declared)
        self.assertEqual(declared[attempt_id]["cleanup"], "retained")
        self.assertTrue(declared[attempt_id]["gate_discharged"])
        self.assertEqual(
            two_job_supervisor._settled_by_abandonment(declared),
            [attempt_id])
        self.assertIsNotNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))

    def test_a_budget_that_runs_out_mid_ending_is_held_not_claimed(self):
        """THE BOUNDED FAILURE, which is what the allocation buys honesty for.

        Review 2026-09-24T13:43:14Z asked for a bounded supervise failure
        beside the positive path. The work allowance here is exhausted PART
        WAY THROUGH the ending -- a costing boundary spends it -- so a vector
        is refused mid-sequence. What must come out is a recorded outcome
        that claims nothing: never `retained` with a discharge, never counted
        as settled, and whatever DID commit read back rather than guessed at.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage("abandon-35")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        reserve = two_job_supervisor.ABANDONMENT_RESERVE_SECONDS

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        spent = [0]
        for engine in self.engines:
            held_call = engine.__class__.__call__

            def costing(one, argv, *, seconds=None, _held=held_call):
                spent[0] += 1
                return _held(one, argv, seconds=seconds)

            engine.__class__.__call__ = costing
            self.addCleanup(setattr, engine.__class__, "__call__", held_call)

        # THREE SECONDS OF WORK, and the ending needs more vectors than that.
        declared = two_job_supervisor._declare_abandonment(
            operations, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest,
            remaining=lambda: reserve + 3 - spent[0])
        outcome = declared[attempt_id]
        self.assertIsNot(outcome["declared"], False,
                         f"an exception denied an ending it did not check: "
                         f"{outcome}")
        # NOTHING IS CLAIMED SETTLED.
        self.assertEqual(
            two_job_supervisor._settled_by_abandonment(declared), [],
            f"a budget that ran out still reported a completed ending: "
            f"{outcome}")
        self.assertTrue(outcome.get("why"), outcome)
        # AND WHAT THE STORE SAYS IS WHAT IS REPORTED -- no cleanup claimed
        # that the journal does not carry.
        committed = intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest)
        if committed is None:
            self.assertIsNone(outcome.get("cleanup"))
        else:
            self.assertEqual(outcome.get("cleanup"),
                             committed["cleanup"].get("cleanup"))

    def test_the_worst_case_is_recorded_and_is_not_the_reserve(self):
        """What completion COULD need, kept apart from what is allocated.

        The worst case is five sequential engine calls per custody act, two
        acts, each waiting up to `CUSTODY_RECLAIM_SECONDS` -- 1200s. It is
        recorded so an operator reading "unresolved" knows what this run did
        not buy, and it is deliberately NOT the reserve.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import custody as custody_module

        self.assertEqual(two_job_supervisor._reclamation_worst_case(),
                         2 * 5 * custody_module.CUSTODY_RECLAIM_SECONDS)
        self.assertLess(two_job_supervisor.ABANDONMENT_RESERVE_SECONDS,
                        two_job_supervisor._reclamation_worst_case())
        # AND IT MOVES WITH THE PACKAGE rather than being a literal here.
        held = custody_module.CUSTODY_RECLAIM_SECONDS
        try:
            custody_module.CUSTODY_RECLAIM_SECONDS = held + 7
            self.assertEqual(two_job_supervisor._reclamation_worst_case(),
                             2 * 5 * (held + 7))
        finally:
            custody_module.CUSTODY_RECLAIM_SECONDS = held

    def unresolved_custody(self, incarnation):
        """Drive a REAL external uncertainty: the request crosses, nothing
        answers.

        The engine port raises on the custodian's own vector, which is what a
        killed client looks like from here: `custody_act` submitted, got no
        answer, and says UNRESOLVED. Everything before the submission is
        untouched, so this is the one shape the hold exists for.
        """
        from baton_v12.worker_manager import workspaces

        held, _stage = self.faulted_with_stage(incarnation)
        control, worker, attempt_id = held[1], held[2]._worker, held[5]
        for engine in self.engines:
            held_acting = engine.__class__.acting

            def severed(one, argv, mount, verb, _held=held_acting):
                del mount, verb
                one.vectors.append(list(argv))
                raise RuntimeError("the fixture killed the client")

            engine.__class__.acting = severed
            self.addCleanup(setattr, engine.__class__, "acting", held_acting)
            # THE PRE-ACT RECONCILIATION ANSWERS "NOTHING STRANDED", which is
            # the fake's post-removal listing; without it the base listing
            # answers a worker row the custody reader rightly rejects.
            engine.removed = True
        roots = workspaces.adopted_assignment_workspace(
            worker.given["workspace_storage"], attempt_id)
        return control, worker._adapter(roots, None, None, None), attempt_id

    def test_an_unresolved_submission_holds_the_root(self):
        """THE HOLD, WRITTEN BEFORE THE REQUEST AND STANDING AFTER IT.

        Owner 257086 selected it for actual engine uncertainty; review
        2026-09-24T13:58:36Z placed it at the submission and ruled that the
        same act may not resubmit. Both are asserted here over real stores.
        """
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import custody as custody_module

        control, composed, attempt_id = self.unresolved_custody("abandon-36")
        with self.assertRaises(ContractRefusal) as caught:
            custody_module.normalize_directory(
                control, composed, assignment_id=attempt_id, which="result")
        self.assertIn("did not answer accountably", caught.exception.message)

        # THE EPISODE EXISTS, uncleared, and names the helper that request
        # would have created.
        [episode] = custody_module.custody_holds(control, attempt_id,
                                                 "result")
        self.assertFalse(episode["cleared"])
        self.assertTrue(episode["held"]["helper_identity"].startswith(
            custody_module.CUSTODY_NAME))
        self.assertEqual(episode["held"]["root"], "result")
        self.assertEqual(episode["held"]["verb"], "normalize")

        # AND THE NEXT ACT REFUSES -- even with the custodian working again,
        # because the uncertainty is about what may still be reaching the root.
        for engine in self.engines:
            engine.__class__.acting = \
                TheComposedAbandonmentIsCalled.Removing.acting
        with self.assertRaises(ContractRefusal) as again:
            custody_module.normalize_directory(
                control, composed, assignment_id=attempt_id, which="result")
        self.assertIn("FROZEN", again.exception.message)
        self.assertIn("unreconciled uncertainty episode",
                      again.exception.message)
        # THE OTHER ROOT IS NOT FROZEN: the hold is per root, not per attempt.
        self.assertEqual(
            custody_module.custody_holds(control, attempt_id, "workspace"),
            [])

    def test_a_reconciliation_lifts_one_episode_and_the_act_proceeds(self):
        """An operator's evidence, and what it does and does not lift."""
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import custody as custody_module

        control, composed, attempt_id = self.unresolved_custody("abandon-37")
        with self.assertRaises(ContractRefusal):
            custody_module.normalize_directory(
                control, composed, assignment_id=attempt_id, which="result")
        [episode] = custody_module.custody_holds(control, attempt_id,
                                                 "result")
        helper = episode["held"]["helper_identity"]

        # A CLEARANCE NAMING ANOTHER HELPER IS EVIDENCE ABOUT SOMETHING ELSE.
        with self.assertRaises(ContractRefusal) as wrong:
            custody_module.clear_custody_hold(
                control, attempt_id=attempt_id, which="result", episode=0,
                observed="I looked; nothing is running",
                helper_identity="baton-custody-" + "0" * 32)
        self.assertIn("evidence about the helper", wrong.exception.message)
        # A BLANK OBSERVATION IS NOT AN OBSERVATION.
        with self.assertRaises(ContractRefusal):
            custody_module.clear_custody_hold(
                control, attempt_id=attempt_id, which="result", episode=0,
                observed="   ", helper_identity=helper)
        # AN EPISODE THAT DOES NOT EXIST IS REFUSED.
        with self.assertRaises(ContractRefusal):
            custody_module.clear_custody_hold(
                control, attempt_id=attempt_id, which="result", episode=3,
                observed="I looked", helper_identity=helper)

        custody_module.clear_custody_hold(
            control, attempt_id=attempt_id, which="result", episode=0,
            observed="I inspected the daemon; no helper of that name exists",
            helper_identity=helper)
        [cleared] = custody_module.custody_holds(control, attempt_id,
                                                 "result")
        self.assertTrue(cleared["cleared"])

        # AND THE ACT MAY PROCEED AGAIN, which is what a reconciliation is FOR.
        for engine in self.engines:
            engine.__class__.acting = \
                TheComposedAbandonmentIsCalled.Removing.acting
        answered = custody_module.normalize_directory(
            control, composed, assignment_id=attempt_id, which="result")
        self.assertEqual(answered["root"], "result")
        # A SECOND UNCERTAINTY WOULD BE ITS OWN EPISODE, not covered by the
        # clearance already written -- which is why the episode is in the
        # identity.
        self.assertEqual(
            len(custody_module.custody_holds(control, attempt_id, "result")),
            2)

    def test_an_allowance_never_exceeds_what_is_left(self):
        """R1, reproduced: `allowed(lambda: 0.1, 120)` used to answer 1.

        Rounding UP hands a boundary more time than the caller has, which is
        the one direction an allowance may never round. It rounds down now,
        and a sub-second remainder answers zero -- which every boundary reads
        as "do not start" rather than as "wait".
        """
        from baton_v12.worker_manager.custody import allowed

        self.assertEqual(allowed(lambda: 0.1, 120), 0)
        self.assertEqual(allowed(lambda: 0.9, 120), 0)
        self.assertEqual(allowed(lambda: -3, 120), 0)
        self.assertEqual(allowed(lambda: 57.8, 120), 57)
        # NEVER MORE THAN THE CEILING, and `None` is the ceiling itself.
        self.assertEqual(allowed(lambda: 9999, 120), 120)
        self.assertEqual(allowed(None, 120), 120)
        # AND NEVER MORE THAN WHAT IS LEFT, over the whole range.
        for left in (0, 0.4, 1, 1.9, 59, 60.5, 119, 121):
            with self.subTest(left=left):
                self.assertLessEqual(allowed(lambda: left, 120), left)

    def test_a_readback_failure_keeps_the_declaration_and_says_so(self):
        """R2: the act happened; what can be said about it did not.

        A read-back that fails must leave `declared` TRUE and the settlement
        UNKNOWN -- reporting it as undeclared would deny an ending that
        really occurred, and reporting it as settled would claim one nobody
        read.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage("abandon-24")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        original = intake.abandonment_cleanup_of
        # SEVERED AFTER THE ACT, NOT DURING IT. The composition reads this
        # same public reader twice inside the operation -- as the discharge's
        # precondition and as the discharge's own proof -- so failing every
        # call would fail the ABANDONMENT, which is a different case and is
        # correctly reported as undeclared. The read-back is what
        # `_declared_one` asks once the ending has committed, so the sever is
        # armed exactly when the operation returns.
        armed = []

        def failing(*arguments, **operands):
            if armed:
                raise RuntimeError("the fixture severed the read-back")
            return original(*arguments, **operands)

        intake.abandonment_cleanup_of = failing
        self.addCleanup(setattr, intake, "abandonment_cleanup_of", original)

        class Arming:
            """`operations`, plus the moment the read-back stops working."""

            @staticmethod
            def abandon_attempt(**operands):
                answered = operations.abandon_attempt(**operands)
                armed.append(True)
                return answered

        declared = two_job_supervisor._declare_abandonment(
            Arming, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest)
        self.assertTrue(declared[attempt_id]["declared"])
        self.assertIsNone(declared[attempt_id]["cleanup"])
        self.assertFalse(declared[attempt_id]["gate_discharged"])
        self.assertIn("could not be read back", declared[attempt_id]["why"])
        # AND IT IS NOT COUNTED AS SETTLED, because settling takes both facts.
        self.assertEqual(
            two_job_supervisor._settled_by_abandonment(declared), [])
        intake.abandonment_cleanup_of = original
        # THE ENDING REALLY DID HAPPEN, which is why `declared` stays true.
        self.assertIsNotNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))

    def test_a_failure_after_the_ending_does_not_deny_the_ending(self):
        """R2: an exception is not evidence that nothing was declared.

        The call can raise AFTER the declaration and even after the cleanup
        committed -- the lost-discharge history is exactly that shape. So the
        durable state is READ rather than inferred, and the invocation failure
        is reported beside it.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage("abandon-27")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        class Raising:
            """The ending happens, and THEN the call fails."""

            @staticmethod
            def abandon_attempt(**operands):
                operations.abandon_attempt(**operands)
                raise RuntimeError("the fixture failed after the ending")

        declared = two_job_supervisor._declare_abandonment(
            Raising, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest)
        self.assertIs(declared[attempt_id]["declared"], True)
        self.assertEqual(declared[attempt_id]["cleanup"], "retained")
        self.assertTrue(declared[attempt_id]["gate_discharged"])
        self.assertIn("failed after the ending", declared[attempt_id]["why"])
        # AND IT COUNTS AS SETTLED, because the ending really did settle.
        self.assertEqual(
            two_job_supervisor._settled_by_abandonment(declared),
            [attempt_id])
        self.assertIsNotNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))

    def test_a_failure_before_the_ending_is_unknown_not_denied(self):
        """R2: and when nothing committed, the answer is UNKNOWN.

        `declared` is `None` rather than `False`: this manager did not
        establish that no declaration exists, only that it could not read one.
        Either way the attempt stays unresolved.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import intake

        held, stage = self.faulted_with_stage("abandon-28")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        del operations

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        class Refusing:
            @staticmethod
            def abandon_attempt(**operands):
                del operands
                raise RuntimeError("the fixture failed before the ending")

        before = self.effects()
        declared = two_job_supervisor._declare_abandonment(
            Refusing, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest)
        self.assertIsNone(declared[attempt_id]["declared"])
        self.assertIsNone(declared[attempt_id]["cleanup"])
        self.assertEqual(
            two_job_supervisor._settled_by_abandonment(declared), [])
        self.assertEqual(self.effects(), before)
        self.assertIsNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))

    def test_an_eligible_attempt_with_no_recorded_stage_is_unresolved(self):
        """R2: the MISSING-STAGE branch, over an attempt that really exists.

        The earlier ineligible candidates were both absent attempts, which
        never reach this branch. This one is eligible in every way and simply
        was not recorded at launch.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import intake

        held, _stage = self.faulted_with_stage("abandon-25")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        eligible, why = two_job_supervisor._abandonment_eligible(
            control, attempt_id)
        self.assertTrue(eligible, why)

        class Gate:
            launched_stage = {}

        before = self.effects()
        declared = two_job_supervisor._declare_abandonment(
            operations, control, Gate, [attempt_id],
            reason="the supervisor stopped this run", policy=digest)
        self.assertFalse(declared[attempt_id]["declared"])
        self.assertIn("no launch stage document",
                      declared[attempt_id]["why"])
        self.assertEqual(self.effects(), before)
        self.assertIsNone(intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=digest))

    def test_one_attempts_failure_does_not_discard_the_others(self):
        """R2: a partial map is kept, and later attempts still run.

        The whole declaration used to travel through one outer guard, so an
        eligibility read that raised replaced every result with nothing.
        """
        import two_job_supervisor

        held, stage = self.faulted_with_stage("abandon-26")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        stranger = "attempt-" + "8" * 64

        class Gate:
            launched_stage = {attempt_id: dict(stage)}

        original = two_job_supervisor._abandonment_eligible

        def sometimes(store, attempt):
            if attempt == stranger:
                raise RuntimeError("the fixture severed this read")
            return original(store, attempt)

        two_job_supervisor._abandonment_eligible = sometimes
        self.addCleanup(setattr, two_job_supervisor,
                        "_abandonment_eligible", original)
        declared = two_job_supervisor._declare_abandonment(
            operations, control, Gate, [stranger, attempt_id],
            reason="the supervisor stopped this run", policy=digest)
        self.assertIn("eligibility could not be read",
                      declared[stranger]["why"])
        # THE OTHER ONE STILL RAN, which is the whole point.
        self.assertTrue(declared[attempt_id]["declared"], declared)
        self.assertEqual(
            two_job_supervisor._settled_by_abandonment(declared),
            [attempt_id])

    def test_a_declared_ending_with_no_discharge_is_not_settled(self):
        """R2: `declared=True` alone is not a completed ending.

        An undischarged quiescence gate leaves the Work stopped, so the
        settled set requires the discharge as well as the positive cleanup.
        """
        import two_job_supervisor

        self.assertEqual(two_job_supervisor._settled_by_abandonment(
            {"a": {"declared": True, "cleanup": "retained",
                   "gate_discharged": False}}), [])
        self.assertEqual(two_job_supervisor._settled_by_abandonment(
            {"a": {"declared": True, "cleanup": "failed",
                   "gate_discharged": True}}), [])
        self.assertEqual(two_job_supervisor._settled_by_abandonment(
            {"a": {"declared": True, "cleanup": "retained",
                   "gate_discharged": True}}), ["a"])

    def test_an_answered_attempt_is_never_declared_abandoned(self):
        """The eligibility rule that matters most: a worker that ANSWERED.

        Declaring a completed turn abandoned would relabel somebody's result.
        The reader refuses it by name and the declaration reports that rather
        than calling it done.
        """
        import two_job_supervisor
        from baton_v12.worker_manager import intake

        held, _stage = self.faulted_with_stage("abandon-22")
        control, operations, attempt_id = held[1], held[2], held[5]
        digest = self.config["retention_policy_digest"]
        del operations, digest
        # THE FOUR DISQUALIFYING SHAPES, asked of the reader directly. The
        # receipt one is patched at its own public reader rather than by
        # forging an intake, which would be composing somebody else's record.
        eligible, why = two_job_supervisor._abandonment_eligible(
            control, attempt_id)
        self.assertTrue(eligible, why)
        original = intake.intake_receipt_of
        intake.intake_receipt_of = lambda store, attempt: {"receipt": "held"}
        self.addCleanup(setattr, intake, "intake_receipt_of", original)
        eligible, why = two_job_supervisor._abandonment_eligible(
            control, attempt_id)
        self.assertFalse(eligible)
        self.assertIn("the worker answered", why)

    def test_a_malformed_stage_refuses_without_crashing(self):
        """A refusal that raises AttributeError is not a refusal."""
        from baton_v12.contracts import ContractRefusal
        held, _stage = self.faulted_with_stage("abandon-3")
        operations, attempt_id = held[2], held[5]
        for malformed in ("a string", ["a", "list"], 7, None):
            with self.subTest(stage=type(malformed).__name__):
                with self.assertRaises(ContractRefusal):
                    operations.abandon_attempt(
                        attempt_id=attempt_id, reason=self.REASON,
                        stage=malformed)

    def test_a_stage_naming_another_attempt_is_refused(self):
        from baton_v12.contracts import ContractRefusal
        held, stage = self.faulted_with_stage("abandon-4")
        operations, attempt_id = held[2], held[5]
        with self.assertRaises(ContractRefusal):
            operations.abandon_attempt(
                attempt_id=attempt_id, reason=self.REASON,
                stage=dict(stage, attempt_id="attempt-" + "0" * 64))

    def test_a_blank_reason_is_a_declaration_nobody_made(self):
        from baton_v12.contracts import ContractRefusal
        held, stage = self.faulted_with_stage("abandon-5")
        operations, attempt_id = held[2], held[5]
        with self.assertRaises(ContractRefusal):
            operations.abandon_attempt(attempt_id=attempt_id, reason="   ",
                                       stage=stage)


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only this module's own cases.

    The fixture is an accepted product case; loading it normally would re-run
    W85500's evidence under this dossier's name.
    """
    suite = unittest.TestSuite()
    for name in loader.getTestCaseNames(TheComposedAbandonmentIsCalled):
        if name in TheComposedAbandonmentIsCalled.__dict__:
            suite.addTest(TheComposedAbandonmentIsCalled(name))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
