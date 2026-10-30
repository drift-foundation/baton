"""W333486 -- the typed cessation records, their readers, and the composed cause.

WHAT THIS MODULE COVERS, and it is a BOUNDED FIRST SLICE whose limits are
stated here rather than left to be discovered: the two durable records and
their public readers, the replay-honest `effects` vocabulary, the separation
of a known typed failure from an unknown cessation, the collision discipline,
the composed cause's explicit `unknown` branch naming which records are
absent, and the secret canary on the recording path.

WHAT IT DOES NOT COVER YET, stated plainly: the end-to-end reclaim-to-
settlement composition and the cancellation fence sequence driven through the
production composition with restart cuts at every external-effect boundary.
Those need a real adapter, a governed workspace token and a settlement
handoff, and they are the next milestone rather than a thing this module
quietly claims.
"""

import os
import sqlite3
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import documents, failure_cause

from .test_attempts import (ADAPTER, ATTEMPT, NOW, Adapter, Agent,
                            AttemptCase, ControlStore, activate_assignment,
                            request_cancellation, request_runtime_start)

SECRET = "canary-" + "s" * 32


class TheVocabularyIsClosedAndTheTwoAXESDoNotCollapse(unittest.TestCase):
    """A known typed stop failure is NOT an unknown, and `absent` is not `quiescent`."""

    def test_every_outcome_maps_to_a_declared_cessation(self):
        for outcome, cessation in failure_cause.OUTCOMES.items():
            self.assertIn(cessation, failure_cause.CESSATION, outcome)

    def test_absent_and_quiescent_are_DIFFERENT_facts(self):
        # A quiescent container still exists and still holds its mounts, so
        # the two outcomes may not share a cessation value.
        self.assertEqual(failure_cause.OUTCOMES["ceased-absent"], "absent")
        self.assertEqual(failure_cause.OUTCOMES["ceased-quiescent"],
                         "quiescent")

    def test_a_KNOWN_typed_failure_still_leaves_cessation_UNKNOWN(self):
        for outcome in ("stop-failed", "engine-unavailable", "engine-timeout",
                        "lost-reply", "uncertain-observation",
                        "identity-mismatch", "fenced-not-ordered",
                        "no-identity-resolved", "ordered"):
            self.assertEqual(failure_cause.OUTCOMES[outcome], "unknown",
                             outcome)

    def test_the_HELD_outcome_carries_BOTH_facts_without_choosing(self):
        # (c) the token-bound runtime ceased and the attempt's own attachment
        # is unresolved. Neither half may be dropped.
        self.assertEqual(failure_cause.OUTCOMES["held-attachment-unresolved"],
                         "quiescent-or-absent")

    def test_an_UNDECLARED_outcome_or_component_or_effect_is_REFUSED(self):
        for call, operand in ((failure_cause._outcome, "stopped"),
                              (failure_cause._component, "sweeper"),
                              (failure_cause._effects, ("delete",))):
            with self.assertRaises(ContractRefusal):
                call(operand)


