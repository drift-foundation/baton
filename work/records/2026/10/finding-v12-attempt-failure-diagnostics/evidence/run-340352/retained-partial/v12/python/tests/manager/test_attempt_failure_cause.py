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

import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import documents, failure_cause

from .test_attempts import ATTEMPT, AttemptCase

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
        self.assertEqual(composed["cause"]["outcome_state"],
                         "ordered-without-outcome")
        self.assertEqual(composed["cause"]["cessation"], "unknown")

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
        for name in ("revocation", "completion", "token", "domain",
                     "generation", "start_failure", "preparation_failure"):
            member = composed[name]
            if member["known"]:
                self.assertTrue(member["source"], name)
            else:
                self.assertTrue(member["why"], name)
                self.assertIsNone(member["value"], name)

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
        self.assertEqual(composed["cause"]["component"], "expiry-reclaim")
        self.assertEqual(composed["cause"]["cessation"], "absent")
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
