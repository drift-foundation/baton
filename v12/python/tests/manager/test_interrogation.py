"""W6627 — the operator interrogation split: `probe` and `inquire`.

`work/records/2026/08/finding-v12-manager-agent-session-protocols/`, the
approver ruling of 2026-08-25.

THE DEFECT THIS REMOVES. v11's conversational `poke` conflated two facts:
whether the adapter and the session can be OBSERVED right now, and whether a
model has accepted and answered a new request. One operation answering both
charges an operator a model turn for asking "is it alive", and leaves an
operator who asked "please consider this" unable to tell a delivery from an
answer.

The review's required evidence, and every case below belongs to one line of it:
positive and negative `probe` and `inquire` shapes; operation replay and
collision; restart between enqueue, delivery, answer, journal and Baton
publication; manager deadline expiry WITHOUT cancellation; adapter-unreachable
and runtime-absent distinguished; answer correlation and safe-turn delivery;
and proof that no worker receives a Baton or SQLite capability.
"""

import json
import os
import sqlite3
import tempfile
import unittest

import baton_v12.worker_manager as worker_manager
from baton_v12.contracts import SECRET_MEMBERS, ContractRefusal
from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                      INTERROGATION_KINDS, inquire,
                                      interrogation_of, interrogations_of,
                                      probe, publish_inquiry_answer,
                                      record_inquiry_answer,
                                      settle_interrogation)
from baton_v12.worker_manager import schema
from baton_v12.worker_manager.interrogation import (INQUIRY_ACKNOWLEDGEMENTS,
                                                    MAX_ANSWER, MAX_QUESTION,
                                                    PROBE_ANSWERS)

from .test_attempts import ADAPTER, ATTEMPT
from .test_handshake import acp_profile
from .test_offers import (FakeSession, NOW, PROFILE, UUID, WHO, WORK,
                          fake_claim_signature)

PROVIDER = "provider-session-1"
LATER = "2026-08-24T00:05:00.000Z"


class Agent:
    """The agent adapter contract, with every answer a case may set.

    Deliberately records what it was asked, because half of what this suite
    proves is about the REQUEST the manager makes rather than the answer it
    gets back.
    """

    def __init__(self):
        self.probed = []
        self.inquired = []
        self.cancelled = []
        self.observed = []
        self.probe_answer = {"kind": "observed", "state": "ready",
                             "provider_session_id": PROVIDER,
                             "last_activity_at": NOW,
                             "diagnostics": {"acp.example/1": "idle"}}
        self.inquiry_answer = {"kind": "queued"}
        self.failure = None

    def cancel(self, operands):
        self.cancelled.append(operands)
        return {"acknowledged": True}

    def observe_session(self, reference):
        self.observed.append(reference)
        return {"kind": "present", "state": "ready",
                "provider_session_id": reference["provider_session_id"]}

    def probe(self, request):
        self.probed.append(request)
        if self.failure is not None:
            raise self.failure
        return self.probe_answer

    def inquire(self, request):
        self.inquired.append(request)
        if self.failure is not None:
            raise self.failure
        return self.inquiry_answer


class PublishingSession(FakeSession):
    """The injected authority session, with the one member W6627 adds.

    The manager is the ONE Baton client: an answer published by the worker
    would need the worker to hold a Baton capability, and the topology exists
    so that it does not.
    """

    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self.published = []
        self.publish_answer_result = "baton:M4242"

    def publish_answer(self, operands):
        self.published.append(dict(operands))
        if isinstance(self.publish_answer_result, BaseException):
            raise self.publish_answer_result
        return self.publish_answer_result


class InterrogationCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-interrogation-")
        self.addCleanup(self._root.cleanup)
        self.path = os.path.join(self._root.name, "control.sqlite3")
        self.store = ControlStore.open(self.path, incarnation="manager-1",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        worker_manager.certify_profile(self.store, "runtime", "reference",
                                       PROFILE)
        self.session = PublishingSession()
        self.port = AuthorityPort(self.session, fake_claim_signature)
        self.profile = acp_profile()
        worker_manager.certify_agent_session_profile(self.store, self.profile)
        self.digest = self.profile["document_digest"]
        self.agent = Agent()
        self.opened()

    def opened(self, posture="execution"):
        worker_manager.issue_offer(
            self.store, self.port, offer_id="offer-1", work_id=WORK,
            runtime_attempt_id=ATTEMPT, input_digest="sha256:" + "1" * 64,
            policy_digest="sha256:" + "2" * 64, profile_digest=PROFILE,
            profile_name="reference", mint_bearer=lambda: "bearer-1")
        worker_manager.accept_offer(
            self.store, self.port, offer_id="offer-1", decision="accept",
            bearer="bearer-1", now=NOW, runtime_attempt_id=ATTEMPT,
            work_ref={"authority_uuid": UUID, "work_id": WORK})
        worker_manager.record_attempt(
            self.store, attempt_id=ATTEMPT, adapter_name="acp",
            adapter_digest=ADAPTER, profile_digest=PROFILE)
        worker_manager.submit_claim(self.store, self.port, offer_id="offer-1")
        worker_manager.activate_assignment(
            self.store, self.port, attempt_id=ATTEMPT,
            expect={"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                    "participant": WHO, "generation": 1})
        worker_manager.open_agent_session(
            self.store, self.port, attempt_id=ATTEMPT, posture=posture,
            profile_digest=self.digest, intent="open-1")
        worker_manager.adopt_provider_session(
            self.store, attempt_id=ATTEMPT, posture=posture, session_epoch=1,
            provider_session_id=PROVIDER)
        return ATTEMPT

    # -- drivers -------------------------------------------------------

    def probing(self, operation_id="probe-1", **spoiled):
        operands = dict(attempt_id=ATTEMPT, posture="execution",
                        session_epoch=1, operation_id=operation_id,
                        deadline_seconds=30)
        operands.update(spoiled)
        return probe(self.store, self.port, self.agent, **operands)

    def inquiring(self, operation_id="inquire-1", **spoiled):
        operands = dict(attempt_id=ATTEMPT, posture="execution",
                        session_epoch=1, operation_id=operation_id,
                        deadline_seconds=30, question="how is it going?")
        operands.update(spoiled)
        return inquire(self.store, self.port, self.agent, **operands)

    def row(self, operation_id):
        beside = sqlite3.connect(self.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        try:
            found = beside.execute(
                "SELECT * FROM interrogations WHERE operation_id = ?",
                (operation_id,)).fetchone()
            return None if found is None else {k: found[k]
                                               for k in found.keys()}
        finally:
            beside.close()


# -- the two operations are two ----------------------------------------------

class TheSplitIsTheWholePoint(InterrogationCase):

    def test_the_two_kinds_are_the_whole_set(self):
        self.assertEqual(INTERROGATION_KINDS, ("probe", "inquire"))

    def test_a_probe_consumes_no_model_turn(self):
        """The half of v11's `poke` an operator asking "is this alive" should
        never have been charged for."""
        self.probing()
        self.assertEqual(len(self.agent.probed), 1)
        self.assertEqual(self.agent.inquired, [],
                         "a probe asked the model something")

    def test_a_probe_reports_the_control_plane_reading(self):
        answer = self.probing()
        self.assertEqual(answer["outcome"], "observed")
        self.assertEqual(answer["observation"]["state"], "ready")
        self.assertEqual(answer["observation"]["last_activity_at"], NOW)
        self.assertEqual(answer["observation"]["diagnostics"],
                         {"acp.example/1": "idle"})
        self.assertIs(answer["answered"], False)

    def test_an_inquiry_is_acknowledged_and_not_answered(self):
        """The acknowledgement is not the answer, which is the split's whole
        content: `queued` and `delivered` are facts about where the request
        got to, and neither is a model saying anything."""
        answer = self.inquiring()
        self.assertEqual(answer["outcome"], "queued")
        self.assertIs(answer["answered"], False)
        self.assertIsNone(answer["published_at"])

    def test_an_acknowledgement_can_never_be_an_answer(self):
        """An adapter that could answer synchronously would be reporting a
        model turn it has not had, so `answered` is not in the set at all."""
        self.assertNotIn("answered", INQUIRY_ACKNOWLEDGEMENTS)
        self.agent.inquiry_answer = {"kind": "answered"}
        with self.assertRaises(ContractRefusal) as caught:
            self.inquiring()
        self.assertEqual(caught.exception.code, "schema")

    def test_the_adapter_contract_carries_both(self):
        self.assertEqual(worker_manager.AGENT_ADAPTER,
                         ("cancel", "observe_session", "probe", "inquire"))

    def test_an_adapter_missing_either_is_refused(self):
        for absent in ("probe", "inquire"):
            with self.subTest(absent=absent):
                class Partial:
                    pass

                for name in ("probe", "inquire"):
                    if name != absent:
                        setattr(Partial, name, lambda self, request: None)
                with self.assertRaises(ContractRefusal) as caught:
                    probe(self.store, self.port, Partial(),
                          attempt_id=ATTEMPT, posture="execution",
                          session_epoch=1, operation_id="probe-x",
                          deadline_seconds=30)
                self.assertEqual(caught.exception.code, "schema")


# -- the four bindings -------------------------------------------------------

class BothBindTheExactAssignmentAndSession(InterrogationCase):

    def test_the_journalled_row_carries_all_four_bindings(self):
        self.probing()
        row = self.row("probe-1")
        self.assertEqual(
            (row["runtime_attempt_id"], row["posture"], row["session_epoch"]),
            (ATTEMPT, "execution", 1))
        self.assertEqual(
            (row["authority_uuid"], row["work_id"],
             row["assignment_participant"], row["assignment_generation"]),
            (UUID, WORK, WHO, 1))
        self.assertEqual(row["operation_id"], "probe-1")
        self.assertEqual(row["deadline_at"], "2026-08-24T00:00:30.000Z")

    def test_a_session_that_does_not_exist_is_interrogated_by_nobody(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.probing(session_epoch=9)
        self.assertEqual(caught.exception.code, "precondition")

    def test_a_dead_generation_is_refused(self):
        """An interrogation is about work somebody is executing; asking about
        a generation that ended is asking about somebody else's."""
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal) as caught:
            self.probing()
        self.assertEqual(caught.exception.category, "stale-assignment")

    def test_a_superseded_generation_is_refused(self):
        self.session.live_assignment = {
            "work_ref": {"authority_uuid": UUID, "work_id": WORK},
            "participant": WHO, "generation": 2}
        with self.assertRaises(ContractRefusal) as caught:
            self.inquiring()
        self.assertEqual(caught.exception.code, "generation")

    def test_a_foreign_session_interrogates_nothing(self):
        other = AuthorityPort(PublishingSession(participant="lang.bee"),
                              fake_claim_signature)
        with self.assertRaises(ContractRefusal) as caught:
            probe(self.store, other, self.agent, attempt_id=ATTEMPT,
                  posture="execution", session_epoch=1,
                  operation_id="probe-x", deadline_seconds=30)
        self.assertEqual(caught.exception.code, "capability")

    def test_a_consent_session_carries_no_generation_to_bind(self):
        """A consent session exists before any claim, so there is no exact
        assignment for an interrogation to be about."""
        worker_manager.open_agent_session(
            self.store, self.port, attempt_id=ATTEMPT, posture="consent",
            profile_digest=self.digest, intent="open-consent")
        with self.assertRaises(ContractRefusal) as caught:
            self.probing(posture="consent")
        self.assertIn("carries no assignment", caught.exception.message)

    def test_an_answer_about_another_provider_session_is_refused(self):
        self.agent.probe_answer = {**self.agent.probe_answer,
                                   "provider_session_id": "somebody-else"}
        with self.assertRaises(ContractRefusal) as caught:
            self.probing()
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_the_adapter_is_asked_about_the_exact_session(self):
        self.probing()
        asked = self.agent.probed[0]
        self.assertEqual(asked["runtime_attempt_id"], ATTEMPT)
        self.assertEqual(asked["posture"], "execution")
        self.assertEqual(asked["session_epoch"], 1)
        self.assertEqual(asked["provider_session_id"], PROVIDER)
        self.assertEqual(asked["operation_id"], "probe-1")


# -- effectively once --------------------------------------------------------

class TheOperationIdentityIsEffectivelyOnce(InterrogationCase):

    def test_an_exact_retry_replays_and_asks_the_adapter_once(self):
        first = self.probing()
        again = self.probing()
        self.assertEqual(first["operation_id"], again["operation_id"])
        self.assertEqual(len(self.agent.probed), 1,
                         "an exact retry asked the adapter a second time")
        self.assertEqual(again["outcome"], "observed")

    def test_an_exact_retry_is_not_redecided_by_later_assignment_liveness(
            self):
        """The journal decides replay before mutable external authority.

        A fresh interrogation still requires a live exact assignment. Once
        that interrogation has a durable answer, however, a later retry is a
        read of the operation already performed, not a new interrogation of
        the now-ended assignment.
        """
        first = self.probing()
        self.session.live_assignment = None
        again = self.probing()
        self.assertEqual(again, first)
        self.assertEqual(len(self.agent.probed), 1,
                         "the replay asked the adapter a second time")

    def test_an_exact_retry_does_not_collide_with_the_managers_new_clock(self):
        """Wall time is not a caller operand and cannot change an operation's
        identity across restart."""
        first = self.probing()
        self.store._clock = lambda: LATER
        again = self.probing()
        self.assertEqual(first["operation_id"], again["operation_id"])
        self.assertEqual(len(self.agent.probed), 1,
                         "an exact retry asked the adapter a second time")

    def test_an_exact_retry_does_not_recompute_an_impossible_later_deadline(
            self):
        """The later clock decides NOTHING, including whether a derived
        deadline is representable. Replay must reach the journal before doing
        fresh-request clock arithmetic."""
        first = self.probing()
        self.store._clock = lambda: "9999-12-31T23:59:59.999Z"
        again = self.probing()
        self.assertEqual(again, first)
        self.assertEqual(len(self.agent.probed), 1,
                         "an exact retry asked the adapter a second time")

    def test_a_different_question_under_one_identity_collides(self):
        self.inquiring()
        with self.assertRaises(ContractRefusal) as caught:
            self.inquiring(question="something else entirely")
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_a_different_session_under_one_identity_collides(self):
        self.probing()
        with self.assertRaises(ContractRefusal) as caught:
            self.probing(deadline_seconds=60)
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_the_store_itself_holds_one_row_per_identity(self):
        self.probing()
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        with self.assertRaises(sqlite3.IntegrityError):
            beside.execute(
                "INSERT INTO interrogations (operation_id, kind, "
                "runtime_attempt_id, posture, session_epoch, authority_uuid, "
                "work_id, assignment_participant, assignment_generation, "
                "requested_at, deadline_at, outcome) VALUES "
                "('probe-1', 'probe', ?, 'execution', 1, ?, ?, ?, 1, ?, ?, "
                "'requested')", (ATTEMPT, UUID, WORK, WHO, NOW, LATER))


# -- the outcomes are six and they are different -----------------------------

class TheOutcomesAreDistinguished(InterrogationCase):

    def test_an_unreachable_adapter_is_not_an_absent_runtime(self):
        """Neither implies the other. An adapter this manager could not reach
        says nothing about the runtime, and a runtime observed absent says
        nothing about whether the adapter is up."""
        self.agent.probe_answer = {"kind": "unreachable",
                                   "why": "the socket refused"}
        self.assertEqual(self.probing()["outcome"], "adapter-unreachable")
        self.agent.probe_answer = {"kind": "runtime-absent",
                                   "provider_session_id": PROVIDER}
        self.assertEqual(self.probing("probe-2")["outcome"], "runtime-absent")

    def test_an_inquiry_distinguishes_queued_from_delivered(self):
        self.agent.inquiry_answer = {"kind": "delivered"}
        self.assertEqual(self.inquiring()["outcome"], "delivered")
        self.agent.inquiry_answer = {"kind": "queued"}
        self.assertEqual(self.inquiring("inquire-2")["outcome"], "queued")

    def test_an_unrecognised_answer_is_refused_rather_than_read(self):
        for spoiled in ({"kind": "fine"}, {"kind": "observed"},
                        {"kind": "unreachable"}):
            with self.subTest(answer=spoiled):
                self.agent.probe_answer = spoiled
                with self.assertRaises(ContractRefusal) as caught:
                    self.probing(f"probe-{id(spoiled)}")
                self.assertEqual(caught.exception.code, "schema")

    def test_a_probe_state_is_owned_as_the_frozen_session_vocabulary(self):
        """A runtime state cannot cross as an agent-session observation."""
        self.agent.probe_answer = {**self.agent.probe_answer,
                                   "state": "running"}
        with self.assertRaises(ContractRefusal):
            self.probing()

    def test_the_two_axes_are_two(self):
        """A probe is never queued and an inquire is never merely observed;
        one merged table would admit both."""
        probe_axis = schema.INTERROGATION_OUTCOMES["probe"]
        inquire_axis = schema.INTERROGATION_OUTCOMES["inquire"]
        self.assertNotIn("queued", probe_axis)
        self.assertNotIn("delivered", probe_axis)
        self.assertNotIn("answered", probe_axis)
        self.assertNotIn("observed", inquire_axis)

    def test_an_outcome_from_the_other_axis_is_refused(self):
        self.probing()
        with self.assertRaises(ContractRefusal) as caught:
            settle_interrogation(self.store, operation_id="probe-1",
                                 outcome="answered")
        self.assertEqual(caught.exception.code, "schema")

    def test_a_terminal_outcome_does_not_move_again(self):
        self.probing()
        with self.assertRaises(ContractRefusal) as caught:
            settle_interrogation(self.store, operation_id="probe-1",
                                 outcome="adapter-unreachable")
        self.assertEqual(caught.exception.code, "state-regression")


# -- a timeout is an observation ---------------------------------------------

class ATimeoutIsAnObservationAndNotACancellation(InterrogationCase):

    def test_the_deadline_is_the_managers_own(self):
        """Nothing in the worker is asked to agree with it, and nothing about
        it cancels anything."""
        self.inquiring()
        row = self.row("inquire-1")
        self.assertEqual(row["deadline_at"], "2026-08-24T00:00:30.000Z")
        self.assertEqual(self.agent.inquired[0]["deadline_at"],
                         row["deadline_at"])

    def test_a_timeout_cancels_nothing(self):
        self.inquiring()
        settle_interrogation(self.store, operation_id="inquire-1",
                             outcome="timed-out")
        self.assertEqual(self.agent.cancelled, [],
                         "a timeout cancelled the agent")
        beside = sqlite3.connect(self.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        self.addCleanup(beside.close)
        axis = beside.execute(
            "SELECT execution_runtime FROM attempts WHERE "
            "runtime_attempt_id = ?", (ATTEMPT,)).fetchone()
        self.assertEqual(axis["execution_runtime"], "not-started")

    def test_a_model_that_answers_after_the_timeout_is_answering(self):
        """`timed-out` is NOT terminal, and that is the ruling rather than an
        oversight: an axis that made it terminal would turn this manager's
        patience into a decision about somebody else's turn."""
        self.inquiring()
        settle_interrogation(self.store, operation_id="inquire-1",
                             outcome="timed-out")
        settled = record_inquiry_answer(
            self.store, operation_id="inquire-1",
            answer={"body": "it is going well, thank you"})
        self.assertEqual(settled["outcome"], "answered")
        self.assertIs(settled["answered"], True)

    def test_a_probe_may_also_be_observed_after_a_timeout(self):
        """The same rule on the other axis: this manager stopping its wait is
        not the adapter becoming unobservable.

        The request has to still be OPEN for a timeout to be about it, which
        is what an adapter that never returns produces — and reaching it this
        way also proves the request was journalled BEFORE the adapter was
        called, because otherwise there would be no row to time out.
        """
        self.assertIn("observed",
                      schema.INTERROGATION_OUTCOMES["probe"]["timed-out"])
        self.agent.failure = TimeoutError("the adapter never came back")
        with self.assertRaises(TimeoutError):
            self.probing()
        self.assertEqual(self.row("probe-1")["outcome"], "requested")

        settle_interrogation(self.store, operation_id="probe-1",
                             outcome="timed-out")
        # A LATE OBSERVATION IS STILL AN OBSERVATION, and it carries its
        # reading. Re-review [P1] made the pairing a rule: an `observed` probe
        # row without one is refused, here and by the column's own CHECK.
        late = settle_interrogation(self.store, operation_id="probe-1",
                                    outcome="observed",
                                    observation=dict(self.agent.probe_answer))
        self.assertEqual(late["outcome"], "observed")
        self.assertEqual(late["observation"]["state"], "ready")

    def test_an_observation_is_read_back_by_every_durable_view(self):
        """Not only after a restart: the replay, the single lookup and the
        list all reconstruct the same row, and each of them omitted the
        reading before this correction."""
        fresh = self.probing()
        self.assertEqual(fresh["observation"]["state"], "ready")
        again = worker_manager.probe(
            self.store, self.port, self.agent, attempt_id=ATTEMPT,
            posture="execution", session_epoch=1, operation_id="probe-1",
            deadline_seconds=30)
        self.assertEqual(again["observation"], fresh["observation"])
        one = worker_manager.interrogation_of(self.store, "probe-1")
        self.assertEqual(one["observation"], fresh["observation"])
        listed = worker_manager.interrogations_of(
            self.store, ATTEMPT, "execution", 1)
        self.assertEqual([entry["observation"] for entry in listed
                          if entry["operation_id"] == "probe-1"],
                         [fresh["observation"]])

    def test_an_unobserved_outcome_carries_no_observation_member_at_all(self):
        """Absent rather than null, which is the constructor's rule and is why
        `observation` is optional in the contract: a member present and empty
        would say the manager looked and saw nothing."""
        self.agent.probe_answer = {"kind": "unreachable", "why": "no route"}
        answer = self.probing()
        self.assertEqual(answer["outcome"], "adapter-unreachable")
        self.assertNotIn("observation", answer)
        self.assertIsNone(self.row("probe-1")["observation"])

    def test_a_runtime_axis_state_never_crosses_as_a_session_state(self):
        """The two vocabularies stay two. `alternative` closes the member
        NAMES and does not own their values, so without this the runtime
        axis's own words would be written into a durable session reading."""
        sound = dict(self.agent.probe_answer)
        # TWO RULES, IN ORDER, and the refusal says which one it is. The type
        # is established first — `x in mapping` on a list RAISES rather than
        # answering, so a membership check that assumed its own operand's type
        # would not be owning the field — and the frozen vocabulary second.
        for spoiled, expected in (("running", "nine agent session states"),
                                  ("attached", "nine agent session states"),
                                  ("", "durable text"),
                                  (None, "durable text"),
                                  (["ready"], "durable text")):
            with self.subTest(state=spoiled):
                self.agent.probe_answer = {**sound, "state": spoiled}
                with self.assertRaises(ContractRefusal) as caught:
                    self.probing(f"probe-state-{spoiled!r}")
                self.assertEqual(caught.exception.code, "schema")
                self.assertIn("an observed session state",
                              caught.exception.message)
                self.assertIn(expected, caught.exception.message)

    def test_an_observed_instant_and_its_diagnostics_are_owned(self):
        """The other two members. Both are persisted now, so an unowned one
        would be written into the row and read back by every later lookup as
        though this manager had established it."""
        cases = {
            "last_activity_at": ("not-an-instant",
                                 "an observed last activity instant"),
            "diagnostics": ("not a document", "probe diagnostics"),
        }
        # ONE SPOILED MEMBER AT A TIME, from a FRESH answer each round: an
        # accumulating fixture would leave the first round's fault in place and
        # the second would refuse for the first one's reason.
        sound = dict(self.agent.probe_answer)
        for member, (spoiled, label) in cases.items():
            with self.subTest(member=member):
                self.agent.probe_answer = {**sound, member: spoiled}
                with self.assertRaises(ContractRefusal) as caught:
                    self.probing(f"probe-{member}")
                self.assertIn(label, caught.exception.message)

    def test_diagnostics_are_bounded_in_both_dimensions(self):
        """Bounded has to mean bounded in the dimension a careless adapter
        would grow. A nested structure is refused too: a durable column is not
        a place to put whatever an adapter felt like."""
        sound = dict(self.agent.probe_answer)
        for spoiled in ({f"k{index}": "v" for index in range(33)},
                        {"acp.example/1": "x" * 2_001},
                        {"acp.example/1": {"nested": True}},
                        {"": "unnamed"}):
            with self.subTest(diagnostics=sorted(spoiled)[:1]):
                self.agent.probe_answer = {**sound, "diagnostics": spoiled}
                with self.assertRaises(ContractRefusal):
                    self.probing(f"probe-{id(spoiled)}")

    def test_diagnostic_names_and_numbers_cannot_bypass_the_character_bound(
            self):
        """A one-entry document is still unbounded when its key or integer
        representation can grow without limit. Both become durable JSON just
        like a string value does."""
        sound = dict(self.agent.probe_answer)
        for operation_id, spoiled in (
                ("probe-long-diagnostic-name", {"k" * 2_001: "v"}),
                ("probe-long-diagnostic-number", {"turns": 10 ** 2_000})):
            with self.subTest(operation_id=operation_id):
                self.agent.probe_answer = {**sound, "diagnostics": spoiled}
                with self.assertRaises(ContractRefusal):
                    self.probing(operation_id)

    def test_public_settlement_cannot_bypass_observation_ownership(self):
        """`settle_interrogation` is exported and receives the reading too.
        Typing only the fresh adapter path leaves this second public door able
        to persist a runtime-axis state as an agent-session observation."""
        self.agent.failure = TimeoutError("the adapter never came back")
        with self.assertRaises(TimeoutError):
            self.probing()
        with self.assertRaises(ContractRefusal) as caught:
            settle_interrogation(
                self.store, operation_id="probe-1", outcome="observed",
                observation={**self.agent.probe_answer, "state": "running"})
        self.assertEqual(caught.exception.code, "schema")

    def test_an_ordinary_diagnostics_document_is_kept_verbatim(self):
        """The bound refuses excess and nothing else: what an adapter
        legitimately reports survives to the durable view unchanged."""
        self.agent.probe_answer = {
            **self.agent.probe_answer,
            "diagnostics": {"acp.example/1": "idle", "turns": 3,
                            "degraded": False}}
        answer = self.probing()
        self.assertEqual(answer["observation"]["diagnostics"],
                         {"acp.example/1": "idle", "turns": 3,
                          "degraded": False})
        self.assertEqual(
            worker_manager.interrogation_of(
                self.store, "probe-1")["observation"]["diagnostics"],
            {"acp.example/1": "idle", "turns": 3, "degraded": False})

    def test_probe_diagnostics_named_for_a_secret_never_reach_the_row(self):
        """Owning a bounded document is not the durable-secret walk.

        Adapter diagnostics are free injected structure and become durable in
        the observation column. A secret-shaped member must be refused before
        that write, just as it is at every other durable free-form boundary.
        """
        self.agent.probe_answer = {
            **self.agent.probe_answer,
            "diagnostics": {"claim_token": "anything"}}
        with self.assertRaises(ContractRefusal) as caught:
            self.probing()
        self.assertEqual(caught.exception.code, "secret-leak")
        self.assertEqual(self.row("probe-1")["outcome"], "requested")
        self.assertIsNone(self.row("probe-1")["observation"])

    def test_the_public_door_owns_what_the_adapter_path_owns(self):
        """One observation owner, at every receiving door. The exported
        settlement used to take its caller's reading straight to the column,
        so the vocabulary collapse the adapter path refuses survived at the
        door nobody had checked."""
        self.agent.failure = TimeoutError("the adapter never came back")
        with self.assertRaises(TimeoutError):
            self.probing()
        sound = {"kind": "observed", "state": "ready",
                 "provider_session_id": PROVIDER,
                 "last_activity_at": NOW, "diagnostics": {}}
        for spoiled in ({**sound, "state": "running"},
                        {**sound, "last_activity_at": "not-an-instant"},
                        {**sound, "diagnostics": "not a document"},
                        {**sound, "diagnostics": {"k" * 2_001: "v"}},
                        {"kind": "observed", "state": "ready"}):
            with self.subTest(observation=sorted(spoiled)):
                with self.assertRaises(ContractRefusal):
                    settle_interrogation(self.store, operation_id="probe-1",
                                         outcome="observed",
                                         observation=spoiled)
        self.assertEqual(self.row("probe-1")["outcome"], "requested")
        self.assertIsNone(self.row("probe-1")["observation"])

    def test_the_public_door_binds_the_exact_provider_session(self):
        """An observation about another session is about another session,
        whichever door it arrives at."""
        self.agent.failure = TimeoutError("the adapter never came back")
        with self.assertRaises(TimeoutError):
            self.probing()
        with self.assertRaises(ContractRefusal) as caught:
            settle_interrogation(
                self.store, operation_id="probe-1", outcome="observed",
                observation={"kind": "observed", "state": "ready",
                             "provider_session_id": "provider-somebody-else",
                             "last_activity_at": NOW, "diagnostics": {}})
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_a_second_settlement_with_a_different_reading_is_refused(self):
        """The idempotence re-audit. Answering the second caller with the
        FIRST reading would tell them theirs was recorded when it was
        discarded."""
        first = self.probing()
        same = settle_interrogation(
            self.store, operation_id="probe-1", outcome="observed",
            observation=dict(self.agent.probe_answer))
        self.assertEqual(same["observation"], first["observation"])
        with self.assertRaises(ContractRefusal) as caught:
            settle_interrogation(
                self.store, operation_id="probe-1", outcome="observed",
                observation={**self.agent.probe_answer, "state": "closed"})
        self.assertEqual(caught.exception.code, "already-terminal")
        self.assertEqual(
            worker_manager.interrogation_of(
                self.store, "probe-1")["observation"]["state"], "ready")

    def test_a_diagnostic_named_for_a_secret_never_becomes_durable(self):
        """Ownership is not the secret walk. §13's named half refuses a member
        NAMED for a secret whether or not this process is holding one, and the
        observation is walked at the one owner both doors reach — so neither
        the adapter path nor the exported settlement can persist it."""
        sound = dict(self.agent.probe_answer)
        # The frozen member names themselves, so this cannot drift from the
        # rule: a name outside `SECRET_MEMBERS` is ordinary text and refusing
        # it would be a different rule with the same spelling.
        for name in SECRET_MEMBERS:
            with self.subTest(diagnostic=name):
                self.agent.probe_answer = {
                    **sound, "diagnostics": {name: "anything"}}
                with self.assertRaises(ContractRefusal) as caught:
                    self.probing(f"probe-{name}")
                self.assertEqual(caught.exception.code, "secret-leak")
                self.assertIsNone(self.row(f"probe-{name}")["observation"])

    def test_the_exported_settlement_walks_the_reading_too(self):
        """The same rule at the other door, because a guard on one of two
        doors is not a guard."""
        self.agent.failure = TimeoutError("the adapter never came back")
        with self.assertRaises(TimeoutError):
            self.probing()
        with self.assertRaises(ContractRefusal) as caught:
            settle_interrogation(
                self.store, operation_id="probe-1", outcome="observed",
                observation={"kind": "observed", "state": "ready",
                             "provider_session_id": PROVIDER,
                             "last_activity_at": NOW,
                             "diagnostics": {"claim_token": "anything"}})
        self.assertEqual(caught.exception.code, "secret-leak")
        self.assertIsNone(self.row("probe-1")["observation"])

    def test_a_diagnostic_name_is_bounded_like_its_value(self):
        """A bound on half of an entry is not a bound on the entry."""
        sound = dict(self.agent.probe_answer)
        self.agent.probe_answer = {
            **sound, "diagnostics": {"n" * 2_001: "short"}}
        with self.assertRaises(ContractRefusal) as caught:
            self.probing("probe-long-name")
        self.assertEqual(caught.exception.code, "limit")
        self.assertIn("diagnostic name", caught.exception.message)
        self.agent.probe_answer = {
            **sound, "diagnostics": {"n" * 2_000: "short"}}
        answer = self.probing("probe-exact-name")
        self.assertEqual(len(next(iter(answer["observation"]["diagnostics"]))),
                         2_000)

    def test_an_outcome_without_its_reading_is_refused_both_ways(self):
        """The pairing, as a rule rather than as a habit of the one caller.

        Re-review [P1] required the schema to reject an `observed` probe with
        no observation and an observation on any other outcome. Both are
        refused in this build's own vocabulary before the driver sees them, so
        a caller learns what is wrong instead of receiving an IntegrityError.
        """
        self.agent.failure = TimeoutError("the adapter never came back")
        with self.assertRaises(TimeoutError):
            self.probing()
        with self.assertRaises(ContractRefusal) as caught:
            settle_interrogation(self.store, operation_id="probe-1",
                                 outcome="observed")
        self.assertIn("nothing observed", caught.exception.message)
        with self.assertRaises(ContractRefusal) as caught:
            settle_interrogation(self.store, operation_id="probe-1",
                                 outcome="timed-out",
                                 observation=dict(self.agent.probe_answer))
        self.assertIn("carries no observation", caught.exception.message)
        self.assertEqual(self.row("probe-1")["outcome"], "requested")
        self.assertIsNone(self.row("probe-1")["observation"])

    def test_a_replayed_request_answers_with_the_first_deadline(self):
        """The other half of taking wall time out of the signature.

        The absolute deadline is the operation's committed RESULT, so the
        manager's FIRST observation is what every later caller sees. If the
        replay recomputed it, two callers would hold two deadlines for one
        journalled request and the later one would be the manager's own clock
        wearing the operation's identity.
        """
        first = self.probing()
        self.store._clock = lambda: LATER
        again = self.probing()
        self.assertEqual(again["deadline_at"], first["deadline_at"])
        self.assertEqual(again["requested_at"], first["requested_at"])
        self.assertEqual(len(self.agent.probed), 1,
                         "the retry asked the adapter a second time")

    def test_no_clock_is_read_before_the_journal_decides(self):
        """The correction, stated as the property rather than as one instant.

        A replay must not depend on the manager's current clock being usable
        at all — which is what an exact retry near the representable limit
        proves, and is why the arithmetic moved inside the transacted act.
        """
        first = self.probing()
        reads = []
        original = self.store._clock
        self.store._clock = lambda: (reads.append(1) or original())
        again = self.probing()
        self.assertEqual(reads, [], "the replay path read the clock")
        self.assertEqual(again["requested_at"], first["requested_at"])
        self.assertEqual(again["deadline_at"], first["deadline_at"])

    def test_nothing_mutable_is_consulted_before_the_journal_decides(self):
        """The property behind both of the last two corrections, stated once.

        A replay must depend on the journal and on durable state alone. The
        clock was the first mutable input to be moved inside the fresh act;
        the AUTHORITY was the second, and this counts BOTH — a replay reads
        neither.
        """
        self.probing()
        clock_reads, authority_reads = [], []
        original_clock = self.store._clock
        original_of = self.session.assignment_of
        self.store._clock = lambda: (clock_reads.append(1) or original_clock())
        self.session.assignment_of = (
            lambda *a, **k: (authority_reads.append(1) or original_of(*a, **k)))
        self.probing()
        self.assertEqual(clock_reads, [], "the replay path read the clock")
        self.assertEqual(authority_reads, [],
                         "the replay path asked Baton to re-decide")

    def test_replay_does_not_require_the_adapter_capabilities_to_still_exist(
            self):
        """The adapter is mutable too, and it is not a signed operand.

        A restart may have no reachable adapter at all. The already committed
        answer must still replay from the journal; inspecting today's adapter
        protocol before that decision makes historical success depend on a
        capability the replay promises not to use.
        """
        first = self.probing()

        class Gone:
            pass

        again = probe(
            self.store, self.port, Gone(), attempt_id=ATTEMPT,
            posture="execution", session_epoch=1, operation_id="probe-1",
            deadline_seconds=30)
        self.assertEqual(again, first)

    def test_a_fresh_interrogation_still_needs_the_live_generation(self):
        """The half the correction had to KEEP. Moving the authority read
        inside the fresh act must not stop it happening for a fresh
        request."""
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal) as caught:
            self.probing("probe-dead")
        self.assertEqual(caught.exception.category, "stale-assignment")
        self.assertIsNone(self.row("probe-dead"),
                          "a refused fresh request was journalled anyway")

    def test_a_different_duration_is_a_different_request(self):
        """The signature still carries what the CALLER asked for. Taking the
        derived instant out must not take the duration out with it — two
        different waits under one identity are two different requests."""
        self.probing()
        with self.assertRaises(ContractRefusal) as caught:
            self.probing(deadline_seconds=60)
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_an_inquiry_is_journalled_before_the_model_is_asked(self):
        """The same property for the conversational half: a crash between the
        two boundaries must be answerable, and an outcome column that only
        ever recorded settled requests could not say one was made."""
        self.agent.failure = TimeoutError("the adapter never came back")
        with self.assertRaises(TimeoutError):
            self.inquiring()
        row = self.row("inquire-1")
        self.assertEqual(row["outcome"], "requested")
        self.assertEqual(row["kind"], "inquire")


# -- the answer is a separate correlated fact --------------------------------

class TheAnswerIsSeparateAndCorrelated(InterrogationCase):

    def answered(self, body="it is going well"):
        self.inquiring()
        settle_interrogation(self.store, operation_id="inquire-1",
                             outcome="delivered")
        return record_inquiry_answer(self.store, operation_id="inquire-1",
                                     answer={"body": body})

    def test_an_answer_moves_the_outcome_and_is_journalled(self):
        settled = self.answered()
        self.assertEqual(settled["outcome"], "answered")
        self.assertEqual(json.loads(self.row("inquire-1")["answer"])["body"],
                         "it is going well")

    def test_a_probe_has_no_answer_to_record(self):
        self.probing()
        with self.assertRaises(ContractRefusal) as caught:
            record_inquiry_answer(self.store, operation_id="probe-1",
                                  answer={"body": "x"})
        self.assertIn("consumes no model turn", caught.exception.message)

    def test_the_store_refuses_a_probe_row_carrying_an_answer(self):
        self.probing()
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        with self.assertRaises(sqlite3.IntegrityError):
            beside.execute("UPDATE interrogations SET answer = '{}' "
                           "WHERE operation_id = 'probe-1'")

    def test_one_turn_answers_once(self):
        self.answered()
        again = record_inquiry_answer(self.store, operation_id="inquire-1",
                                      answer={"body": "it is going well"})
        self.assertEqual(again["outcome"], "answered")
        with self.assertRaises(ContractRefusal) as caught:
            record_inquiry_answer(self.store, operation_id="inquire-1",
                                  answer={"body": "actually, differently"})
        self.assertEqual(caught.exception.code, "already-terminal")

    def test_an_answer_body_is_bounded(self):
        self.inquiring()
        with self.assertRaises(ContractRefusal) as caught:
            record_inquiry_answer(self.store, operation_id="inquire-1",
                                  answer={"body": "x" * (MAX_ANSWER + 1)})
        self.assertEqual(caught.exception.code, "limit")

    def test_a_question_is_bounded_too(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.inquiring(question="x" * (MAX_QUESTION + 1))
        self.assertEqual(caught.exception.code, "limit")

    def test_an_answer_to_an_interrogation_nobody_journalled_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            record_inquiry_answer(self.store, operation_id="never-asked",
                                  answer={"body": "x"})
        self.assertEqual(caught.exception.code, "precondition")


# -- publication is the manager's, and it is a separate act ------------------

class TheManagerPublishesAndTheWorkerHoldsNothing(InterrogationCase):

    def test_the_manager_publishes_with_its_own_provenance(self):
        self.inquiring()
        settle_interrogation(self.store, operation_id="inquire-1",
                             outcome="delivered")
        record_inquiry_answer(self.store, operation_id="inquire-1",
                              answer={"body": "it is going well"})
        published = publish_inquiry_answer(self.store, self.port,
                                           operation_id="inquire-1")
        self.assertEqual(published["published_at"], NOW)
        self.assertEqual(len(self.session.published), 1)
        sent = self.session.published[0]
        self.assertEqual(sent["work_ref"],
                         {"authority_uuid": UUID, "work_id": WORK})
        self.assertEqual(sent["operation_id"], "inquire-1")
        self.assertEqual(sent["body"], "it is going well")

    def test_nothing_is_published_before_an_answer_exists(self):
        """Publishing what nobody answered would put this manager's own
        sentence into Baton wearing a model's provenance."""
        self.inquiring()
        with self.assertRaises(ContractRefusal) as caught:
            publish_inquiry_answer(self.store, self.port,
                                   operation_id="inquire-1")
        self.assertEqual(caught.exception.code, "precondition")
        self.assertEqual(self.session.published, [])

    def test_the_store_refuses_publication_without_an_answer(self):
        self.inquiring()
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        with self.assertRaises(sqlite3.IntegrityError):
            beside.execute("UPDATE interrogations SET published_at = ? "
                           "WHERE operation_id = 'inquire-1'", (NOW,))

    def test_publishing_twice_is_one_publication(self):
        self.inquiring()
        settle_interrogation(self.store, operation_id="inquire-1",
                             outcome="delivered")
        record_inquiry_answer(self.store, operation_id="inquire-1",
                              answer={"body": "done"})
        first = publish_inquiry_answer(self.store, self.port,
                                       operation_id="inquire-1")
        again = publish_inquiry_answer(self.store, self.port,
                                       operation_id="inquire-1")
        self.assertEqual(first["published_at"], again["published_at"])
        self.assertEqual(len(self.session.published), 1)

    def test_a_committed_baton_request_is_not_proof_the_model_saw_anything(
            self):
        """The ordering, asserted as a property: publication FOLLOWS an
        answer, so nothing in Baton can stand for a request the adapter or the
        model never received."""
        self.inquiring()
        row = self.row("inquire-1")
        self.assertEqual(row["outcome"], "queued")
        self.assertIsNone(row["answer"])
        self.assertIsNone(row["published_at"])
        self.assertEqual(self.session.published, [])

    def test_the_worker_receives_no_baton_or_sqlite_capability(self):
        """The requests this manager hands the adapter carry the session
        reference, the operation identity, the question and the deadline —
        and nothing that could reach an authority or a store."""
        self.probing()
        self.inquiring()
        for request in self.agent.probed + self.agent.inquired:
            flat = json.dumps(request, default=str)
            for forbidden in ("sqlite", "baton.json", "authority",
                              "connection", "session_capability", "bearer"):
                self.assertNotIn(forbidden, flat.lower(), request)
            self.assertTrue(
                set(request) <= {"runtime_attempt_id", "posture",
                                 "session_epoch", "provider_session_id",
                                 "operation_id", "question", "deadline_at"},
                sorted(request))


# -- restart --------------------------------------------------------------

class ARestartReadsTheLifecycleBack(InterrogationCase):

    def reopened(self):
        self.store.close()
        store = ControlStore.open(self.path, incarnation="manager-2",
                                  clock=lambda: LATER)
        self.addCleanup(store.close)
        return store

    def test_a_restart_between_enqueue_and_delivery_finds_the_request(self):
        self.inquiring()
        store = self.reopened()
        found = interrogation_of(store, "inquire-1")
        self.assertEqual(found["outcome"], "queued")
        self.assertEqual(found["assignment"]["generation"], 1)

    def test_a_restart_reads_a_probe_observation_not_only_its_outcome(self):
        first = self.probing()
        store = self.reopened()
        found = interrogation_of(store, "probe-1")
        self.assertEqual(found["outcome"], "observed")
        self.assertEqual(found["observation"], first["observation"])

    def test_a_restart_between_delivery_and_answer_finds_the_delivery(self):
        self.inquiring()
        settle_interrogation(self.store, operation_id="inquire-1",
                             outcome="delivered")
        store = self.reopened()
        self.assertEqual(interrogation_of(store, "inquire-1")["outcome"],
                         "delivered")

    def test_a_restart_between_answer_and_publication_finds_the_answer(self):
        self.inquiring()
        settle_interrogation(self.store, operation_id="inquire-1",
                             outcome="delivered")
        record_inquiry_answer(self.store, operation_id="inquire-1",
                              answer={"body": "done"})
        store = self.reopened()
        found = interrogation_of(store, "inquire-1")
        self.assertIs(found["answered"], True)
        self.assertIsNone(found["published_at"])
        published = publish_inquiry_answer(store, self.port,
                                           operation_id="inquire-1")
        self.assertEqual(published["published_at"], LATER)

    def test_an_absent_identity_is_absence_rather_than_an_error(self):
        self.assertIsNone(interrogation_of(self.store, "never-asked"))

    def test_one_session_lists_its_own_interrogations_in_order(self):
        self.probing()
        self.inquiring()
        found = interrogations_of(self.store, ATTEMPT, "execution", 1)
        self.assertEqual([entry["operation_id"] for entry in found],
                         ["inquire-1", "probe-1"])
        self.assertEqual([entry["kind"] for entry in found],
                         ["inquire", "probe"])


# -- the store carries what this build writes --------------------------------

class TheStoreKnowsItsOwnShape(InterrogationCase):

    def test_the_table_is_declared(self):
        self.assertIn("interrogations", schema.TABLES)

    def test_the_schema_version_moved_with_the_shape(self):
        """Past eight: a store written before the interrogation lifecycle
        existed cannot be adopted by a build that requires it."""
        self.assertGreater(schema.SCHEMA_VERSION, 8)

    def test_a_persisted_outcome_this_contract_never_had_is_refused(self):
        self.probing()
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        beside.execute("PRAGMA ignore_check_constraints = ON")
        beside.execute("UPDATE interrogations SET outcome = 'poked'")
        beside.close()
        with self.assertRaises(ContractRefusal) as caught:
            interrogation_of(self.store, "probe-1")
        self.assertEqual(caught.exception.code, "schema")


if __name__ == "__main__":
    unittest.main()