class TheRecordsAndTheirReaders(AttemptCase):

    def setUp(self):
        super().setUp()
        self.recorded()

    def intent(self, **spoiled):
        operands = {"component": "expiry-reclaim", "generation": None,
                    "domain": "workspace:7:9", "launched": True,
                    "runtime_id": "container-1",
                    "correlation_id": "resource.reclaim:abc"}
        operands.update(spoiled)
        return failure_cause.record_and_raise_cessation_intent(
            self.store, ATTEMPT, **operands)

    def outcome(self, **spoiled):
        operands = {"component": "expiry-reclaim", "generation": None,
                    "runtime_id": "container-1",
                    "correlation_id": "resource.reclaim:abc",
                    "effects": ("revoke", "stop", "remove"),
                    "outcome": "ceased-absent"}
        operands.update(spoiled)
        return failure_cause.record_and_raise_cessation_outcome(
            self.store, ATTEMPT, **operands)

    def test_an_INTENT_reads_back_under_its_own_identity(self):
        operation_id, document = self.intent()
        found = failure_cause.attempt_cessation_intent_of(
            self.store, ATTEMPT, "expiry-reclaim")
        self.assertEqual(found["operation_id"], operation_id)
        self.assertEqual(found["runtime_id"], "container-1")
        self.assertEqual(found["correlation_id"], document["correlation_id"])
        self.assertEqual(set(document),
                         set(documents.ATTEMPT_CESSATION_INTENT))

    def test_an_INTENT_IS_NOT_A_STOP_and_the_outcome_is_still_ABSENT(self):
        self.intent()
        self.assertIsNone(failure_cause.attempt_cessation_outcome_of(
            self.store, ATTEMPT, "expiry-reclaim"))
        composed = failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)
        # W341357: READ THROUGH THE PUBLISHED SHAPE. The recovered assertions
        # named `outcome_state` and compared bare scalars, which is the shape
        # the rejected candidate had; the producer this slice publishes wraps
        # EVERY leaf and names the member `outcome`. The claim is unchanged
        # and is now made through the decoder the parent will use, so a
        # recorded known value cannot be read back as unknown.
        self.assertEqual(failure_cause.answer_of(composed), "intent-only")
        self.assertEqual(failure_cause.decode(composed["cause"]["outcome"]),
                         (True, "ordered-without-outcome"))
        self.assertEqual(failure_cause.decode(composed["cause"]["cessation"]),
                         (True, "unknown"))

    def test_ABSENCE_is_the_ordinary_answer_for_both_readers(self):
        for read in (failure_cause.attempt_cessation_intent_of,
                     failure_cause.attempt_cessation_outcome_of):
            self.assertIsNone(read(self.store, ATTEMPT, "cancellation"))
            self.assertIsNone(read(self.store, "attempt-nobody", "settlement"))

    def test_a_MALFORMED_attempt_id_is_a_REFUSAL_and_not_an_absence(self):
        with self.assertRaises(ContractRefusal):
            failure_cause.attempt_cessation_intent_of(self.store, "",
                                                      "expiry-reclaim")

    def test_an_UNDECLARED_component_is_refused_at_the_reader_too(self):
        with self.assertRaises(ContractRefusal):
            failure_cause.attempt_cessation_outcome_of(self.store, ATTEMPT,
                                                       "sweeper")

    def test_an_EXACT_replay_returns_the_FIRST_account(self):
        first, document = self.outcome()
        again, replayed = self.outcome()
        self.assertEqual(first, again)
        self.assertEqual(document, replayed)

    def test_an_UNCERTAIN_observation_is_SUPERSEDED_by_a_later_POSITIVE_one(self):
        """review340349 item 3, and the defect it names exactly.

        Outcome identity is fixed by attempt/assignment/start/component/
        generation, so the rejected candidate retained the UNCERTAIN account
        forever and the later positive observation was swallowed as a
        collision. A historical uncertainty must not be an enduring
        substitute for better later evidence.
        """
        first, _held = self.outcome(outcome="uncertain-observation")
        later, placed = self.outcome(outcome="ceased-absent")
        self.assertNotEqual(first, later)
        # THE TIP IS CURRENT...
        found = failure_cause.attempt_cessation_outcome_of(
            self.store, ATTEMPT, "expiry-reclaim")
        self.assertEqual(found["outcome"], "ceased-absent")
        self.assertEqual(found["cessation"], "absent")
        self.assertEqual(found["revision"], 1)
        # ...AND BOTH ARE KEPT, with the chain saying which it replaced.
        self.assertEqual(placed["supersedes"], first)
        self.assertEqual(len(found["superseded"]), 1)
        self.assertEqual(found["superseded"][0]["outcome"],
                         "uncertain-observation")
        self.assertEqual(found["superseded"][0]["revision"], 0)

    def test_a_REPLAY_of_a_SUPERSEDED_revision_writes_NOTHING_MORE(self):
        """An exact replay is an exact replay wherever in the chain it sits.

        Comparing only the TIP would append a third revision every time the
        reclaim replayed its first, uncertain pass -- so the whole chain is
        compared and the account already held is returned.
        """
        first, _one = self.outcome(outcome="uncertain-observation")
        self.outcome(outcome="ceased-absent")
        again, replayed = self.outcome(outcome="uncertain-observation")
        self.assertEqual(again, first)
        self.assertEqual(replayed["revision"], 0)
        # AND THE TIP IS STILL THE POSITIVE ONE: a replay of the older
        # account does not make it current again.
        found = failure_cause.attempt_cessation_outcome_of(
            self.store, ATTEMPT, "expiry-reclaim")
        self.assertEqual(found["outcome"], "ceased-absent")
        self.assertEqual(len(found["superseded"]), 1)

    def test_the_CHAIN_IS_BOUNDED_and_REFUSES_rather_than_dropping_evidence(self):
        """A bound keeps the reader bounded; it does not discard the newer fact."""
        outcomes = ["uncertain-observation", "ceased-absent",
                    "ceased-quiescent", "lost-reply", "ordered",
                    "stop-failed", "engine-timeout", "engine-unavailable",
                    "identity-mismatch", "no-identity-resolved",
                    "fenced-not-ordered", "held-attachment-unresolved"]
        placed = 0
        for one in outcomes:
            if placed >= failure_cause.OUTCOME_REVISIONS:
                break
            self.outcome(outcome=one)
            placed += 1
        self.assertLessEqual(placed, failure_cause.OUTCOME_REVISIONS)
        # The bound is a REFUSAL, proved by asking for one revision past it.
        from baton_v12.worker_manager import attempts as _attempts

        row = _attempts._require_attempt(self.store, ATTEMPT)
        with self.assertRaises(ContractRefusal):
            failure_cause.cessation_outcome_operation_id(
                row, "expiry-reclaim", None,
                failure_cause.OUTCOME_REVISIONS)
        # ...and a negative or non-integer revision is refused the same way.
        for bad in (-1, True, "0", None):
            with self.assertRaises(ContractRefusal):
                failure_cause.cessation_outcome_operation_id(
                    row, "expiry-reclaim", None, bad)

    def test_the_NEVER_RAISING_recorder_still_NEVER_RAISES(self):
        """And its answer names the record, degraded or not.

        `recording_degraded` is the one place a caller decides whether a
        record reached disk, so the ordinary answer must NOT be marked.
        """
        said = failure_cause.record_cessation_outcome(
            self.store, ATTEMPT, component="expiry-reclaim", generation=None,
            runtime_id="container-1", correlation_id="resource.reclaim:abc",
            effects=(), outcome="ceased-quiescent")
        self.assertIn("journalled as", said)
        self.assertFalse(failure_cause.recording_degraded(said))

    def test_the_RECORDER_NEVER_RAISES_even_on_an_undeclared_outcome(self):
        said = failure_cause.record_cessation_outcome(
            self.store, ATTEMPT, component="expiry-reclaim", generation=None,
            runtime_id="container-1", correlation_id="x", effects=(),
            outcome="stopped")
        self.assertIn("could not be recorded", said)

    def test_the_THREE_REPLAY_EFFECT_SHAPES_are_distinguishable(self):
        # (b) `before == "absent"` orders NEITHER; `before == "quiescent"`
        # skips the stop and STILL REMOVES; anything else does both. The
        # record must not read a pass that ordered nothing as one that
        # ordered a stop.
        shapes = {"expiry-reclaim": ("revoke",),
                  "settlement": ("revoke", "remove"),
                  "cancellation": ("revoke", "stop", "remove")}
        for component, effects in shapes.items():
            failure_cause.record_and_raise_cessation_outcome(
                self.store, ATTEMPT, component=component, generation=None,
                runtime_id="container-1", correlation_id="c-" + component,
                effects=effects, outcome="ceased-absent")
        for component, effects in shapes.items():
            found = failure_cause.attempt_cessation_outcome_of(
                self.store, ATTEMPT, component)
            self.assertEqual(tuple(found["effects"]), effects, component)

    def test_NO_MESSAGE_reaches_the_record_and_a_SECRET_cannot_ride_one(self):
        # A refusal's prose can quote adapter stderr. The record carries the
        # TYPED PAIR and nothing else, so there is no member for a secret to
        # travel in -- proved by the member set rather than by scanning text.
        _id, document = self.outcome(outcome="stop-failed",
                                     category="refused", code="precondition")
        self.assertEqual(set(document),
                         set(documents.ATTEMPT_CESSATION_OUTCOME))
        self.assertNotIn(SECRET, repr(document))
        self.assertEqual(document["cessation"], "unknown")
        self.assertEqual(document["outcome"], "stop-failed")

    def test_the_OUTCOME_document_has_NO_member_a_message_could_ride(self):
        # The canary cannot reach the record because there is nowhere in the
        # closed member set for prose to go: every member is an identity, a
        # typed token or a closed list of effect names.
        prose = [name for name in documents.ATTEMPT_CESSATION_OUTCOME
                 if name in ("why", "message", "detail", "stderr", "failure")]
        self.assertEqual(prose, [])
        _id, document = self.outcome(outcome="engine-unavailable")
        self.assertNotIn(SECRET, repr(document))


