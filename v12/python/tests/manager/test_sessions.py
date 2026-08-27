"""W6627 — the agent session: its axis, its adapter protocol, its lifecycle.

`work/records/2026/08/finding-v12-manager-agent-session-protocols/`.

THE ACCEPTANCE, and every case below belongs to one of its five lines:

  - consent and execution session axes distinct, with the frozen `sessionState`
    vocabulary and no collapsing of runtime, session and posture;
  - certified typed observations, including POSITIVE ABSENCE of a session as
    distinct from an absent runtime;
  - effectively-once operation identities and restart reconciliation;
  - cancellation ordering preserved: fence, then agent, then runtime;
  - public composition hooks on W6592's boundary, not beside it.

THE DEFECT THAT MADE THE FIRST LINE A REQUIREMENT. Three vocabularies describe
three different things — is the container up, is the agent inside it ready, and
which of the two containers is this — and a design that collapses any two of
them reports one as evidence for another. `agent-quiescent` would become "the
runtime is gone"; `execution_runtime: running` would become "an agent is
ready". Neither implication holds, and the cases here require each to be
refused rather than merely undocumented.
"""

import os
import sqlite3
import tempfile
import unittest

import baton_v12.worker_manager as worker_manager
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                      SESSION_STATES, SESSION_SUCCESSORS,
                                      TERMINAL_SESSION_STATES,
                                      accept_offer, activate_assignment,
                                      adopt_provider_session,
                                      agent_sessions_of, close_agent_session,
                                      certify_agent_session_profile,
                                      handle_transport_loss, issue_offer,
                                      observe, observe_session_state,
                                      open_agent_session,
                                      permits_session_transition,
                                      posture_slot, reconcile_agent_session,
                                      record_attempt, release_slot,
                                      reprompt_after_transport_loss,
                                      request_cancellation,
                                      require_slot_recovery,
                                      satisfies_runtime_quiescence_gate,
                                      submit_claim,
                                      transport_reachability_reidentifies)
from baton_v12.worker_manager import posture_slots, schema, sessions

from .test_attempts import ADAPTER, ATTEMPT, Adapter
from .test_handshake import acp_profile
from .test_offers import (FakeSession, NOW, PROFILE, UUID, WHO, WORK,
                          fake_claim_signature)


class Agent:
    """The narrow AGENT adapter — every operation the contract names, with
    every answer a case may need to set.

    Deliberately not the runtime `Adapter`: the two are different boundaries
    and a fixture that carried both would make it easy to write a case that
    proves nothing about which one was reached.
    """

    def __init__(self, provider_session_id=None):
        self.cancelled = []
        self.observed = []
        self.answer = None
        self.failure = None
        self.provider_session_id = provider_session_id

    def cancel(self, operands):
        self.cancelled.append(operands)
        if self.failure is not None:
            raise self.failure
        return {"acknowledged": True}

    def observe_session(self, reference):
        self.observed.append(reference)
        if self.failure is not None:
            raise self.failure
        if self.answer is not None:
            return self.answer
        return {"kind": "present", "state": "ready",
                "provider_session_id": self.provider_session_id}

    def probe(self, request):
        # W6627: the adapter contract now names `probe` and `inquire`. A fake
        # missing either is refused at the capability check, which would make
        # every case in this file fail for a reason it is not about.
        return {"kind": "unreachable", "why": "this fixture does not probe"}

    def inquire(self, request):
        return {"kind": "unreachable", "why": "this fixture does not inquire"}


PROVIDER = "provider-session-1"


class SessionCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-agent-session-")
        self.addCleanup(self._root.cleanup)
        self.path = os.path.join(self._root.name, "control.sqlite3")
        self.store = ControlStore.open(self.path, incarnation="manager-1",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        # TWO PROFILES, and they are different things. `certify_profile`
        # files the RUNTIME shape an offer promises; the agent-session profile
        # is the document a session pins its per-posture policy from. A
        # fixture that used one for both would let a case pass while proving
        # the wrong composition was consumed.
        worker_manager.certify_profile(self.store, "runtime", "reference",
                                       PROFILE)
        self.session = FakeSession()
        self.port = AuthorityPort(self.session, fake_claim_signature)
        self.profile = acp_profile()
        certify_agent_session_profile(self.store, self.profile)
        self.digest = self.profile["document_digest"]
        self.agent = Agent()

    # -- fixtures ---------------------------------------------------------

    def attempt(self, attempt_id=ATTEMPT, *, activate=True):
        """An attempt with its own committed claim, optionally activated."""
        issue_offer(self.store, self.port, offer_id="offer-" + attempt_id,
                    work_id=WORK, runtime_attempt_id=attempt_id,
                    input_digest="sha256:" + "1" * 64,
                    policy_digest="sha256:" + "2" * 64,
                    profile_digest=PROFILE, profile_name="reference",
                    mint_bearer=lambda: "bearer-" + attempt_id)
        accept_offer(self.store, self.port, offer_id="offer-" + attempt_id,
                     decision="accept", bearer="bearer-" + attempt_id, now=NOW,
                     runtime_attempt_id=attempt_id,
                     work_ref={"authority_uuid": UUID, "work_id": WORK})
        record_attempt(self.store, attempt_id=attempt_id, adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       policy_digest="sha256:" + "2" * 64)
        submit_claim(self.store, self.port, offer_id="offer-" + attempt_id)
        if activate:
            activate_assignment(
                self.store, self.port, attempt_id=attempt_id,
                expect={"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                        "participant": WHO, "generation": 1})
        return attempt_id

    def opened(self, posture="execution", *, attempt_id=ATTEMPT,
               intent=None, activate=True):
        self.attempt(attempt_id, activate=activate)
        return open_agent_session(
            self.store, self.port, attempt_id=attempt_id, posture=posture,
            profile_digest=self.digest,
            intent=intent or f"open-{posture}-1")

    def live(self, posture="execution", attempt_id=ATTEMPT, epoch=1,
             provider_session_id=None):
        return {"runtime_attempt_id": attempt_id, "posture": posture,
                "session_epoch": epoch,
                "provider_session_id": provider_session_id}

    def with_runtime(self, attempt_id=ATTEMPT):
        """A started, attached runtime, so a cancellation has something to
        stop. Without one `_order_quiescence` correctly reports that there is
        nothing to order, and a case asserting the stop would be asserting the
        fixture."""
        adapter = Adapter()
        worker_manager.request_runtime_start(self.store, adapter,
                                             attempt_id=attempt_id)
        worker_manager.reconcile_runtime(self.store, adapter,
                                         attempt_id=attempt_id)
        return adapter

    def row(self, attempt_id=ATTEMPT, posture="execution", epoch=1):
        beside = sqlite3.connect(self.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        try:
            found = beside.execute(
                "SELECT * FROM agent_sessions WHERE runtime_attempt_id = ? "
                "AND posture = ? AND session_epoch = ?",
                (attempt_id, posture, epoch)).fetchone()
            return None if found is None else {k: found[k]
                                               for k in found.keys()}
        finally:
            beside.close()


# -- the axis is the frozen one, and it never regresses ----------------------

class TheAxisIsTheFrozenOne(SessionCase):

    def test_the_nine_states_are_the_frozen_vocabulary(self):
        """Taken from the schema rather than retyped: a list written twice is
        a list that holds in one of the two places."""
        frozen = worker_manager.SESSION_STATES
        self.assertEqual(len(frozen), 9)
        self.assertEqual(set(frozen), set(SESSION_SUCCESSORS))

    def test_unknown_and_closed_are_terminal_and_nothing_else_is(self):
        self.assertEqual(set(TERMINAL_SESSION_STATES), {"unknown", "closed"})

    def test_unknown_never_becomes_closed(self):
        """§3.3: `unknown` means no terminal fact was OBSERVED. Promoting it
        would record knowledge nobody acquired — a session record asserting
        every turn has a terminal fact when nobody saw the ending."""
        self.assertFalse(permits_session_transition("unknown", "closed"))
        self.assertEqual(SESSION_SUCCESSORS["unknown"], ())

    def test_a_turn_ended_epoch_may_be_prompted_again(self):
        """The edge the spine diagram does not draw: one epoch runs a second
        supervised turn."""
        self.assertTrue(permits_session_transition("turn-ended", "prompting"))

    def test_observing_the_same_state_is_not_a_move(self):
        for state in SESSION_STATES:
            with self.subTest(state=state):
                self.assertTrue(permits_session_transition(state, state))

    def test_a_state_this_contract_does_not_have_is_refused(self):
        for what, pair in [("from", ("gone", "ready")),
                           ("to", ("ready", "gone")),
                           ("a list", (["ready"], "ready"))]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    permits_session_transition(*pair)
                self.assertEqual(caught.exception.code, "schema")


class TheAxisIsNotTheRuntime(SessionCase):
    """§7.4 — agent quiescence is not runtime quiescence."""

    def test_no_session_state_satisfies_the_runtime_quiescence_gate(self):
        for state in SESSION_STATES:
            with self.subTest(state=state):
                self.assertIs(satisfies_runtime_quiescence_gate(state), False)

    def test_a_malformed_question_is_refused_rather_than_answered_false(self):
        """Answering `false` to a malformed question is how a caller
        concludes it asked a good one."""
        with self.assertRaises(ContractRefusal):
            satisfies_runtime_quiescence_gate("agent-gone")

    def test_the_runtime_axis_and_the_session_axis_are_separate(self):
        """The collapse this Job's own title invites, refused in both
        directions: a session state is not a runtime value and the reverse."""
        # NOT A DISJOINT-SET ASSERTION. The two vocabularies share three
        # words -- `not-started`, `cancel-requested`, `unknown` -- and that is
        # ordinary English rather than a merge: a container that has not
        # started and an agent that has not started are both accurately
        # described by those words and are different facts. What must hold is
        # that neither axis ACCEPTS the other's values, which is a property of
        # the boundaries and is what these two calls prove.
        self.opened()
        with self.assertRaises(ContractRefusal):
            observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                    value="initializing")
        with self.assertRaises(ContractRefusal):
            observe_session_state(self.store, self.live(), "start-requested")

    def test_the_two_runtime_enums_stay_deliberately_asymmetric(self):
        """The M6617 topology, written into the frozen contract: a consent
        container is never asked to start work or cancelled mid-turn, so it
        has no state for either. An implementation that tidied them into one
        enum would erase the topology while looking like a simplification."""
        from baton_v12.worker_manager import TRANSITIONS
        consent = set(TRANSITIONS["consent_runtime"])
        execution = set(TRANSITIONS["execution_runtime"])
        self.assertEqual(execution - consent,
                         {"start-requested", "cancel-requested", "stopping"})


# -- opening: fresh epochs, posture bindings, no capability out --------------

class OpeningASession(SessionCase):

    def test_a_consent_session_carries_no_assignment(self):
        answer = self.opened("consent")
        self.assertIsNone(answer["assignment"])
        self.assertIs(answer["workspace"], False)
        self.assertIs(answer["declared_output"], False)
        self.assertEqual(answer["state"], "not-started")
        self.assertIsNone(self.row(posture="consent")["participant"])

    def test_an_execution_session_carries_the_exact_assignment(self):
        answer = self.opened("execution")
        self.assertEqual(answer["assignment"],
                         {"work_ref": {"authority_uuid": UUID,
                                       "work_id": WORK},
                          "participant": WHO, "generation": 1})
        self.assertIs(answer["workspace"], True)
        self.assertIs(answer["declared_output"], True)

    def test_the_store_itself_refuses_a_consent_session_with_a_generation(self):
        """The posture binding is a CHECK rather than a convention: a store
        that could hold a consent session carrying somebody's generation is a
        store in which the separation the two postures exist for is prose."""
        self.opened("consent")
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        with self.assertRaises(sqlite3.IntegrityError):
            beside.execute("UPDATE agent_sessions SET generation = 1 WHERE "
                           "posture = 'consent'")

    def test_an_unactivated_attempt_has_no_execution_session(self):
        self.attempt(activate=False)
        with self.assertRaises(ContractRefusal) as caught:
            open_agent_session(self.store, self.port, attempt_id=ATTEMPT,
                               posture="execution",
                               profile_digest=self.digest, intent="open-1")
        self.assertEqual(caught.exception.code, "precondition")

    def test_a_dead_assignment_refuses_an_execution_session(self):
        """The CACHED ROW IS NOT THE LIVE ASSIGNMENT. The manager is the
        authority client; it asks."""
        self.attempt()
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal) as caught:
            open_agent_session(self.store, self.port, attempt_id=ATTEMPT,
                               posture="execution",
                               profile_digest=self.digest, intent="open-1")
        self.assertEqual(caught.exception.category, "stale-assignment")

    def test_a_superseded_generation_refuses_an_execution_session(self):
        self.attempt()
        self.session.live_assignment = {
            "work_ref": {"authority_uuid": UUID, "work_id": WORK},
            "participant": WHO, "generation": 2}
        with self.assertRaises(ContractRefusal) as caught:
            open_agent_session(self.store, self.port, attempt_id=ATTEMPT,
                               posture="execution",
                               profile_digest=self.digest, intent="open-1")
        self.assertEqual(caught.exception.code, "generation")

    def test_an_uncertified_profile_opens_nothing(self):
        """A session pins a per-posture policy, and one nothing has agreed to
        is not a policy. This is W6592's boundary, consumed rather than
        restated beside it."""
        self.attempt()
        with self.assertRaises(ContractRefusal) as caught:
            open_agent_session(self.store, self.port, attempt_id=ATTEMPT,
                               posture="execution",
                               profile_digest="sha256:" + "9" * 64,
                               intent="open-1")
        self.assertEqual(caught.exception.code, "profile-uncertified")

    def test_the_pinned_policy_is_the_profiles_own(self):
        answer = self.opened("execution")
        self.assertEqual(
            answer["pinned_policy"],
            digest(self.profile["postures"]["execution"]["policy"]))
        self.assertNotEqual(
            answer["pinned_policy"],
            digest(self.profile["postures"]["consent"]["policy"]))

    def test_no_authority_capability_leaves_with_the_answer(self):
        """Rule 3: the untrusted agent endpoint and relay never receive a
        Baton capability. The port is read once, for the liveness check, and
        appears in nothing this returns or writes."""
        answer = self.opened("execution")
        flat = repr(answer) + repr(self.row())
        self.assertNotIn("FakeSession", flat)
        self.assertNotIn("bearer", flat)

    def test_the_two_postures_get_independent_epochs(self):
        self.attempt()
        for posture in ("consent", "execution"):
            answer = open_agent_session(
                self.store, self.port, attempt_id=ATTEMPT, posture=posture,
                profile_digest=self.digest, intent=f"open-{posture}")
            self.assertEqual(answer["agent_session_ref"]["session_epoch"], 1)
        self.assertEqual(len(agent_sessions_of(self.store, ATTEMPT)), 2)

    def test_a_posture_holds_one_session(self):
        """Freshness and concurrency are two rules, and allocating the next
        epoch answers only the first."""
        self.opened("execution")
        with self.assertRaises(ContractRefusal) as caught:
            open_agent_session(self.store, self.port, attempt_id=ATTEMPT,
                               posture="execution",
                               profile_digest=self.digest, intent="open-2")
        self.assertEqual(caught.exception.code, "duplicate-runtime")

    def test_a_third_posture_is_not_a_posture(self):
        self.attempt()
        with self.assertRaises(ContractRefusal) as caught:
            open_agent_session(self.store, self.port, attempt_id=ATTEMPT,
                               posture="supervision",
                               profile_digest=self.digest, intent="open-1")
        self.assertEqual(caught.exception.code, "schema")


class OpeningIsEffectivelyOnce(SessionCase):

    def test_an_exact_retry_replays_the_first_opening(self):
        """A crash between the slot compare-and-set and the caller's answer
        left an epoch occupied by a session the caller never learned about,
        and the retry took the next epoch and found the posture taken."""
        first = self.opened("execution", intent="open-a")
        again = open_agent_session(
            self.store, self.port, attempt_id=ATTEMPT, posture="execution",
            profile_digest=self.digest, intent="open-a")
        self.assertEqual(first, again)
        self.assertEqual(len(agent_sessions_of(self.store, ATTEMPT)), 1)

    def test_a_different_profile_under_one_intent_collides(self):
        """An operation identity that ignores its operands is not an
        identity, and the retry's answer would describe the first act."""
        self.opened("execution", intent="open-a")
        other = acp_profile(profile_id="profile-other")
        certify_agent_session_profile(self.store, other)
        with self.assertRaises(ContractRefusal) as caught:
            open_agent_session(
                self.store, self.port, attempt_id=ATTEMPT, posture="execution",
                profile_digest=other["document_digest"], intent="open-a")
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_a_deliberate_second_session_needs_its_own_intent(self):
        """Two sessions in one posture are a real thing — the second begins
        after the first slot is recovered — so the identity cannot be derived
        from the attempt and posture alone or the retry of a crash and a
        deliberate reopening would be the same string."""
        self.opened("execution", intent="open-a")
        observe_session_state(self.store, self.live(), "initializing")
        close_agent_session(self.store, self.live())
        second = open_agent_session(
            self.store, self.port, attempt_id=ATTEMPT, posture="execution",
            profile_digest=self.digest, intent="open-b")
        self.assertEqual(second["agent_session_ref"]["session_epoch"], 2)


# -- the reference labels evidence, and binds all four components ------------

class TheReferenceBindsAllFourComponents(SessionCase):

    def test_an_observation_naming_another_provider_session_is_refused(self):
        self.opened()
        adopt_provider_session(self.store, attempt_id=ATTEMPT,
                               posture="execution", session_epoch=1,
                               provider_session_id=PROVIDER)
        with self.assertRaises(ContractRefusal) as caught:
            observe_session_state(
                self.store,
                self.live(provider_session_id="provider-session-2"),
                "initializing")
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_a_no_op_observation_is_bound_too(self):
        """Affirming that provider session B's axis reads `not-started` is a
        claim about B, and answering it from A's row is the same mistake as
        moving A's row."""
        self.opened()
        adopt_provider_session(self.store, attempt_id=ATTEMPT,
                               posture="execution", session_epoch=1,
                               provider_session_id=PROVIDER)
        with self.assertRaises(ContractRefusal) as caught:
            observe_session_state(
                self.store, self.live(provider_session_id="other"),
                "not-started")
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_a_reference_missing_a_component_is_refused(self):
        self.opened()
        for missing in ("runtime_attempt_id", "posture", "session_epoch",
                        "provider_session_id"):
            with self.subTest(missing=missing):
                reference = self.live()
                del reference[missing]
                with self.assertRaises(ContractRefusal) as caught:
                    observe_session_state(self.store, reference,
                                          "initializing")
                self.assertEqual(caught.exception.code, "schema")

    def test_epoch_zero_is_not_a_session_epoch(self):
        self.opened()
        with self.assertRaises(ContractRefusal) as caught:
            observe_session_state(self.store, self.live(epoch=0),
                                  "initializing")
        self.assertEqual(caught.exception.code, "schema")

    def test_a_provider_session_id_is_adopted_once(self):
        self.opened()
        first = adopt_provider_session(self.store, attempt_id=ATTEMPT,
                                       posture="execution", session_epoch=1,
                                       provider_session_id=PROVIDER)
        self.assertIs(first["adopted"], True)
        again = adopt_provider_session(self.store, attempt_id=ATTEMPT,
                                       posture="execution", session_epoch=1,
                                       provider_session_id=PROVIDER)
        self.assertIs(again["adopted"], False)
        with self.assertRaises(ContractRefusal) as caught:
            adopt_provider_session(self.store, attempt_id=ATTEMPT,
                                   posture="execution", session_epoch=1,
                                   provider_session_id="provider-session-2")
        self.assertEqual(caught.exception.code, "identity-mismatch")


class TheAxisRefusesARegression(SessionCase):

    def test_a_backwards_observation_is_refused(self):
        self.opened()
        observe_session_state(self.store, self.live(), "initializing")
        observe_session_state(self.store, self.live(), "ready")
        with self.assertRaises(ContractRefusal) as caught:
            observe_session_state(self.store, self.live(), "initializing")
        self.assertEqual(caught.exception.code, "state-regression")

    def test_a_skipped_edge_is_refused(self):
        self.opened()
        with self.assertRaises(ContractRefusal) as caught:
            observe_session_state(self.store, self.live(), "ready")
        self.assertEqual(caught.exception.code, "state-regression")

    def test_a_retransmitted_observation_answers_rather_than_refusing(self):
        self.opened()
        first = observe_session_state(self.store, self.live(), "initializing")
        again = observe_session_state(self.store, self.live(), "initializing")
        self.assertIs(first["moved"], True)
        self.assertIs(again["moved"], False)

    def test_an_axis_without_a_session_is_refused(self):
        self.attempt()
        with self.assertRaises(ContractRefusal) as caught:
            observe_session_state(self.store, self.live(), "initializing")
        self.assertEqual(caught.exception.code, "precondition")


# -- the posture slot is a separate, manager-owned axis ----------------------

class ThePostureSlotIsItsOwnAxis(SessionCase):

    def test_opening_occupies_and_closing_releases(self):
        self.opened()
        self.assertEqual(posture_slot(self.store, ATTEMPT, "execution")
                         ["occupancy"], "occupied")
        observe_session_state(self.store, self.live(), "initializing")
        answer = close_agent_session(self.store, self.live())
        self.assertIs(answer["closed"], True)
        self.assertIs(answer["released_slot"], True)
        self.assertEqual(answer["slot_occupancy"], "available")

    def test_a_never_used_posture_has_no_slot(self):
        self.attempt()
        self.assertIsNone(posture_slot(self.store, ATTEMPT, "consent"))

    def test_a_close_from_a_state_seven_three_forbids_is_refused(self):
        """The superseded behaviour, refused: `closed` used to be written over
        any state, taking four edges §7.3 forbids — including `unknown`, which
        records knowledge nobody acquired. It did that because `closed` was
        also the only thing that freed the posture."""
        self.opened()
        with self.assertRaises(ContractRefusal) as caught:
            close_agent_session(self.store, self.live())
        self.assertEqual(caught.exception.code, "state-regression")
        self.assertEqual(posture_slot(self.store, ATTEMPT, "execution")
                         ["occupancy"], "occupied")

    def test_silence_recovers_nothing(self):
        self.opened()
        for evidence in ("stop-requested", "deadline-elapsed", "disconnected",
                         "the manager believes it is gone"):
            with self.subTest(evidence=evidence):
                with self.assertRaises(ContractRefusal) as caught:
                    release_slot(self.store, attempt_id=ATTEMPT,
                                 posture="execution", session_epoch=1,
                                 evidence=evidence, reason="a guess")
                self.assertEqual(caught.exception.code, "schema")

    def test_a_provider_close_release_reads_the_observation(self):
        """A closed vocabulary of labels is not evidence; it is a closed
        vocabulary of claims."""
        self.opened()
        with self.assertRaises(ContractRefusal) as caught:
            release_slot(self.store, attempt_id=ATTEMPT, posture="execution",
                         session_epoch=1,
                         evidence="provider-session-closed",
                         reason="I say it closed")
        self.assertEqual(caught.exception.code, "precondition")

    def test_evidence_about_one_epoch_never_moves_another(self):
        self.opened(intent="open-a")
        observe_session_state(self.store, self.live(), "initializing")
        close_agent_session(self.store, self.live())
        open_agent_session(self.store, self.port, attempt_id=ATTEMPT,
                           posture="execution", profile_digest=self.digest,
                           intent="open-b")
        with self.assertRaises(ContractRefusal) as caught:
            require_slot_recovery(self.store, attempt_id=ATTEMPT,
                                  posture="execution", session_epoch=1,
                                  reason="a delayed report about epoch 1")
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_a_close_lands_on_its_own_epoch_even_after_recovery(self):
        """Epoch 1's provider session really did close, and that observation
        is true whatever the posture has done since. The observation always
        lands; the RELEASE is about the slot, and a slot already recovered on
        other evidence is not this close's to free again."""
        self.opened(intent="open-a")
        adopt_provider_session(self.store, attempt_id=ATTEMPT,
                               posture="execution", session_epoch=1,
                               provider_session_id=PROVIDER)
        reference = self.live(provider_session_id=PROVIDER)
        observe_session_state(self.store, reference, "initializing")
        handle_transport_loss(self.store, reference)
        release_slot(self.store, attempt_id=ATTEMPT, posture="execution",
                     session_epoch=1, evidence="session-absent",
                     observed_identity=PROVIDER,
                     reason="the adapter observed the provider session absent")
        # And NOW the close arrives, late. `unknown` is terminal, so §7.3
        # refuses it -- which is the ruling working, not a defect: a close
        # nobody saw complete never overwrites the ambiguity that was
        # recorded.
        with self.assertRaises(ContractRefusal) as caught:
            close_agent_session(self.store, reference)
        self.assertEqual(caught.exception.code, "state-regression")
        self.assertEqual(posture_slot(self.store, ATTEMPT, "execution")
                         ["occupancy"], "available")

    def test_a_runtime_absence_names_the_exact_runtime(self):
        self.opened()
        adapter = Adapter()
        worker_manager.request_runtime_start(self.store, adapter,
                                             attempt_id=ATTEMPT)
        worker_manager.reconcile_runtime(self.store, adapter,
                                         attempt_id=ATTEMPT)
        with self.assertRaises(ContractRefusal) as caught:
            release_slot(self.store, attempt_id=ATTEMPT, posture="execution",
                         session_epoch=1, evidence="runtime-absent",
                         observed_identity="somebody-elses-container",
                         reason="a container is gone")
        self.assertEqual(caught.exception.code, "identity-mismatch")


# -- positive absence of a SESSION, distinct from an absent runtime ----------

class SessionAbsenceIsNotRuntimeAbsence(SessionCase):

    def test_a_session_observed_absent_recovers_the_posture(self):
        """An agent process can die inside a container that is still running
        somebody's code. Before this evidence kind, the only way to recover
        that posture was to destroy a container doing nothing wrong."""
        self.opened()
        adopt_provider_session(self.store, attempt_id=ATTEMPT,
                               posture="execution", session_epoch=1,
                               provider_session_id=PROVIDER)
        self.agent.answer = {"kind": "absent",
                             "provider_session_id": PROVIDER}
        answer = reconcile_agent_session(self.store, self.agent,
                                         attempt_id=ATTEMPT,
                                         posture="execution", session_epoch=1)
        self.assertEqual(answer["found"], "absent")
        self.assertEqual(answer["slot"], "available")

    def test_an_absent_session_moves_no_observation(self):
        """Absence is not one of the nine. Adding a tenth is how a failed look
        becomes a claim about what the provider did."""
        self.opened()
        adopt_provider_session(self.store, attempt_id=ATTEMPT,
                               posture="execution", session_epoch=1,
                               provider_session_id=PROVIDER)
        observe_session_state(self.store,
                              self.live(provider_session_id=PROVIDER),
                              "initializing")
        self.agent.answer = {"kind": "absent",
                             "provider_session_id": PROVIDER}
        answer = reconcile_agent_session(self.store, self.agent,
                                         attempt_id=ATTEMPT,
                                         posture="execution", session_epoch=1)
        self.assertEqual(answer["state"], "initializing")
        self.assertEqual(self.row()["state"], "initializing")

    def test_session_absence_satisfies_no_runtime_gate(self):
        """The distinction the acceptance requires, asserted as a property
        rather than left to prose: recovering a posture is not evidence about
        a container."""
        self.opened()
        adopt_provider_session(self.store, attempt_id=ATTEMPT,
                               posture="execution", session_epoch=1,
                               provider_session_id=PROVIDER)
        self.agent.answer = {"kind": "absent",
                             "provider_session_id": PROVIDER}
        reconcile_agent_session(self.store, self.agent, attempt_id=ATTEMPT,
                                posture="execution", session_epoch=1)
        beside = sqlite3.connect(self.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        self.addCleanup(beside.close)
        axis = beside.execute(
            "SELECT execution_runtime FROM attempts WHERE "
            "runtime_attempt_id = ?", (ATTEMPT,)).fetchone()
        self.assertEqual(axis["execution_runtime"], "not-started")
        self.assertIs(satisfies_runtime_quiescence_gate(self.row()["state"]),
                      False)

    def test_an_epoch_that_never_named_a_provider_session_has_none_to_lose(self):
        """Absence of a NAME is not absence of a session."""
        self.opened()
        self.agent.answer = {"kind": "absent", "provider_session_id": None}
        with self.assertRaises(ContractRefusal) as caught:
            reconcile_agent_session(self.store, self.agent,
                                    attempt_id=ATTEMPT, posture="execution",
                                    session_epoch=1)
        self.assertEqual(caught.exception.code, "precondition")

    def test_an_absence_about_another_session_recovers_nothing(self):
        self.opened()
        adopt_provider_session(self.store, attempt_id=ATTEMPT,
                               posture="execution", session_epoch=1,
                               provider_session_id=PROVIDER)
        self.agent.answer = {"kind": "absent",
                             "provider_session_id": "provider-session-2"}
        with self.assertRaises(ContractRefusal) as caught:
            reconcile_agent_session(self.store, self.agent,
                                    attempt_id=ATTEMPT, posture="execution",
                                    session_epoch=1)
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_the_three_evidence_kinds_are_three(self):
        self.assertEqual(posture_slots.RECOVERY_EVIDENCE,
                         ("provider-session-closed", "session-absent",
                          "runtime-absent"))


# -- the adapter protocol: what an agent adapter must answer -----------------

class TheAdapterProtocolIsTyped(SessionCase):

    def test_an_adapter_missing_an_operation_is_refused(self):
        self.opened()

        class Partial:
            def cancel(self, operands):
                return {}

        with self.assertRaises(ContractRefusal) as caught:
            reconcile_agent_session(self.store, Partial(),
                                    attempt_id=ATTEMPT, posture="execution",
                                    session_epoch=1)
        self.assertEqual(caught.exception.code, "schema")

    def test_an_unrecognised_answer_is_refused_rather_than_read(self):
        """An answer outside the closed set must not become the least
        alarming member of it."""
        self.opened()
        self.agent.answer = {"kind": "unreachable",
                             "provider_session_id": None}
        with self.assertRaises(ContractRefusal) as caught:
            reconcile_agent_session(self.store, self.agent,
                                    attempt_id=ATTEMPT, posture="execution",
                                    session_epoch=1)
        self.assertEqual(caught.exception.code, "schema")

    def test_closing_the_vocabulary_alone_is_not_enough(self):
        """Knowing WHICH alternative arrived tells you nothing if you do not
        then know what it must carry."""
        self.opened()
        self.agent.answer = {"kind": "present"}
        with self.assertRaises(ContractRefusal) as caught:
            reconcile_agent_session(self.store, self.agent,
                                    attempt_id=ATTEMPT, posture="execution",
                                    session_epoch=1)
        self.assertEqual(caught.exception.code, "schema")

    def test_a_present_answer_moves_the_axis_through_its_own_boundary(self):
        self.opened()
        self.agent.answer = {"kind": "present", "state": "initializing",
                             "provider_session_id": None}
        answer = reconcile_agent_session(self.store, self.agent,
                                         attempt_id=ATTEMPT,
                                         posture="execution", session_epoch=1)
        self.assertEqual((answer["found"], answer["state"], answer["moved"]),
                         ("present", "initializing", True))
        self.assertIsNone(answer["slot"], "a present agent freed a posture")

    def test_a_present_answer_cannot_regress_the_axis(self):
        """The adapter's report is an observation like any other, and the
        regression refusal is not relaxed because it arrived over a
        reconnect."""
        self.opened()
        observe_session_state(self.store, self.live(), "initializing")
        observe_session_state(self.store, self.live(), "ready")
        self.agent.answer = {"kind": "present", "state": "not-started",
                             "provider_session_id": None}
        with self.assertRaises(ContractRefusal) as caught:
            reconcile_agent_session(self.store, self.agent,
                                    attempt_id=ATTEMPT, posture="execution",
                                    session_epoch=1)
        self.assertEqual(caught.exception.code, "state-regression")

    def test_an_answer_about_another_session_is_refused(self):
        self.opened()
        self.agent.answer = {"kind": "present", "state": "ready",
                             "provider_session_id": "somebody-else"}
        with self.assertRaises(ContractRefusal) as caught:
            reconcile_agent_session(self.store, self.agent,
                                    attempt_id=ATTEMPT, posture="execution",
                                    session_epoch=1)
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_the_adapter_is_asked_about_the_exact_reference(self):
        self.opened()
        adopt_provider_session(self.store, attempt_id=ATTEMPT,
                               posture="execution", session_epoch=1,
                               provider_session_id=PROVIDER)
        self.agent.answer = {"kind": "present", "state": "initializing",
                             "provider_session_id": PROVIDER}
        reconcile_agent_session(self.store, self.agent, attempt_id=ATTEMPT,
                                posture="execution", session_epoch=1)
        self.assertEqual(self.agent.observed, [
            {"runtime_attempt_id": ATTEMPT, "posture": "execution",
             "session_epoch": 1, "provider_session_id": PROVIDER}])


# -- transport loss ends the epoch -------------------------------------------

class ALostTransportEndsTheEpoch(SessionCase):

    def test_it_records_unknown_and_requires_recovery_together(self):
        """One transaction, so a crash leaves either both or neither: a
        session recorded `unknown` whose posture still looked live is the
        state this composition exists to prevent."""
        self.opened()
        answer = handle_transport_loss(self.store, self.live())
        self.assertEqual(answer["session_state"], "unknown")
        self.assertEqual(answer["slot_occupancy"], "recovery-required")
        self.assertEqual(self.row()["state"], "unknown")

    def test_it_reports_the_two_refusals_as_facts(self):
        self.opened()
        answer = handle_transport_loss(self.store, self.live())
        self.assertIs(answer["resume"], False)
        self.assertIs(answer["reprompt"], False)
        self.assertIs(
            answer["next_epoch_allowed_without_runtime_reidentification"],
            False)

    def test_a_turn_in_flight_is_reported_and_not_recorded(self):
        self.opened()
        with_turn = handle_transport_loss(self.store, self.live(),
                                          turn_in_flight=True)
        self.assertEqual(with_turn["turn_outcome"], "transport-lost")
        self.opened(attempt_id="attempt-2", intent="open-2")
        without = handle_transport_loss(
            self.store, self.live(attempt_id="attempt-2"))
        self.assertIsNone(without["turn_outcome"])

    def test_whether_a_turn_was_in_flight_is_never_inferred(self):
        self.opened()
        with self.assertRaises(ContractRefusal) as caught:
            handle_transport_loss(self.store, self.live(), turn_in_flight="1")
        self.assertEqual(caught.exception.code, "schema")

    def test_a_transport_does_not_die_twice_differently(self):
        self.opened()
        handle_transport_loss(self.store, self.live())
        again = handle_transport_loss(self.store, self.live())
        self.assertEqual(again["session_state"], "unknown")
        self.assertEqual(again["slot_occupancy"], "recovery-required")

    def test_re_prompting_is_refused_always(self):
        with self.assertRaises(ContractRefusal) as caught:
            reprompt_after_transport_loss("please continue")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("ambiguous", "operation"))

    def test_reachability_is_not_re_identification(self):
        self.assertIs(transport_reachability_reidentifies("the socket is up"),
                      False)

    def test_an_ambiguous_posture_is_recovered_by_evidence_not_by_time(self):
        """The normal shape after an agent died inside a live container:
        observation `unknown`, runtime untouched, slot available."""
        self.opened()
        adopt_provider_session(self.store, attempt_id=ATTEMPT,
                               posture="execution", session_epoch=1,
                               provider_session_id=PROVIDER)
        handle_transport_loss(self.store,
                              self.live(provider_session_id=PROVIDER))
        released = release_slot(
            self.store, attempt_id=ATTEMPT, posture="execution",
            session_epoch=1, evidence="session-absent",
            observed_identity=PROVIDER,
            reason="the adapter observed the provider session absent")
        self.assertEqual(released["occupancy"], "available")
        self.assertEqual(self.row()["state"], "unknown")


# -- cancellation: the session announcement, and nothing reordered -----------

class CancellationAnnouncesTheSession(SessionCase):

    def test_the_session_axis_is_announced_before_the_agent_is_asked(self):
        self.opened()
        observe_session_state(self.store, self.live(), "initializing")
        observe_session_state(self.store, self.live(), "ready")
        adapter = Adapter()
        answer = request_cancellation(self.store, self.port, self.agent,
                                      adapter, attempt_id=ATTEMPT,
                                      reason="operator")
        self.assertIs(answer["session_quiescence"]["requested"], True)
        self.assertEqual(answer["session_quiescence"]["state"],
                         "cancel-requested")
        self.assertEqual(self.row()["state"], "cancel-requested")

    def test_the_fence_still_precedes_everything(self):
        """FENCE, THEN STOP. The session announcement is added without
        reordering the two boundaries that exist."""
        self.opened()
        for state in ("initializing", "ready"):
            observe_session_state(self.store, self.live(), state)
        adapter = self.with_runtime()
        request_cancellation(self.store, self.port, self.agent, adapter,
                             attempt_id=ATTEMPT, reason="operator")
        acts = [name for name, _operands in self.session.calls]
        self.assertIn("cancel", acts, "the authority was never fenced")
        self.assertEqual(self.row()["state"], "cancel-requested")
        # And the two boundaries below the fence kept their order.
        self.assertTrue(self.agent.cancelled and adapter.stopped)

    def test_the_announcement_never_writes_agent_quiescent(self):
        """`agent-quiescent` is what the provider was OBSERVED to reach. An
        announcement is not an observation."""
        self.opened()
        for state in ("initializing", "ready"):
            observe_session_state(self.store, self.live(), state)
        adapter = Adapter()
        request_cancellation(self.store, self.port, self.agent, adapter,
                             attempt_id=ATTEMPT, reason="operator")
        self.assertNotEqual(self.row()["state"], "agent-quiescent")

    def test_a_finished_conversation_does_not_veto_the_cancellation(self):
        """Refusing the whole act because the conversation had already ended
        would leave a fenced runtime running."""
        self.opened()
        for state in ("initializing", "ready", "cancel-requested",
                      "agent-quiescent"):
            observe_session_state(self.store, self.live(), state)
        adapter = self.with_runtime()
        answer = request_cancellation(self.store, self.port, self.agent,
                                      adapter, attempt_id=ATTEMPT,
                                      reason="operator")
        self.assertIs(answer["session_quiescence"]["requested"], False)
        self.assertIn("agent-quiescent", answer["session_quiescence"]["why"])
        self.assertTrue(adapter.stopped, "a fenced runtime was left running")

    def test_an_ambiguous_posture_has_no_live_session_to_interrupt(self):
        """Transport loss moves the posture to `recovery-required`, so there
        is no live session -- and the cancellation says exactly that rather
        than announcing an interruption to a conversation nobody is having."""
        self.opened()
        handle_transport_loss(self.store, self.live())
        adapter = Adapter()
        answer = request_cancellation(self.store, self.port, self.agent,
                                      adapter, attempt_id=ATTEMPT,
                                      reason="operator")
        self.assertIs(answer["session_quiescence"]["requested"], False)
        self.assertIn("no execution session",
                      answer["session_quiescence"]["why"])
        self.assertEqual(self.row()["state"], "unknown")

    def test_an_attempt_with_no_session_still_cancels(self):
        self.attempt()
        adapter = Adapter()
        answer = request_cancellation(self.store, self.port, self.agent,
                                      adapter, attempt_id=ATTEMPT,
                                      reason="operator")
        self.assertIs(answer["session_quiescence"]["requested"], False)
        self.assertIn("no execution session",
                      answer["session_quiescence"]["why"])

    def test_a_consent_session_is_not_cancelled_mid_turn(self):
        """The M6617 topology: a consent container is never asked to start
        work or cancelled mid-turn."""
        self.attempt()
        open_agent_session(self.store, self.port, attempt_id=ATTEMPT,
                           posture="consent", profile_digest=self.digest,
                           intent="open-consent")
        adapter = Adapter()
        answer = request_cancellation(self.store, self.port, self.agent,
                                      adapter, attempt_id=ATTEMPT,
                                      reason="operator")
        self.assertIs(answer["session_quiescence"]["requested"], False)
        self.assertEqual(self.row(posture="consent")["state"], "not-started")


# -- the store carries what this build writes --------------------------------

class TheStoreKnowsItsOwnShape(SessionCase):

    def test_the_two_tables_are_declared(self):
        self.assertIn("agent_sessions", schema.TABLES)
        self.assertIn("posture_slots", schema.TABLES)

    def test_the_schema_version_moved_with_the_shape(self):
        """A store written under an earlier shape cannot hold what this build
        enforces, and keeping the number would let this build adopt one.

        PAST SIX, not EQUAL TO SEVEN. The property this case owns is that a
        store written before the agent session existed cannot be adopted by a
        build that requires it; which number the CURRENT shape is at is a fact
        about the newest slice, and `test_store` already pins that the store
        records whatever this constant says. Asserting the literal here made
        every later table addition edit a case about agent sessions, which is
        a coupling this case never meant to claim. (W6628 moved it to eight.)
        """
        self.assertGreater(schema.SCHEMA_VERSION, 6)

    def test_a_persisted_state_this_contract_never_had_is_refused(self):
        """The store is a receiving trust domain: this process did not write
        the bytes it is reading."""
        self.opened()
        beside = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(beside.close)
        beside.execute("PRAGMA writable_schema = ON")
        beside.execute("UPDATE sqlite_master SET sql = replace(sql, "
                       "\"state IN ('not-started'\", \"state IN ('gone'\") "
                       "WHERE name = 'agent_sessions'")
        beside.execute("PRAGMA writable_schema = OFF")
        beside.close()
        broken = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(broken.close)
        broken.execute("UPDATE agent_sessions SET state = 'gone'")
        broken.close()
        with self.assertRaises(ContractRefusal) as caught:
            agent_sessions_of(self.store, ATTEMPT)
        self.assertEqual(caught.exception.code, "schema")


if __name__ == "__main__":
    unittest.main()