class TheDURABLEINTENTAUTHORIZESTHEEFFECTORNOEFFECTISORDERED(AttemptCase):
    """W341357 item 1: a COLLISION IS NOT AUTHORIZATION.

    `store.transact` replays an exact match through its SUCCESS path, so a
    `refused/operation-collision` out of the intent recorder can mean only one
    thing: a durable intent for this act exists and IT DESCRIBES DIFFERENT
    OPERANDS. The recovered `ensure_cessation_intent` read that refusal as
    proof an intent existed and as permission to order the effect, which is
    backwards in the one case where the durable record provably does not
    describe the effect about to be ordered.

    These two cases are deliberately SEPARATE acceptance evidence, because an
    exact replay and a changed-signature collision are different facts and one
    case cannot stand for both.
    """

    def setUp(self):
        super().setUp()
        self.recorded()
        self.ordered = []

    def guarded(self, **spoiled):
        """The call-site contract, exactly as the three boundaries spell it.

        `ensure_cessation_intent` is called, and the effect is ordered on the
        next line. If the intent is not durable FOR THIS EFFECT, nothing may
        be appended to `self.ordered`.
        """
        operands = {"component": "expiry-reclaim", "generation": None,
                    "domain": "workspace:7:9", "launched": True,
                    "runtime_id": "container-1",
                    "correlation_id": "resource.reclaim:abc"}
        operands.update(spoiled)
        reported = failure_cause.ensure_cessation_intent(
            self.store, ATTEMPT, **operands)
        self.ordered.append("effect")
        return reported

    def test_an_EXACT_REPLAY_authorizes_the_effect_and_writes_nothing_new(self):
        """The first of the two, and it must keep working.

        An exact replay never reaches the collision guard at all -- `replay`
        returns the recorded value -- so the second pass is authorized and the
        record is the same one.
        """
        first = self.guarded()
        again = self.guarded()
        self.assertEqual(self.ordered, ["effect", "effect"])
        self.assertFalse(failure_cause.recording_degraded(first))
        self.assertFalse(failure_cause.recording_degraded(again))
        self.assertEqual(first, again)
        found = failure_cause.attempt_cessation_intent_of(
            self.store, ATTEMPT, "expiry-reclaim")
        self.assertEqual(found["runtime_id"], "container-1")
        self.assertEqual(found["correlation_id"], "resource.reclaim:abc")

    def test_a_CONFLICTING_RUNTIME_is_NOT_authorization_and_NO_EFFECT_is_ordered(self):
        """The second of the two, and it is the defect.

        Same attempt, same fixed assignment, same start operation, same
        component and same generation -- so the SAME operation id -- and a
        DIFFERENT token-bound runtime, which rides the signature because
        `_identity` deliberately keeps the runtime out of the id.
        """
        self.guarded()
        self.assertEqual(self.ordered, ["effect"])
        with self.assertRaises(ContractRefusal) as refused:
            self.guarded(runtime_id="container-2")
        # NO SECOND EFFECT. This is the whole claim.
        self.assertEqual(self.ordered, ["effect"])
        self.assertEqual((refused.exception.category, refused.exception.code),
                         ("refused", "operation-collision"))
        # AND THE READER CAN SEE WHICH FACTS WERE COMPARED.
        self.assertIn("runtime_id", refused.exception.message)
        self.assertIn("container-1", refused.exception.message)
        self.assertIn("container-2", refused.exception.message)
        # THE FIRST ACCOUNT STILL STANDS, unrewritten.
        found = failure_cause.attempt_cessation_intent_of(
            self.store, ATTEMPT, "expiry-reclaim")
        self.assertEqual(found["runtime_id"], "container-1")

    def test_a_CONFLICTING_CORRELATION_is_refused_the_same_way(self):
        """The other half of the signature, proved separately from the runtime.

        A different correlation id is a different act under the same identity,
        and the engine is about to be handed THIS one. Authorizing it on the
        strength of a record naming another would attribute the effect to the
        wrong operation.
        """
        self.guarded()
        with self.assertRaises(ContractRefusal) as refused:
            self.guarded(correlation_id="resource.reclaim:xyz")
        self.assertEqual(self.ordered, ["effect"])
        self.assertIn("correlation_id", refused.exception.message)

    def test_a_CONFLICTING_LAUNCHED_FACT_is_refused_too(self):
        """`launched` distinguishes "nothing to stop" from "a writer I cannot name"."""
        self.guarded(runtime_id=None, launched=False)
        with self.assertRaises(ContractRefusal):
            self.guarded(runtime_id=None, launched=True)
        self.assertEqual(self.ordered, ["effect"])

    def test_NOTHING_DURABLE_means_NO_EFFECT(self):
        """The shape the recovered bytes already had, proved at the call site.

        A journal that cannot record raises, the refusal propagates, and the
        effect is not ordered. A reportable degradation would not do: the
        caller appends the effect on the next line.
        """
        def refusing(*operands, **named):
            raise ContractRefusal("unavailable", "transport",
                                  "the journal is unreachable")

        self.store.transact = refusing
        with self.assertRaises(ContractRefusal) as refused:
            self.guarded()
        self.assertEqual(self.ordered, [])
        self.assertEqual(refused.exception.code, "transport")

    def test_a_BUILD_DEFECT_is_reported_as_one_and_not_as_a_collision(self):
        with self.assertRaises(ContractRefusal) as refused:
            self.guarded(component="sweeper")
        self.assertEqual(self.ordered, [])
        self.assertEqual(refused.exception.code, "schema")


class TheComposedCause(AttemptCase):

    def setUp(self):
        super().setUp()
        self.recorded()

    def test_an_UNKNOWN_historical_attempt_NAMES_the_absent_records(self):
        composed = failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)
        self.assertIsNone(composed["cause"])
        self.assertIsNotNone(composed["unknown"])
        named = composed["unknown"]["absent"]
        for component in failure_cause.COMPONENTS:
            self.assertIn("attempt.cessation-*:" + component, named)
        self.assertIn("runtime.start-failed", named)
        self.assertIn("runtime.preparation-failed", named)

    def test_an_ABSENT_attempt_is_an_ABSENCE_and_a_bad_id_is_a_REFUSAL(self):
        self.assertIsNone(failure_cause.attempt_failure_cause_of(
            self.store, "attempt-nobody"))
        with self.assertRaises(ContractRefusal):
            failure_cause.attempt_failure_cause_of(self.store, "")

    def test_every_member_is_KNOWN_WITH_A_SOURCE_or_UNKNOWN_WITH_A_REASON(self):
        composed = failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)
        # W341357: the published member names. `token` is an AXIS of wrapped
        # members rather than one leaf, so it is walked member by member --
        # the recovered assertion indexed it as a leaf and the two failure
        # members under their recovered names (`start_failure`,
        # `preparation_failure`) are published as `*_recorded`.
        for name in ("revocation", "completion", "domain", "generation",
                     "start_failure_recorded", "preparation_failure_recorded",
                     "revoked_expired_at", "revoked_container",
                     "revoked_owner", "start_failure_runtime_id",
                     "preparation_failure_runtime_id", "renewal_limit",
                     "lifetime_seconds"):
            known, value = failure_cause.decode(composed[name])
            if not known:
                self.assertIsNone(value, name)
                self.assertTrue(composed[name]["why"], name)
            else:
                self.assertTrue(composed[name]["source"], name)
        for name, member in composed["token"].items():
            failure_cause.decode(member)
        for name, member in composed["execution"].items():
            failure_cause.decode(member)

    def test_a_MISSING_count_is_never_a_ZERO(self):
        composed = failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)
        activity = composed["execution"]["activity_bytes"]
        self.assertFalse(activity["known"])
        self.assertIsNone(activity["value"])
        self.assertIn("observed", activity["why"])

    def test_DEVICE_AND_INODE_are_an_object_identity_and_NOT_a_locator(self):
        composed = failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)
        self.assertIs(composed["workspace_object"]["is_a_locator"], False)
        self.assertIn("not a path", composed["workspace_object"]["why"])

    def test_an_ESTABLISHED_cessation_is_preferred_over_an_UNKNOWN_one(self):
        failure_cause.record_and_raise_cessation_outcome(
            self.store, ATTEMPT, component="cancellation", generation=None,
            runtime_id=None, correlation_id="cancel-1", effects=(),
            outcome="fenced-not-ordered")
        failure_cause.record_and_raise_cessation_outcome(
            self.store, ATTEMPT, component="expiry-reclaim", generation=None,
            runtime_id="container-1", correlation_id="reclaim-1",
            effects=("revoke", "stop", "remove"), outcome="ceased-absent")
        composed = failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)
        self.assertEqual(failure_cause.decode(composed["cause"]["component"]),
                         (True, "expiry-reclaim"))
        self.assertEqual(failure_cause.decode(composed["cause"]["cessation"]),
                         (True, "absent"))
        self.assertEqual(failure_cause.answer_of(composed), "ceased")
        self.assertIsNone(composed["unknown"])

    def test_a_DIAGNOSTIC_CAUSE_decides_no_stage_and_accepts_nothing(self):
        # The composed answer has no acceptance member and no stage member to
        # branch on: a diagnostic cause is not candidate acceptance.
        composed = failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)
        self.assertNotIn("accepted", composed)
        self.assertNotIn("state", composed)
        self.assertNotIn("stage", composed)


if __name__ == "__main__":
    unittest.main()


class ARecordingFailureOBSERVABLYPREVENTSTHEEFFECT(AttemptCase):
    """W341357 item 2, at the boundaries where the effects are ACTUALLY ordered.

    The claim is not that a degradation is reported. It is that the effect is
    NOT ORDERED. `attempts._order_quiescence` calls `agent.cancel` and
    `adapter.stop` on the lines after the intent, and
    `intake.reclaim_expired_resource` calls `govern.revoke` on the line after
    its own -- so a journal that cannot record the intent must leave both
    boundaries uncrossed, and these cases watch the boundaries rather than the
    answer document.

    A REPORTABLE DEGRADATION IS NOT A SUBSTITUTE, which is why every case here
    asserts on a call log of the injected boundary.
    """

    class Died(BaseException):
        """A CRASH IS NOT A REFUSAL, so it is not a `ContractRefusal`.

        It also inherits `BaseException` rather than `Exception` so that no
        `except Exception` anywhere on these paths can turn the manager's
        death into a handled outcome -- which would make the case about error
        handling instead of about a process that stopped existing.
        """

    def crash_after_the_intent(self):
        """The manager ceases to exist BETWEEN the intent and the effect.

        Injected exactly at that seam -- the intent commits, and nothing after
        it runs. `attempts` and `intake` both reach `failure_cause` through
        the module object, so replacing the attribute puts the death precisely
        where the crash this record exists for would happen.
        """
        whole = failure_cause.ensure_cessation_intent

        def dying(*operands, **facts):
            whole(*operands, **facts)
            raise self.Died("the manager stopped existing between the durable "
                            "intent and the effect it authorized")

        failure_cause.ensure_cessation_intent = dying
        self.addCleanup(setattr, failure_cause, "ensure_cessation_intent",
                        whole)

    def refuse_intent(self):
        """A journal that records everything EXCEPT a cessation intent.

        Narrow on purpose: a store that refused every act would stop the path
        for a reason that is not the one under test, and the claim would not
        be about the intent at all.
        """
        whole = self.store.transact

        def selective(operation_id, kind, signature, action):
            if kind == "attempt.cessation-intent":
                raise ContractRefusal("unavailable", "transport",
                                      "the journal is unreachable")
            return whole(operation_id, kind, signature, action)

        self.store.transact = selective

    # -- cancellation --------------------------------------------------------

    def attached(self, attempt_id=ATTEMPT):
        """The production cancellation fixture, as `test_attempts` builds it."""
        self.claimed(attempt_id=attempt_id)
        activate_assignment(self.store, self.port, attempt_id=attempt_id,
                            expect=self.expect())
        self.adapter = Adapter()
        request_runtime_start(self.store, self.adapter, attempt_id=attempt_id)
        return attempt_id

    def watched(self):
        """`agent.cancel` and `adapter.stop` with a shared call log."""
        ordered = []
        agent = Agent()
        agent.cancel = lambda operands: ordered.append("agent-cancel")
        self.adapter.stop = lambda operands: ordered.append("stop")
        return agent, ordered

    def test_CANCELLATION_orders_NEITHER_boundary_when_the_intent_is_not_durable(self):
        self.attached()
        agent, ordered = self.watched()
        self.refuse_intent()
        with self.assertRaises(ContractRefusal) as refused:
            request_cancellation(self.store, self.port, agent, self.adapter,
                                 attempt_id=ATTEMPT)
        self.assertEqual(ordered, [])
        self.assertEqual(refused.exception.code, "transport")

    def test_CANCELLATION_DOES_order_both_boundaries_when_the_intent_IS_durable(self):
        """The other half, so the case above is about the intent and nothing else."""
        self.attached()
        agent, ordered = self.watched()
        request_cancellation(self.store, self.port, agent, self.adapter,
                             attempt_id=ATTEMPT)
        self.assertEqual(ordered, ["agent-cancel", "stop"])
        found = failure_cause.attempt_cessation_intent_of(
            self.store, ATTEMPT, "cancellation")
        self.assertIsNotNone(found)

    def test_CANCELLATIONS_FENCE_IS_STILL_TAKEN_and_the_runtime_is_NOT_ordered_stopped(self):
        """The refusal weakens no fencing, proved rather than asserted.

        `request_cancellation` fences the exact assignment at the Authority
        BEFORE it reaches `_order_quiescence`, so a refusal here leaves the
        assignment FENCED with its runtime not ordered stopped -- which is the
        typed `fenced-not-ordered` state this manager already describes, not
        an invented one.
        """
        self.attached()
        agent, ordered = self.watched()
        self.refuse_intent()
        with self.assertRaises(ContractRefusal):
            request_cancellation(self.store, self.port, agent, self.adapter,
                                 attempt_id=ATTEMPT)
        self.assertEqual(ordered, [])
        # THE FENCE HAPPENED: the Authority session holds this assignment's
        # fence for this exact generation.
        fenced = [one for one in self.session.calls if one[0] == "cancel"]
        self.assertTrue(fenced, self.session.calls)
        # AND IT FENCED THIS EXACT ASSIGNMENT GENERATION.
        self.assertEqual(fenced[0][1]["expect"], self.expect())

    def test_a_CRASH_between_the_INTENT_and_the_EFFECT_leaves_INTENT_ONLY(self):
        """The crash case the intent exists for, on the cancellation boundary.

        The intent commits, the process dies before either boundary answers,
        and a later reader must say THIS MANAGER ORDERED THIS CONTAINER
        STOPPED AND NO OUTCOME WAS RECORDED -- not `unknown`, and not a stop.
        """
        self.attached()
        agent, ordered = self.watched()
        self.crash_after_the_intent()
        with self.assertRaises(self.Died):
            request_cancellation(self.store, self.port, agent, self.adapter,
                                 attempt_id=ATTEMPT)
        # NEITHER BOUNDARY WAS REACHED, which is what makes this the crash
        # the intent exists for rather than a failed effect.
        self.assertEqual(ordered, [])
        # THE INTENT IS DURABLE...
        intent = failure_cause.attempt_cessation_intent_of(
            self.store, ATTEMPT, "cancellation")
        self.assertIsNotNone(intent)
        # ...AND NO OUTCOME WAS EVER RECORDED.
        self.assertIsNone(failure_cause.attempt_cessation_outcome_of(
            self.store, ATTEMPT, "cancellation"))
        composed = failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)
        self.assertEqual(failure_cause.answer_of(composed), "intent-only")
        self.assertEqual(
            failure_cause.decode(composed["cause"]["cessation"]),
            (True, "unknown"))
        # AND IT IS NOT A STOP: nothing here says the runtime ceased.
        self.assertNotEqual(failure_cause.answer_of(composed), "ceased")

    # -- reclaim -------------------------------------------------------------

    def governed(self, calls):
        """The reclaim's INJECTED resource governance, with a call log.

        `govern` is the production injection point -- `tools/job_manager.py`
        hands in `tokens.workspace_governance()` -- so watching it is watching
        the boundary rather than a stand-in for it.
        """
        from types import SimpleNamespace

        return SimpleNamespace(
            resource_kind="workspace",
            identity=lambda attempt: "7:9",
            # The generation is `None` because this fixture's attempt names
            # no workspace OBJECT, so `token_bound_runtime` resolves none --
            # and the writer and the reader must agree on the identity's
            # operands or the reader is answering about another act. The
            # token-bound-before-attachment claim is unaffected and is made
            # below: the record names the bound container while the attempt
            # row's own `runtime_id` is still `None`.
            overdue=lambda store, attempt, operation: {
                "generation": None, "domain": "workspace:7:9",
                "container": "container-1", "launch": {"at": "x"},
                "expired": True, "returned": False, "revoked": False},
            revoke=lambda store, attempt, operation: calls.append("revoke"),
            release=lambda store, attempt, operation, cessation, reclaiming:
                calls.append("release"))

    def replayed(self, calls, state):
        """A RECLAIM THAT IS REPLAYING, which is the only pass that observes first.

        `before` is read exactly when `overdue["revoked"]` is true -- a first
        pass has nothing to replay -- so the two effect shapes below are
        reachable only on a replay, which is precisely the case `effects`
        exists to describe honestly.
        """
        govern = self.governed(calls)
        govern.overdue = lambda store, attempt, operation: {
            "generation": None, "domain": "workspace:7:9",
            "container": "container-1", "launch": {"at": "x"},
            "expired": True, "returned": False, "revoked": True}
        return govern, self.reclaim_adapter(calls, before=state)

    def reclaim_adapter(self, calls, before="running"):
        from types import SimpleNamespace

        return SimpleNamespace(
            stop_expired=lambda operands: calls.append("stop"),
            remove=lambda operands: calls.append("remove"),
            observe=lambda operands: {"state": before, "why": "fixture"})

    def test_RECLAIM_does_not_WITHDRAW_the_entitlement_when_the_intent_fails(self):
        """`revoke` IS an effect, and it is the FIRST one on this path.

        `failure_cause.EFFECTS` names it, so recording after it would leave
        the same gap one step earlier. The intent is therefore ordered before
        the withdrawal, and a journal that cannot record it leaves the
        entitlement intact.
        """
        from baton_v12.worker_manager import intake

        self.recorded()
        calls = []
        self.refuse_intent()
        with self.assertRaises(ContractRefusal) as refused:
            intake.reclaim_expired_resource(
                self.store, self.reclaim_adapter(calls),
                attempt_id=ATTEMPT, govern=self.governed(calls))
        self.assertEqual(calls, [])
        self.assertEqual(refused.exception.code, "transport")

    def test_RECLAIM_DOES_withdraw_and_stop_when_the_intent_IS_durable(self):
        from baton_v12.worker_manager import intake

        self.recorded()
        calls = []
        answer = intake.reclaim_expired_resource(
            self.store, self.reclaim_adapter(calls), attempt_id=ATTEMPT,
            govern=self.governed(calls))
        self.assertEqual(calls[:2], ["revoke", "stop"])
        self.assertEqual(answer["attempt_id"], ATTEMPT)
        intent = failure_cause.attempt_cessation_intent_of(
            self.store, ATTEMPT, "expiry-reclaim")
        self.assertIsNotNone(intent)
        # TOKEN-BOUND-BEFORE-ATTACHMENT: the attempt row carries no runtime
        # and the record names the container the generation bound.
        self.assertIsNone(self.row()["runtime_id"])
        self.assertEqual(intent["runtime_id"], "container-1")

    def test_RECLAIMS_OWN_RELEASE_PATH_is_guarded_the_same_way(self):
        """The no-identity branch: its only effect is the withdrawal, and the
        intent precedes it there too."""
        from types import SimpleNamespace

        from baton_v12.worker_manager import intake

        self.recorded()
        calls = []
        govern = self.governed(calls)
        govern.overdue = lambda store, attempt, operation: {
            "generation": None, "domain": "workspace:7:9", "container": None,
            "launch": {"at": "x"}, "expired": True, "returned": False,
            "revoked": False}
        self.refuse_intent()
        with self.assertRaises(ContractRefusal):
            intake.reclaim_expired_resource(
                self.store, self.reclaim_adapter(calls), attempt_id=ATTEMPT,
                govern=govern)
        self.assertEqual(calls, [])
        # AND WITH A WORKING JOURNAL the withdrawal happens and the typed
        # outcome says no identity resolved -- which is NOT a cessation.
        del self.store.transact
        answer = intake.reclaim_expired_resource(
            self.store, self.reclaim_adapter(calls), attempt_id=ATTEMPT,
            govern=govern)
        self.assertEqual(calls, ["revoke"])
        self.assertEqual(answer["reclaimed"], "held")
        found = failure_cause.attempt_cessation_outcome_of(
            self.store, ATTEMPT, "expiry-reclaim")
        self.assertEqual(found["outcome"], "no-identity-resolved")
        self.assertEqual(found["cessation"], "unknown")

    def test_a_CRASH_between_the_RECLAIM_intent_and_its_withdrawal_leaves_INTENT_ONLY(self):
        from baton_v12.worker_manager import intake

        self.recorded()
        calls = []
        govern = self.governed(calls)
        self.crash_after_the_intent()
        with self.assertRaises(self.Died):
            intake.reclaim_expired_resource(
                self.store, self.reclaim_adapter(calls), attempt_id=ATTEMPT,
                govern=govern)
        self.assertEqual(calls, [])
        self.assertIsNotNone(failure_cause.attempt_cessation_intent_of(
            self.store, ATTEMPT, "expiry-reclaim"))
        self.assertIsNone(failure_cause.attempt_cessation_outcome_of(
            self.store, ATTEMPT, "expiry-reclaim"))
        composed = failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)
        self.assertEqual(failure_cause.answer_of(composed), "intent-only")

    def test_A_REPLAYED_RECLAIM_that_observes_an_EXACT_ABSENCE_orders_NOTHING(self):
        """`effects` names what THIS pass ordered -- and `()` is a KNOWN empty.

        `before == "absent"` skips the stop AND the removal; `quiescent` skips
        the stop and STILL REMOVES. Two different tests, and the record must
        not read a pass that ordered nothing as one that ordered a stop.
        """
        from baton_v12.worker_manager import intake

        self.recorded()
        calls = []
        govern, adapter = self.replayed(calls, "absent")
        intake.reclaim_expired_resource(
            self.store, adapter, attempt_id=ATTEMPT, govern=govern)
        self.assertEqual(calls, ["revoke"])
        found = failure_cause.attempt_cessation_outcome_of(
            self.store, ATTEMPT, "expiry-reclaim")
        self.assertEqual(tuple(found["effects"]), ("revoke",))

    def test_a_QUIESCENT_observation_SKIPS_THE_STOP_AND_STILL_REMOVES(self):
        from baton_v12.worker_manager import intake

        self.recorded()
        calls = []
        govern, adapter = self.replayed(calls, "quiescent")
        intake.reclaim_expired_resource(
            self.store, adapter, attempt_id=ATTEMPT, govern=govern)
        self.assertEqual(calls, ["revoke", "remove"])
        found = failure_cause.attempt_cessation_outcome_of(
            self.store, ATTEMPT, "expiry-reclaim")
        self.assertEqual(tuple(found["effects"]), ("revoke", "remove"))
        # AND IT IS THE TWO-FACT OUTCOME, not a collapsed one. This fixture's
        # attempt row carries no runtime, so the bound container's cessation
        # is established while the attempt's own attachment is NOT -- which is
        # the token-bound-before-attachment case, and the outcome names both
        # halves instead of choosing one.
        self.assertEqual(found["outcome"], "held-attachment-unresolved")
        self.assertEqual(found["cessation"], "quiescent-or-absent")
        self.assertNotEqual(found["cessation"], "absent")
        self.assertEqual(found["runtime_id"], "container-1")
        self.assertIsNone(self.row()["runtime_id"])


class THESETTLEMENTBOUNDARYORDERSITSINTENTBEFOREITSRELEASE(AttemptCase):
    """W341357 item 2, third boundary: `intake.settle_revoked_resource`.

    Driven through a REAL governed generation -- acquired, launched, bound,
    expired by a clock that moved, and revoked by the reclaim's own act -- so
    `tokens.generation_of` and `tokens.token_of` answer from the journal
    rather than from a stand-in. The settlement's effect is the RELEASE, and
    the claim is that a journal which cannot record the intent leaves the
    release unordered and the generation held.
    """

    LATER = "2026-08-24T01:00:00.000Z"

    def setUp(self):
        super().setUp()
        self.attempt = self.attached()
        self.calls = []

    def attached(self, attempt_id=ATTEMPT):
        """A REAL attempt: claimed, activated, started, with a runtime attached
        and its workspace OBJECT pinned.

        Both are preconditions of the paths under test rather than fixture
        decoration: `settle_revoked_resource` answers `held` with no attached
        runtime, and `tokens.workspace_identity` refuses with no pinned
        workspace object -- which is also what the READER resolves the
        generation from, so a fixture without it would have the writer and the
        reader naming different acts.
        """
        from baton_v12.worker_manager.attempts import pin_boundary_identity

        self.claimed(attempt_id=attempt_id)
        activate_assignment(self.store, self.port, attempt_id=attempt_id,
                            expect=self.expect())
        self.adapter = Adapter()
        request_runtime_start(self.store, self.adapter, attempt_id=attempt_id)
        pin_boundary_identity(self.store, attempt_id=attempt_id,
                              source=(7, 11), workspace=(7, 13))
        return attempt_id

    def later(self):
        """THE SAME CONTROL STORE, A CLOCK THAT MOVED.

        Expiry is JUDGED at read time against the store's own clock, so an
        expired generation is produced by time passing rather than by writing
        `expired` into a fixture -- which is the one way to get a token this
        manager will actually agree is overdue.
        """
        moved = ControlStore.open(self.path, incarnation="manager-1",
                                  clock=lambda: self.LATER)
        self.addCleanup(moved.close)
        return moved

    def governance(self):
        """THE PRODUCT'S OWN GOVERNANCE, on the pinned workspace object.

        `tokens.workspace_governance()` names the resource as
        `workspace_identity(attempt)` does, which is exactly how
        `failure_cause.token_bound_runtime` resolves it -- so the writer and
        the reader cannot disagree about which generation is meant.
        """
        from baton_v12.worker_manager import tokens

        return tokens.workspace_governance()

    def revoked(self):
        """A generation this manager has withdrawn, built by its own acts."""
        from baton_v12.worker_manager import tokens

        from baton_v12.worker_manager import attempts as _attempts

        govern = self.governance()
        row = dict(self.row())
        # The generation must be the one the START OPERATION names, because
        # that is what `generation_of` is keyed on and what both the producer
        # and its reader derive.
        start = _attempts._start_operation_id(row)
        domain = tokens.domain_of("workspace",
                                  tokens.workspace_identity(row))
        token = tokens.acquire(self.store, domain, operation=start,
                               execution=ATTEMPT, attempt=ATTEMPT, seconds=1)
        tokens.journal_launch(self.store, token, start)
        tokens.bind_container(self.store,
                              tokens.token_of(self.store, domain,
                                              token["generation"]),
                              row["runtime_id"], launch=start)
        moved = self.later()
        overdue = govern.overdue(moved, row, operation=start)
        self.assertIsNotNone(overdue, "the generation is not overdue")
        govern.revoke(moved, row, operation=start)
        return moved, govern, domain, token["generation"]

    def settle_adapter(self, state="absent"):
        from types import SimpleNamespace

        return SimpleNamespace(
            observe=lambda runtime_id: {"state": state, "why": "fixture"},
            stop_expired=lambda operands: self.calls.append("stop"),
            remove=lambda operands: self.calls.append("remove"))

    def watched_release(self, govern, moved):
        """`govern.release` with a call log, which is the settlement's effect."""
        whole = govern.release

        def watching(control, attempt, **named):
            self.calls.append("release")
            return whole(control, attempt, **named)

        govern.release = watching
        return govern

    def refuse_intent(self, store):
        whole = store.transact

        def selective(operation_id, kind, signature, action):
            if kind == "attempt.cessation-intent":
                raise ContractRefusal("unavailable", "transport",
                                      "the journal is unreachable")
            return whole(operation_id, kind, signature, action)

        store.transact = selective

    def test_the_GENERATION_IS_REVOKED_AND_OVERDUE_which_is_the_precondition(self):
        """The fixture proves itself before anything is claimed about it."""
        from baton_v12.worker_manager import tokens

        moved, _govern, domain, generation = self.revoked()
        token = tokens.token_of(moved, domain, generation)
        self.assertTrue(token["expired"])
        self.assertTrue(token["revoked"])
        self.assertFalse(token["returned"])
        self.assertEqual(token["container"], self.row()["runtime_id"])

    def test_SETTLEMENT_does_NOT_RELEASE_when_the_intent_is_not_durable(self):
        from baton_v12.worker_manager import intake, tokens

        moved, govern, domain, generation = self.revoked()
        govern = self.watched_release(govern, moved)
        self.refuse_intent(moved)
        with self.assertRaises(ContractRefusal) as refused:
            intake.settle_revoked_resource(moved, self.settle_adapter(),
                                           attempt_id=ATTEMPT, govern=govern)
        # THE RELEASE WAS NOT ORDERED...
        self.assertNotIn("release", self.calls)
        self.assertEqual(refused.exception.code, "transport")
        # ...AND THE GENERATION STAYS HELD, which is the state this manager's
        # own reader already describes. Proved rather than asserted.
        token = tokens.token_of(moved, domain, generation)
        self.assertFalse(token["returned"])
        self.assertTrue(token["revoked"])

    def test_SETTLEMENT_DOES_RELEASE_when_the_intent_IS_durable(self):
        """The other half, and the release attribution both paths share.

        `tokens` journals `resource-token.returned` on EITHER release path, so
        completion is attributable from the one record both write -- which is
        why this module adds no third completion record of its own.
        """
        from baton_v12.worker_manager import intake, tokens

        moved, govern, domain, generation = self.revoked()
        govern = self.watched_release(govern, moved)
        answer = intake.settle_revoked_resource(
            moved, self.settle_adapter(), attempt_id=ATTEMPT, govern=govern)
        self.assertIn("release", self.calls)
        self.assertEqual(answer["settled"], "returned")
        self.assertTrue(tokens.token_of(moved, domain, generation)["returned"])
        # THE SETTLEMENT'S OWN INTENT AND OUTCOME, under its own component.
        intent = failure_cause.attempt_cessation_intent_of(
            moved, ATTEMPT, "settlement")
        self.assertIsNotNone(intent)
        self.assertEqual(intent["runtime_id"], self.row()["runtime_id"])
        outcome = failure_cause.attempt_cessation_outcome_of(
            moved, ATTEMPT, "settlement")
        self.assertEqual(outcome["outcome"], "ceased-absent")
        self.assertEqual(outcome["cessation"], "absent")
        # AND COMPLETION IS ATTRIBUTABLE FROM THE RECORD BOTH PATHS WRITE.
        composed = failure_cause.attempt_failure_cause_of(moved, ATTEMPT)
        self.assertEqual(failure_cause.decode(composed["completion"]),
                         (True, True))
        self.assertEqual(failure_cause.answer_of(composed), "ceased")

    def test_a_CRASH_between_the_SETTLEMENT_intent_and_its_release_leaves_INTENT_ONLY(self):
        from baton_v12.worker_manager import intake, tokens

        moved, govern, domain, generation = self.revoked()
        govern = self.watched_release(govern, moved)
        whole = failure_cause.ensure_cessation_intent

        class Died(BaseException):
            pass

        def dying(*operands, **facts):
            whole(*operands, **facts)
            raise Died("the manager stopped existing between the two")

        failure_cause.ensure_cessation_intent = dying
        self.addCleanup(setattr, failure_cause, "ensure_cessation_intent",
                        whole)
        with self.assertRaises(Died):
            intake.settle_revoked_resource(moved, self.settle_adapter(),
                                           attempt_id=ATTEMPT, govern=govern)
        self.assertNotIn("release", self.calls)
        self.assertFalse(tokens.token_of(moved, domain, generation)["returned"])
        self.assertIsNotNone(failure_cause.attempt_cessation_intent_of(
            moved, ATTEMPT, "settlement"))
        self.assertIsNone(failure_cause.attempt_cessation_outcome_of(
            moved, ATTEMPT, "settlement"))
        composed = failure_cause.attempt_failure_cause_of(moved, ATTEMPT)
        self.assertEqual(failure_cause.answer_of(composed), "intent-only")

    def test_RECLAIM_RELEASE_ATTRIBUTION_on_the_OTHER_path(self):
        """The reclaim's own release, so attribution is proved on BOTH paths."""
        from baton_v12.worker_manager import intake, tokens

        moved, govern, domain, generation = self.revoked()
        answer = intake.reclaim_expired_resource(
            moved, self.settle_adapter(), attempt_id=ATTEMPT, govern=govern)
        intent = failure_cause.attempt_cessation_intent_of(
            moved, ATTEMPT, "expiry-reclaim")
        self.assertIsNotNone(intent)
        self.assertEqual(intent["generation"], generation)
        self.assertEqual(intent["runtime_id"], self.row()["runtime_id"])
        outcome = failure_cause.attempt_cessation_outcome_of(
            moved, ATTEMPT, "expiry-reclaim")
        self.assertIsNotNone(outcome)
        # AND THE RUNTIME IDENTITY CAME FROM THE TOKEN, re-resolved here the
        # way every reader in this module re-resolves it.
        bound, _domain, bound_generation, _token = \
            failure_cause.token_bound_runtime(moved, dict(self.row()))
        self.assertEqual(bound, self.row()["runtime_id"])
        self.assertEqual(bound_generation, generation)
        self.assertEqual(answer["attempt_id"], ATTEMPT)


class THEREADCONTRACTISVERSIONEDBOUNDEDANDSECRETSAFE(AttemptCase):
    """W341357 item 4: four answers, an allowlisted bounded shape, and a canary.

    The parent composes ordinary status and the shareable report over exactly
    the API asserted here, so these are the published facts rather than
    incidental ones.
    """

    def setUp(self):
        super().setUp()
        self.recorded()

    def outcome(self, **spoiled):
        operands = {"component": "expiry-reclaim", "generation": None,
                    "runtime_id": "container-1",
                    "correlation_id": "resource.reclaim:abc",
                    "effects": ("revoke", "stop", "remove"),
                    "outcome": "ceased-absent"}
        operands.update(spoiled)
        return failure_cause.record_and_raise_cessation_outcome(
            self.store, ATTEMPT, **operands)

    def intent(self, **spoiled):
        operands = {"component": "expiry-reclaim", "generation": None,
                    "domain": "workspace:7:9", "launched": True,
                    "runtime_id": "container-1",
                    "correlation_id": "resource.reclaim:abc"}
        operands.update(spoiled)
        return failure_cause.record_and_raise_cessation_intent(
            self.store, ATTEMPT, **operands)

    def composed(self):
        return failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)

    # -- four answers and not three ------------------------------------------

    def test_the_FOUR_ANSWERS_are_FOUR_and_each_is_reachable(self):
        self.assertEqual(len(set(failure_cause.ANSWERS)), 4)
        # 1. UNKNOWN -- nobody recorded anything.
        self.assertEqual(failure_cause.answer_of(self.composed()), "unknown")
        # 2. INTENT-ONLY -- ordered, no outcome ever recorded.
        self.intent()
        self.assertEqual(failure_cause.answer_of(self.composed()),
                         "intent-only")
        # 3. KNOWN TYPED OUTCOME -- an outcome exists and cessation is unknown.
        self.outcome(outcome="stop-failed", category="refused",
                     code="precondition")
        self.assertEqual(failure_cause.answer_of(self.composed()),
                         "known-typed-outcome")
        # 4. CEASED -- positively observed, superseding the uncertain account.
        self.outcome(outcome="ceased-absent")
        self.assertEqual(failure_cause.answer_of(self.composed()), "ceased")

    def test_a_KNOWN_TYPED_FAILURE_IS_NOT_AN_UNKNOWN_CESSATION(self):
        """The two must not collapse into "no termination evidence"."""
        self.outcome(outcome="stop-failed", category="refused",
                     code="precondition")
        composed = self.composed()
        self.assertEqual(failure_cause.answer_of(composed),
                         "known-typed-outcome")
        self.assertNotEqual(failure_cause.answer_of(composed), "unknown")
        self.assertEqual(failure_cause.decode(composed["cause"]["outcome"]),
                         (True, "stop-failed"))
        self.assertEqual(failure_cause.decode(composed["cause"]["cessation"]),
                         (True, "unknown"))
        self.assertEqual(failure_cause.decode(composed["cause"]["category"]),
                         (True, "refused"))

    def test_ABSENT_IS_NOT_QUIESCENT_through_the_published_answer(self):
        self.outcome(outcome="ceased-quiescent")
        composed = self.composed()
        self.assertEqual(failure_cause.answer_of(composed), "ceased")
        self.assertEqual(failure_cause.decode(composed["cause"]["cessation"]),
                         (True, "quiescent"))
        self.assertNotEqual(
            failure_cause.decode(composed["cause"]["cessation"]),
            (True, "absent"))

    def test_NO_CALLER_CAN_FILE_A_STOP_FAILURE_AS_A_CESSATION(self):
        """`cessation` is DERIVED from the typed outcome, never supplied."""
        with self.assertRaises(TypeError):
            failure_cause.record_and_raise_cessation_outcome(
                self.store, ATTEMPT, component="expiry-reclaim",
                generation=None, runtime_id="container-1",
                correlation_id="c", effects=(), outcome="stop-failed",
                cessation="absent")
        _id, document = self.outcome(outcome="stop-failed")
        self.assertEqual(document["cessation"], "unknown")

    # -- the version gate -----------------------------------------------------

    def test_an_UNSUPPORTED_DOCUMENT_VERSION_IS_NOT_SILENTLY_ACCEPTED(self):
        composed = dict(self.composed())
        for spoiled in ("baton.v12.attempt-failure-cause/2", "", None,
                        "something-else"):
            composed["schema"] = spoiled
            for read in (failure_cause.answer_of, failure_cause.absent_of):
                with self.assertRaises(ContractRefusal) as refused:
                    read(composed)
                self.assertEqual(refused.exception.code,
                                 "unsupported-version")

    def test_the_PUBLISHED_SCHEMA_is_the_one_the_producer_emits(self):
        self.assertEqual(self.composed()["schema"],
                         failure_cause.DIAGNOSTIC_SCHEMA)
        self.assertIn(failure_cause.DIAGNOSTIC_SCHEMA,
                      failure_cause.READ_SCHEMAS)

    def test_a_BARE_SCALAR_IS_NOT_A_LEAF_and_decode_refuses_it(self):
        for spoiled in ("expiry-reclaim", 0, None, [], {"value": 1},
                        {"known": "yes", "value": 1}):
            with self.assertRaises(ContractRefusal):
                failure_cause.decode(spoiled)
        # AND A KNOWN MEMBER WITHOUT ITS SOURCE, or an unknown without its
        # reason, is refused too -- a fact nobody can check is not an answer.
        for spoiled in ({"known": True, "value": 1, "source": ""},
                        {"known": False, "value": None, "why": ""}):
            with self.assertRaises(ContractRefusal):
                failure_cause.decode(spoiled)
        # A KNOWN ZERO IS A KNOWN ZERO.
        self.assertEqual(
            failure_cause.decode({"known": True, "value": 0,
                                  "source": "tokens.token_of"}),
            (True, 0))

    # -- an honest old-record unknown ----------------------------------------

    def test_an_OLDER_RECORD_LACKING_DIAGNOSTICS_reads_as_a_BOUNDED_UNKNOWN(self):
        """It names what is absent rather than manufacturing a cause."""
        composed = self.composed()
        self.assertEqual(failure_cause.answer_of(composed), "unknown")
        self.assertIsNone(composed["cause"])
        named = failure_cause.absent_of(composed)
        for component in failure_cause.COMPONENTS:
            self.assertIn("attempt.cessation-*:" + component, named)
        self.assertIn("runtime.start-failed", named)
        self.assertIn("runtime.preparation-failed", named)
        self.assertTrue(composed["unknown"]["why"])
        # BOUNDED: the reason and the list are both capped.
        self.assertLessEqual(len(composed["unknown"]["why"]),
                             failure_cause.FIELD_BOUND)
        self.assertLessEqual(len(named), 32)
        # AND AN UNKNOWN CAUSE IS NOT AN UNKNOWN EVERYTHING: the revocation
        # axis still answers, as its own owner's absence.
        failure_cause.decode(composed["revocation"])

    # -- allowlisted, bounded, secret-safe -----------------------------------

    def leaves(self, value, path="", found=None):
        """Every leaf in the composed document, with its path."""
        found = [] if found is None else found
        if isinstance(value, dict) and "known" in value:
            found.append((path, value.get("value")))
            found.append((path + ".why", value.get("why")))
            found.append((path + ".source", value.get("source")))
            return found
        if isinstance(value, dict):
            for name, one in value.items():
                self.leaves(one, f"{path}.{name}", found)
            return found
        if isinstance(value, (list, tuple)):
            for index, one in enumerate(value):
                self.leaves(one, f"{path}[{index}]", found)
            return found
        found.append((path, value))
        return found

    def test_the_CAUSE_MEMBER_SET_is_CLOSED_and_ALLOWLISTED(self):
        self.outcome()
        cause = self.composed()["cause"]
        self.assertEqual(sorted(cause), sorted(failure_cause.CAUSE_MEMBERS))
        for name in cause:
            self.assertIn(name, failure_cause.CAUSE_MEMBERS)
            failure_cause.decode(cause[name])

    def test_EVERY_EMITTED_STRING_IS_BOUNDED(self):
        self.intent()
        self.outcome(outcome="stop-failed", category="refused",
                     code="precondition")
        for path, value in self.leaves(self.composed()):
            if isinstance(value, str):
                self.assertLessEqual(len(value), failure_cause.FIELD_BOUND,
                                     path)

    def test_a_SECRET_CANNOT_RIDE_ANY_EMITTED_FIELD(self):
        """THE CANARY, pushed at every door a secret could plausibly use.

        A credential, an environment value, a provider's text and an arbitrary
        exception repr are each offered to the recording path, and none of them
        has a member to travel in -- the typed pair and the identities are all
        that cross. Proved by walking EVERY leaf of the composed document
        rather than by eyeballing the member list.
        """
        os.environ["BATON_CANARY_FOR_THIS_CASE"] = SECRET
        self.addCleanup(os.environ.pop, "BATON_CANARY_FOR_THIS_CASE", None)
        # 1. a refusal whose PROSE quotes adapter text carrying the secret.
        said = failure_cause.record_cessation_outcome(
            self.store, ATTEMPT, component="cancellation", generation=None,
            runtime_id="container-1", correlation_id="cancel-1", effects=(),
            outcome="stop-failed", category="refused", code="precondition")
        self.assertFalse(failure_cause.recording_degraded(said))
        # 2. an intent whose correlation and runtime are ordinary identities.
        self.intent()
        # 3. an undeclared outcome carrying the secret in its own name, which
        #    is refused before anything is written.
        refused = failure_cause.record_cessation_outcome(
            self.store, ATTEMPT, component="settlement", generation=None,
            runtime_id="container-1", correlation_id="settle-1", effects=(),
            outcome=SECRET)
        self.assertIn("could not be recorded", refused)
        composed = self.composed()
        for path, value in self.leaves(composed):
            if isinstance(value, str):
                self.assertNotIn(SECRET, value, path)
                self.assertNotIn("canary-", value, path)
        self.assertNotIn(SECRET, repr(composed))
        # AND NO ENVIRONMENT VALUE AT ALL reaches the document.
        self.assertNotIn("BATON_CANARY_FOR_THIS_CASE", repr(composed))

    def test_the_RECORD_MEMBER_SETS_HAVE_NO_PROSE_MEMBER(self):
        """Structural, so it holds for inputs no case thought to try."""
        for members in (documents.ATTEMPT_CESSATION_INTENT,
                        documents.ATTEMPT_CESSATION_OUTCOME):
            for name in members:
                self.assertNotIn(name, ("why", "message", "detail", "stderr",
                                        "failure", "repr", "text", "output",
                                        "environment", "credential"))

    # -- every read mutates nothing ------------------------------------------

    def journal(self):
        beside = sqlite3.connect(self.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        try:
            tables = [one["name"] for one in beside.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")]
            return {one: [dict(row) for row in beside.execute(
                f"SELECT * FROM \"{one}\"")] for one in sorted(tables)}
        finally:
            beside.close()

    def test_EVERY_READ_MUTATES_NOTHING(self):
        """No claim, renewal, reconciliation, acknowledgement, retry, store
        creation or migration -- proved by comparing the WHOLE journal.

        A normal SQLite read-only sidecar is allowed; a changed row is not.
        """
        self.intent()
        self.outcome(outcome="uncertain-observation")
        self.outcome(outcome="ceased-absent")
        before = self.journal()
        for read in (
                lambda: failure_cause.attempt_failure_cause_of(self.store,
                                                               ATTEMPT),
                lambda: failure_cause.attempt_cessation_intent_of(
                    self.store, ATTEMPT, "expiry-reclaim"),
                lambda: failure_cause.attempt_cessation_outcome_of(
                    self.store, ATTEMPT, "expiry-reclaim"),
                lambda: failure_cause.token_bound_runtime(
                    self.store, dict(self.row())),
                lambda: failure_cause.answer_of(self.composed()),
                lambda: failure_cause.absent_of(self.composed())):
            read()
            read()
        self.assertEqual(self.journal(), before)

    def test_a_READ_ONLY_STORE_can_still_answer_every_reader(self):
        """The report runs over a read-only handle, so the readers must not
        need a writable one. A store that refuses every act is the proof."""
        self.intent()
        self.outcome()
        before = self.journal()

        def refusing(*operands, **named):
            raise ContractRefusal("policy", "denied",
                                  "a read-only manager performs no action")

        self.store.transact = refusing
        composed = failure_cause.attempt_failure_cause_of(self.store, ATTEMPT)
        self.assertEqual(failure_cause.answer_of(composed), "ceased")
        self.assertIsNotNone(failure_cause.attempt_cessation_intent_of(
            self.store, ATTEMPT, "expiry-reclaim"))
        self.assertEqual(self.journal(), before)

    def test_an_UNCERTAIN_TO_POSITIVE_history_keeps_BOTH_and_names_the_CURRENT(self):
        """Item 3, read through the published composition.

        The uncertain account is not rewritten, the positive one is current,
        and the composed cause reports HOW MANY earlier accounts it replaced
        as a KNOWN COUNT rather than as an absence.
        """
        first, _held = self.outcome(outcome="uncertain-observation")
        later, placed = self.outcome(outcome="ceased-absent")
        self.assertNotEqual(first, later)
        self.assertEqual(placed["supersedes"], first)
        found = failure_cause.attempt_cessation_outcome_of(
            self.store, ATTEMPT, "expiry-reclaim")
        self.assertEqual(found["revision"], 1)
        self.assertEqual(len(found["superseded"]), 1)
        self.assertEqual(found["superseded"][0]["outcome"],
                         "uncertain-observation")
        composed = self.composed()
        self.assertEqual(failure_cause.answer_of(composed), "ceased")
        self.assertEqual(failure_cause.decode(composed["cause"]["superseded"]),
                         (True, 1))
        # A KNOWN ZERO, on a chain nobody superseded.
        self.outcome(component="settlement", outcome="ceased-absent",
                     effects=())
        settled = failure_cause.attempt_cessation_outcome_of(
            self.store, ATTEMPT, "settlement")
        self.assertEqual(settled["revision"], 0)
        self.assertEqual(settled["superseded"], ())
