"""W4 cut D — the runtime attempt, its activation and its observations.

PLAN item 4be, first slice. Every case here is about one question: when this
manager says an attempt is bound to an assignment, what makes that true?

THE ANSWER IS THREE THINGS AGREEING. The session's binding, this attempt's own
committed claim, and the authority's live assignment. Any two of them agreeing
is exactly how a foreign session or a replayed activation gets in, so each case
below removes one of the three and requires a refusal.
"""

import os
import queue
import sqlite3
import tempfile
import threading
import json
import unittest
from unittest import mock

import baton_v12.worker_manager as worker_manager
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (AuthorityPort, ControlStore, TRANSITIONS,
                                      accept_offer, activate_assignment,
                                      certify_profile, issue_offer, observe,
                                      reconcile_runtime, record_attempt,
                                      request_cancellation,
                                      request_runtime_start, submit_claim)
from baton_v12.worker_manager import attempts as attempts_module
from baton_v12.worker_manager.attempts import (OBSERVED_RUNTIME,
                                               authorize_input_root)
from baton_v12.worker_manager.schema import ATTEMPT_COLUMNS
from baton_v12.worker_manager.store import manager_signature
from baton_v12.worker_manager.workspaces import (assignment_workspace,
                                                 compose_input_root)

from . import input_roots
from .test_offers import (FakeSession, NOW, PRINCIPAL, PROFILE, ROUTE,
                          SCOPE, UUID, WHO, WORK, decision,
                          fake_claim_signature)


class Adapter:
    """The narrow runtime adapter, with every answer a test may need to set."""

    def __init__(self, runtime_id="runtime-1"):
        self.runtime_id = runtime_id
        self.started = []
        self.stopped = []
        self.listing = None
        self.start_answer = None
        self.start_failure = None
        self.stop_failure = None
        # W26294: reconciliation now ASKS the engine what the exact runtime
        # is instead of reading `running` off a listing that includes exited
        # containers. Every case that reconciles needs an answer; `running`
        # is the one that preserves what each existing case was about, and
        # the cases that are ABOUT the other states set it.
        self.observation = {"state": "running", "why": "it is up",
                            "mounts": None}
        self.observed = []

    def start(self, operands):
        self.started.append(operands)
        # W6636: a start the adapter REFUSES, which is the post-claim failure
        # the manager has to settle rather than propagate untouched.
        if self.start_failure is not None:
            raise self.start_failure
        if self.start_answer is not None:
            return self.start_answer
        return {"runtime_id": self.runtime_id, "labels": operands["labels"]}

    def list(self, operands):
        if self.listing is not None:
            return self.listing
        if not self.started:
            return []
        return [{"runtime_id": self.runtime_id,
                 "labels": self.started[0]["labels"]}]

    def observe(self, runtime_id):
        self.observed.append(runtime_id)
        if isinstance(self.observation, BaseException):
            raise self.observation
        return self.observation

    def stop(self, operands):
        self.stopped.append(operands)
        if self.stop_failure is not None:
            raise self.stop_failure
        return {"stopped": True}


class Agent:
    def __init__(self):
        self.cancelled = []
        self.failure = None

    def cancel(self, operands):
        self.cancelled.append(operands)
        if self.failure is not None:
            raise self.failure
        return {"acknowledged": True}

ATTEMPT = "attempt-1"
ADAPTER = "sha256:" + "a" * 64


class AttemptCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-worker-manager-")
        self.addCleanup(self._root.cleanup)
        self.path = os.path.join(self._root.name, "control.sqlite3")
        self.store = ControlStore.open(self.path, incarnation="manager-1",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        certify_profile(self.store, "runtime", "reference", PROFILE)
        # W33936 review [P1]: the workspace group is the DEPLOYMENT's, read
        # from this manager's own record. A fixture configures it and then
        # reads it, which is the sequence a deployment performs.
        self.group = input_roots.configured_group(self.store)
        self.session = FakeSession()
        self.port = AuthorityPort(self.session, fake_claim_signature)

    def recorded(self, attempt_id=ATTEMPT):
        # THE POLICY DIGEST IS RECORDED, because W6632 review [P1] made a
        # runtime's labels carry it: reconciliation after a restart proves the
        # resolved identity from the engine's image and this manager's labels,
        # and the policy exists in neither unless it is written here.
        return record_attempt(self.store, attempt_id=attempt_id,
                              adapter_name="acp", adapter_digest=ADAPTER,
                              profile_digest=PROFILE,
                              policy_digest="sha256:" + "2" * 64)

    def claimed(self, offer_id="offer-1", attempt_id=ATTEMPT):
        """An attempt with THIS attempt's own committed claim behind it."""
        issue_offer(self.store, self.port, offer_id=offer_id, work_id=WORK,
                    runtime_attempt_id=attempt_id,
                    input_digest="sha256:" + "1" * 64,
                    policy_digest="sha256:" + "2" * 64,
                    profile_digest=PROFILE, profile_name="reference",
                    mint_bearer=lambda: "bearer-1")
        accept_offer(self.store, self.port, offer_id=offer_id,
                     decision="accept", bearer="bearer-1", now=NOW,
                     runtime_attempt_id=attempt_id,
                     work_ref={"authority_uuid": UUID, "work_id": WORK})
        self.recorded(attempt_id)
        submit_claim(self.store, self.port, offer_id=offer_id)
        return attempt_id

    def expect(self, **spoiled):
        whole = {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                 "participant": WHO, "generation": 1}
        whole.update(spoiled)
        return whole

    def row(self, attempt_id=ATTEMPT):
        beside = sqlite3.connect(self.path, isolation_level=None)
        beside.row_factory = sqlite3.Row
        try:
            found = beside.execute(
                "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
                (attempt_id,)).fetchone()
            return None if found is None else {k: found[k]
                                               for k in found.keys()}
        finally:
            beside.close()


class TheAttemptIsRecordedOnce(AttemptCase):

    def test_an_exact_retry_replays_the_first_record(self):
        first = self.recorded()
        self.assertEqual(first, self.recorded())
        self.assertEqual(self.row()["adapter_name"], "acp")

    def test_every_durable_operand_rides_the_identity(self):
        """The frozen host signed three of eight.

        A changed adapter name or input digest then REPLAYED instead of
        colliding -- an operation identity that ignores operands is not an
        identity, and the retry's answer would describe the first act.
        """
        self.recorded()
        for what, spoiled in [("the adapter name", dict(adapter_name="other")),
                              ("the adapter digest",
                               dict(adapter_digest="sha256:" + "b" * 64)),
                              ("the profile digest",
                               dict(profile_digest="sha256:" + "c" * 64)),
                              ("an input digest that was absent",
                               dict(input_digest="sha256:" + "d" * 64)),
                              ("a policy digest that was absent",
                               dict(policy_digest="sha256:" + "e" * 64)),
                              ("an image digest that was absent",
                               dict(image_digest="sha256:" + "f" * 64)),
                              ("a toolchain digest that was absent",
                               dict(toolchain_digest="sha256:" + "0" * 64))]:
            with self.subTest(what=what):
                operands = dict(adapter_name="acp", adapter_digest=ADAPTER,
                                profile_digest=PROFILE)
                operands.update(spoiled)
                with self.assertRaises(ContractRefusal) as caught:
                    record_attempt(self.store, attempt_id=ATTEMPT, **operands)
                self.assertEqual(caught.exception.code, "operation-collision")

    def test_a_fresh_attempt_starts_at_every_axis_default(self):
        self.recorded()
        row = self.row()
        for axis in TRANSITIONS:
            with self.subTest(axis=axis):
                self.assertIn(row[axis], TRANSITIONS[axis])
        self.assertEqual(row["execution_runtime"], "not-started")
        self.assertEqual(row["cleanup"], "pending")
        self.assertIsNone(row["assignment_generation"])


class ActivationNeedsAllThreeToAgree(AttemptCase):

    def test_activation_fixes_all_four_parts(self):
        self.claimed()
        answer = activate_assignment(self.store, self.port,
                                     attempt_id=ATTEMPT, expect=self.expect())
        self.assertIs(answer["already_fixed"], False)
        self.assertEqual(answer["assignment"], self.expect())
        row = self.row()
        self.assertEqual(
            (row["authority_uuid"], row["work_id"],
             row["assignment_participant"], row["assignment_generation"]),
            (UUID, WORK, WHO, 1))

    def test_an_attempt_with_no_claim_of_its_own_is_refused(self):
        """A live assignment elsewhere is not evidence.

        The frozen host accepted any free-standing attempt beside any currently
        live assignment -- so a foreign session could activate somebody else's
        attempt onto its own Work.
        """
        self.recorded()
        with self.assertRaises(ContractRefusal) as caught:
            activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                                expect=self.expect())
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("no committed claim", caught.exception.message)

    def test_an_activation_for_another_identity_is_refused(self):
        for what, spoiled in [
                ("another participant", dict(participant="baton.someone")),
                ("another generation", dict(generation=2)),
                ("another Work", dict(work_ref={"authority_uuid": UUID,
                                                "work_id": "0000000a-W9"})),
                ("another authority", dict(work_ref={"authority_uuid": "f" * 32,
                                                     "work_id": WORK}))]:
            with self.subTest(what=what):
                self.setUp()
                self.claimed()
                with self.assertRaises(ContractRefusal) as caught:
                    activate_assignment(self.store, self.port,
                                        attempt_id=ATTEMPT,
                                        expect=self.expect(**spoiled))
                self.assertIn(caught.exception.category,
                              ("refused", "stale-assignment"))
                # THE MESSAGE NAMES THE PART THAT DIFFERS. "a dict and a dict"
                # is a true sentence about two assignments and tells a reader
                # nothing about which of the four parts disagreed.
                self.assertRegex(
                    caught.exception.message,
                    r"(participant|generation|work_id|authority_uuid"
                    r"|acts for)")
                self.assertIsNone(self.row()["assignment_generation"])

    def test_the_session_binding_decides_who_may_activate(self):
        """Checked BEFORE the claim is looked up, and before anything writable.

        A session for somebody else must not get as far as reading this
        attempt's claim, let alone fixing an assignment with it.
        """
        self.recorded()
        self.session.participant = "baton.someone"
        port = AuthorityPort(self.session, fake_claim_signature)
        with self.assertRaises(ContractRefusal) as caught:
            activate_assignment(self.store, port, attempt_id=ATTEMPT,
                                expect=self.expect())
        self.assertIn("activated by the identity that holds it",
                      caught.exception.message)
        self.assertIn(WHO, caught.exception.message)
        self.assertIn("baton.someone", caught.exception.message)

    def test_the_live_assignment_must_agree_too(self):
        self.claimed()
        self.session.live_assignment = {
            "work_ref": {"authority_uuid": UUID, "work_id": WORK},
            "participant": WHO, "generation": 2}
        with self.assertRaises(ContractRefusal) as caught:
            activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                                expect=self.expect())
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("stale-assignment", "generation"))

    def test_a_row_fixed_without_a_journal_row_answers_as_it_stands(self):
        """The fallback, and what `already_fixed` now means.

        An exact retry REPLAYS the recorded answer, so it never reaches this
        branch -- which leaves it for the case it was always about: an attempt
        this build finds already fixed with no act of its own to reproduce. Then
        the honest answer is the assignment AS IT STANDS, and saying which of
        the two happened is the point of the flag.
        """
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            # Somebody else's act: the row is fixed and this journal has no
            # record of fixing it.
            beside.execute("DELETE FROM operations WHERE operation_id = ?",
                           (f"assignment.activate:{ATTEMPT}",))
        finally:
            beside.close()
        again = activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                                    expect=self.expect())
        self.assertIs(again["already_fixed"], True)
        self.assertEqual(again["assignment"], self.expect())

    def test_an_exact_reactivation_replays_one_byte_stable_answer(self):
        """The same act cannot answer according to when its retry arrived.

        A retry that entered before the first commit is replayed by the journal;
        one that entered afterwards must not bypass that row and synthesize a
        different `already_fixed` answer from current state.
        """
        self.claimed()
        first = activate_assignment(self.store, self.port,
                                    attempt_id=ATTEMPT, expect=self.expect())
        again = activate_assignment(self.store, self.port,
                                    attempt_id=ATTEMPT, expect=self.expect())
        self.assertEqual(again, first)

    def test_a_fixed_attempt_refuses_a_different_identity(self):
        """FIXED ONCE, and compared on ALL FOUR parts.

        Comparing Work and generation alone let a later activation replay under
        another participant or authority.
        """
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            beside.execute("UPDATE offers SET participant = 'baton.someone', "
                           "claim_generation = 2")
        finally:
            beside.close()
        self.session.participant = "baton.someone"
        self.session.live_assignment = {
            "work_ref": {"authority_uuid": UUID, "work_id": WORK},
            "participant": "baton.someone", "generation": 2}
        port = AuthorityPort(self.session, fake_claim_signature)
        with self.assertRaises(ContractRefusal) as caught:
            activate_assignment(self.store, port, attempt_id=ATTEMPT,
                                expect=self.expect(participant="baton.someone",
                                                   generation=2))
        self.assertEqual(caught.exception.category, "stale-assignment")
        self.assertIn("is fixed to", caught.exception.message)


class ObservationsMoveAlongTheirOwnAxis(AttemptCase):

    def test_unhashable_axis_and_value_are_contract_refusals(self):
        """Closed vocabularies type before asking a membership question."""
        self.recorded()
        for what, call in [
                ("axis", {"axis": [], "value": "running"}),
                ("value", {"axis": "consent_runtime", "value": []})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    observe(self.store, attempt_id=ATTEMPT, **call)
                self.assertEqual((caught.exception.category,
                                  caught.exception.code),
                                 ("integrity", "schema"))

    def test_an_axis_moves_only_where_its_map_allows(self):
        self.recorded()
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="start-requested")
        with self.assertRaises(ContractRefusal) as caught:
            observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                    value="not-started")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("runtime-observation", "state-regression"))

    def test_a_terminal_alternative_is_never_overwritten(self):
        """Every worker disposition is a terminal ANSWER.

        Treating the vocabulary's order as a transition order made `completed`
        advance to `unable` -- a different answer, not a later stage of the same
        one.
        """
        self.recorded()
        observe(self.store, attempt_id=ATTEMPT, axis="worker_disposition",
                value="completed")
        for other in ("unable", "plan-rejected", "cancelled"):
            with self.subTest(other=other):
                with self.assertRaises(ContractRefusal):
                    observe(self.store, attempt_id=ATTEMPT,
                            axis="worker_disposition", value=other)
        self.assertEqual(self.row()["worker_disposition"], "completed")

    def test_uncertainty_never_becomes_destruction(self):
        """Destruction is a fact about the world.

        Inferring it from a failure to look would report a cleaned-up runtime
        that is still executing somebody's code.
        """
        self.recorded()
        observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                value="uncertain")
        with self.assertRaises(ContractRefusal):
            observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                    value="destroyed")
        self.assertIn("running", TRANSITIONS["consent_runtime"]["uncertain"])

    def test_an_exact_repeat_from_one_source_replays(self):
        self.recorded()
        source = {"incarnation": "worker-7", "seq": 3}
        first = observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                        value="running", source=source)
        again = observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                        value="running", source=source)
        self.assertIs(first.get("replayed", False), False)
        self.assertIs(again["replayed"], True)
        self.assertIs(again["changed"], False)

    def test_a_different_observation_under_one_source_identity_refuses(self):
        self.recorded()
        source = {"incarnation": "worker-7", "seq": 3}
        observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                value="running", source=source)
        with self.assertRaises(ContractRefusal) as caught:
            observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                    value="quiescent", source=source)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("runtime-observation", "state-regression"))
        self.assertEqual(self.row()["consent_runtime"], "running")

    def test_an_exact_replay_survives_the_axis_moving_on(self):
        """What a source identity already said is a fact about THAT IDENTITY.

        The frozen host consulted today's axis first, so an EXACT old
        observation was refused once the axis had advanced.
        """
        self.recorded()
        source = {"incarnation": "worker-7", "seq": 1}
        observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                value="running", source=source)
        observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                value="quiescent", source={"incarnation": "worker-7",
                                           "seq": 2})
        again = observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                        value="running", source=source)
        self.assertIs(again["replayed"], True)
        self.assertEqual(self.row()["consent_runtime"], "quiescent")

    def test_an_inert_sourced_observation_still_consumes_its_identity(self):
        """Otherwise the identity's meaning depends on where the axis was.

        An inert sourced observation that wrote no row left its
        `(attempt, incarnation, seq)` reusable, and a DIFFERENT observation
        could then commit under it.
        """
        self.recorded()
        observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                value="running")
        source = {"incarnation": "worker-7", "seq": 1}
        inert = observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                        value="running", source=source)
        self.assertIs(inert["changed"], False)
        with self.assertRaises(ContractRefusal):
            observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                    value="quiescent", source=source)

    def test_a_manager_repeat_stays_inert_and_mints_nothing(self):
        """There is no identity for anyone else to reuse, so there is no row."""
        self.recorded()
        observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                value="running")
        answer = observe(self.store, attempt_id=ATTEMPT,
                         axis="consent_runtime", value="running")
        self.assertIs(answer["changed"], False)
        self.assertNotIn("manager_seq", answer)
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            rows = beside.execute(
                "SELECT COUNT(*) FROM observations").fetchone()[0]
        finally:
            beside.close()
        self.assertEqual(rows, 1)

    def test_a_refused_observation_leaves_no_row_behind(self):
        """The savepoint is the boundary, and it holds at either depth."""
        self.recorded()
        observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                value="running")
        with self.assertRaises(ContractRefusal):
            observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                    value="not-started", source={"incarnation": "w", "seq": 9})
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            found = beside.execute(
                "SELECT COUNT(*) FROM observations WHERE incarnation = 'w'"
            ).fetchone()[0]
        finally:
            beside.close()
        self.assertEqual(found, 0)
        self.assertEqual(self.row()["consent_runtime"], "running")

    def test_the_manager_sequence_orders_what_was_recorded(self):
        self.recorded()
        seen = []
        for axis, value in [("consent_runtime", "running"),
                            ("execution_runtime", "start-requested"),
                            ("output", "freeze-requested")]:
            seen.append(observe(self.store, attempt_id=ATTEMPT, axis=axis,
                                value=value)["manager_seq"])
        self.assertEqual(seen, [1, 2, 3])
        self.assertEqual(self.row()["observation_seq"], 3)


class WhatOnlyAnotherWriterCanCause(AttemptCase):
    """Guards whose condition one process cannot reach on its own.

    Each of these measured zero as a mutation until it was driven the way it
    actually happens: a store some other build wrote, a table some other build
    constrained, or a second manager acting between this one's read and its
    write. A guard that can only be reasoned about is a guard nobody has
    checked.
    """

    def beside(self):
        found = sqlite3.connect(self.path, isolation_level=None)
        found.execute("PRAGMA busy_timeout = 2000")
        return found

    def test_two_claimed_offers_for_one_attempt_refuse_rather_than_choose(self):
        """The unique index makes two impossible GOING FORWARD.

        This fails closed against a store written before it, because "which of
        these two is this attempt's claim" has no answer a manager may guess at.
        """
        self.claimed()
        beside = self.beside()
        try:
            beside.execute("DROP INDEX offers_one_claim_per_attempt")
            beside.execute(
                "INSERT INTO offers (offer_id, work_id, authority_uuid, "
                "participant, runtime_attempt_id, incarnation, input_digest, "
                "policy_digest, profile_digest, verifier, verifier_spent, "
                # W16823: the frozen pair, and the context a `claimed` row must
                # carry all of.
                "work_scope, work_route, claim_event_seq, claim_principal, "
                "claim_scope, claim_role, claim_grant, "
                "claim_policy_generation, "
                "issued_at, expires_at, state, intent_digest, accepted_at, "
                "settle_by, claim_operation_id, claim_signature) VALUES "
                "('offer-2', ?, ?, ?, ?, 'm', 'd', 'd', ?, 'v', 1, "
                "?, ?, 2, ?, ?, ?, 'direct', 1, ?, ?, "
                "'claimed', 'i', ?, ?, 'claim:x', 's')",
                (WORK, UUID, WHO, ATTEMPT, PROFILE, SCOPE, ROUTE,
                 PRINCIPAL, SCOPE, ROUTE, NOW, NOW, NOW, NOW))
        finally:
            beside.close()
        with self.assertRaises(ContractRefusal) as caught:
            activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                                expect=self.expect())
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("2 claimed offers", caught.exception.message)

    def test_a_refused_insert_takes_the_axis_move_with_it(self):
        """The savepoint is the boundary, and this is the case that needs it.

        The transition check refuses BEFORE anything is written, so a rollback
        matters only when the write itself fails -- and then the axis must not
        keep a move whose observation was never recorded.
        """
        self.recorded()
        beside = self.beside()
        try:
            beside.execute(
                "CREATE TRIGGER no_observations BEFORE INSERT ON observations "
                "BEGIN SELECT RAISE(ABORT, 'somebody else constrains this'); "
                "END")
        finally:
            beside.close()
        with self.assertRaises(sqlite3.IntegrityError):
            observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                    value="running")
        self.assertEqual(self.row()["consent_runtime"], "not-started")
        self.assertEqual(self.row()["observation_seq"], 0)

    def test_a_failure_whose_PROSE_says_busy_keeps_its_own_identity(self):
        """The result code decides, never the message.

        The frozen host matched a substring of the free-form message, so a
        trigger raising `busy provider invariant` was handed a database lock's
        portable meaning AND its retry policy. That message is
        APPLICATION-CONTROLLED prose; a caller told to retry a constraint
        violation will retry it forever.

        A mutation that went back to matching prose measured zero until this
        existed -- every failure I had driven differed in code AND in wording.
        """
        self.recorded()
        beside = self.beside()
        try:
            beside.execute(
                "CREATE TRIGGER busy_sounding BEFORE INSERT ON observations "
                "BEGIN SELECT RAISE(ABORT, 'busy provider invariant: database "
                "is locked by policy'); END")
        finally:
            beside.close()
        with self.assertRaises(sqlite3.IntegrityError) as caught:
            observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                    value="running")
        self.assertIn("busy", str(caught.exception))
        self.assertEqual(self.row()["consent_runtime"], "not-started")

    def test_a_second_manager_activating_first_replays_rather_than_writes(self):
        """What the race actually produces, measured rather than assumed.

        I wrote this expecting the activation's compare-and-swap to refuse, and
        it does not: the two managers derive the SAME operation identity from
        the same operands, so the journal replays the first manager's committed
        answer before the second's act runs at all. Effectively-once settles the
        race one layer above the swap.

        THE SWAP IS THEREFORE NOT DRIVABLE THROUGH THE PUBLIC SURFACE, and I am
        recording that rather than deleting it: unlike the three unreachable
        VALIDATIONS this campaign has made me remove, it is the write's own
        condition -- the thing that makes the UPDATE conditional at all -- and
        removing it would leave the durable write unguarded against a future
        caller that reaches it under another identity. Flagged for review as a
        judgement call, not as a proof.
        """
        self.claimed()
        other = ControlStore.open(self.path, incarnation="manager-2",
                                  clock=lambda: NOW)
        self.addCleanup(other.close)
        racing = AuthorityPort(FakeSession(), fake_claim_signature)
        original = self.port.assignment_of

        def activate_first(work_id, authority_uuid):
            # The other manager commits between this call's read and its write.
            activate_assignment(other, racing, attempt_id=ATTEMPT,
                                expect=self.expect())
            return original(work_id, authority_uuid)

        self.port.assignment_of = activate_first
        answer = activate_assignment(self.store, self.port,
                                     attempt_id=ATTEMPT, expect=self.expect())
        self.assertIs(answer["already_fixed"], False)
        self.assertEqual(answer["assignment"], self.expect())
        self.assertEqual(self.row()["assignment_generation"], 1)
        beside = self.beside()
        try:
            rows = beside.execute(
                "SELECT COUNT(*) FROM operations WHERE operation_id = ?",
                (f"assignment.activate:{ATTEMPT}",)).fetchone()[0]
        finally:
            beside.close()
        self.assertEqual(rows, 1)

    def test_a_stale_observer_translates_only_database_contention(self):
        """A deferred snapshot must not leak SQLite's lock vocabulary.

        The clock hook pauses the first manager after it has read the old axis
        and immediately before its conditional update. A second manager commits
        the same transition, leaving the first snapshot stale. The frozen host
        classifies this exact storage condition as a state-regression refusal.
        """
        reached_update = threading.Event()
        release_update = threading.Event()
        outcomes = queue.Queue()
        calls = 0

        def paused_clock():
            nonlocal calls
            calls += 1
            if calls == 2:
                reached_update.set()
                release_update.wait(5)
            return NOW

        self.recorded()

        def stale_writer():
            other = ControlStore.open(self.path, incarnation="manager-2",
                                      clock=paused_clock)
            try:
                try:
                    outcomes.put(observe(
                        other, attempt_id=ATTEMPT, axis="consent_runtime",
                        value="running"))
                except BaseException as failure:
                    outcomes.put(failure)
            finally:
                other.close()

        thread = threading.Thread(target=stale_writer)
        thread.start()
        self.assertTrue(reached_update.wait(5))
        observe(self.store, attempt_id=ATTEMPT, axis="consent_runtime",
                value="running")
        release_update.set()
        thread.join(5)
        self.assertFalse(thread.is_alive())
        outcome = outcomes.get_nowait()
        self.assertIsInstance(outcome, ContractRefusal)
        self.assertEqual((outcome.category, outcome.code),
                         ("runtime-observation", "state-regression"))


class TheRuntimeIsStartedOnceAndReconciled(AttemptCase):
    """ZERO WAITS, and starting a second runtime for one assignment is the
    failure this whole ordering exists to prevent."""

    def activated(self, attempt_id=ATTEMPT):
        self.claimed(attempt_id=attempt_id)
        activate_assignment(self.store, self.port, attempt_id=attempt_id,
                            expect=self.expect())
        return attempt_id

    # THIS SUITE'S OWN CONSTANTS CANNOT APPEAR IN A MANIFEST, and that is not
    # a fixture nicety. `UUID` is 31 zeros and an `a`, so its first eight
    # characters are `00000000` while `WORK` reads `0000000a-W1` -- §12 rule 1
    # refuses that pair, and this suite never noticed because nothing here
    # validated a manifest until now. The launch boundary does, so the cases
    # that drive it use a Work reference the contract accepts.
    VALID_WORK = {"authority_uuid": "43c55d4b1234567890abcdef12345678",
                  "work_id": "43c55d4b-W1439"}

    def delivered(self, attempt_id=ATTEMPT, **override):
        """A composed input root for this attempt, and the attempt recorded
        against the very input manifest inside it.

        BOTH HALVES, because the launch boundary compares them: an attempt
        recorded against one digest and a root carrying another is exactly the
        mis-composition it exists to refuse, and a fixture that produced it by
        accident would make every case here a test of that one refusal.
        """
        work_ref = dict(self.VALID_WORK)
        live = {"work_ref": dict(work_ref), "participant": WHO,
                "generation": 1}
        self.session._work = {"status": "open", "phase": "queued",
                              "handler": None, "gate": None,
                              "authority_uuid": work_ref["authority_uuid"],
                              # W16823: what the offer freezes about the Work.
                              "scope": SCOPE, "route": ROUTE}
        self.session.claim_answer = {"assignment": dict(live),
                                     "claim_event": 1,
                                     "decision": decision()}
        self.session.live_assignment = dict(live)
        given, assignment = input_roots.documents(
            work_ref=work_ref, participant=WHO, generation=1,
            runtime_attempt_id=attempt_id, **override)
        issue_offer(self.store, self.port, offer_id="offer-1",
                    work_id=work_ref["work_id"],
                    runtime_attempt_id=attempt_id,
                    input_digest=given["manifest_digest"],
                    policy_digest="sha256:" + "2" * 64,
                    profile_digest=PROFILE, profile_name="reference",
                    mint_bearer=lambda: "bearer-1")
        accept_offer(self.store, self.port, offer_id="offer-1",
                     decision="accept", bearer="bearer-1", now=NOW,
                     runtime_attempt_id=attempt_id, work_ref=dict(work_ref))
        record_attempt(self.store, attempt_id=attempt_id, adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       input_digest=given["manifest_digest"],
                       policy_digest="sha256:" + "2" * 64)
        submit_claim(self.store, self.port, offer_id="offer-1")
        activate_assignment(self.store, self.port, attempt_id=attempt_id,
                            expect=dict(live))
        storage = input_roots.storage_under(self)
        inputs = assignment_workspace(
            self.group, storage, attempt_id)["inputs"]
        compose_input_root(inputs, given, assignment,
                           assignment=dict(assignment["assignment_ref"]),
                           runtime_attempt_id=attempt_id)
        self.addCleanup(input_roots._forcibly_remove, storage)
        return inputs, given, assignment

    def labels(self, attempt_id=ATTEMPT):
        row = self.row(attempt_id)
        return {"runtime_attempt_id": row["runtime_attempt_id"],
                "authority_uuid": row["authority_uuid"],
                "work_id": row["work_id"],
                "participant": row["assignment_participant"],
                "generation": row["assignment_generation"],
                # W16823: the principal and the scope the claim was authorized
                # for, BESIDE the fence rather than instead of any of it.
                "principal": row["assignment_principal"],
                "effective_scope": row["assignment_scope"],
                "profile_digest": row["profile_digest"],
                "policy_digest": row["policy_digest"],
                "adapter_digest": row["adapter_digest"]}

    def test_a_start_over_an_authorized_root_proceeds(self):
        """W19784 review [P0]. The positive: an attempt claimed against an
        input manifest, a root composed for that exact assignment and attempt,
        and the runtime starts."""
        inputs, given, _assignment = self.delivered()
        adapter = Adapter()
        answer = request_runtime_start(self.store, adapter,
                                       attempt_id=ATTEMPT, inputs=inputs)
        self.assertEqual(answer["decision"], "attached")
        back_input, back_assignment = authorize_input_root(
            self.store, attempt_id=ATTEMPT, inputs=inputs)
        self.assertEqual(back_input["manifest_digest"],
                         given["manifest_digest"])
        self.assertEqual(back_assignment["assignment_ref"],
                         {"work_ref": dict(self.VALID_WORK),
                          "participant": WHO, "generation": 1})

    def test_authorizing_one_root_cannot_start_an_adapter_mounting_another(self):
        """The launch authorization and the mount must name ONE root.

        `request_runtime_start` currently validates its `inputs` operand and
        then calls an adapter whose mount plan is independent of that operand.
        The production OCI adapter owns such a plan at construction. Without
        an equality boundary the manager can prove one directory and expose a
        different one at the worker's fixed `/input` path.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        adapter.mounts = ({"source": os.path.join(os.path.dirname(inputs),
                                                   "workspace"),
                           "target": "/input", "writable": False},)
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(adapter.started, [])
        self.assertEqual(self.row()["execution_runtime"], "not-started")

    def test_a_noncanonical_input_target_refuses_before_start_is_journalled(
            self):
        """Normalizing a plan must not erase the spelling being authorized.

        OCI's own boundary refuses `..` before normalization. If the earlier
        manager check normalizes first, `/else/../input` masquerades as the
        fixed `/input`; the adapter eventually refuses it, but only after the
        manager committed a start operation that now needs settlement.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        adapter.mounts = ({"source": inputs, "target": "/else/../input",
                           "writable": False},)
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(adapter.started, [])
        self.assertEqual(self.row()["execution_runtime"], "not-started")

    def test_a_noncanonical_input_source_refuses_before_start_is_journalled(
            self):
        """The same rule applies to the host source spelling.

        `realpath` equality proves where a spelling resolves; it does not make
        a traversal spelling canonical. The OCI boundary refuses such a
        source, so the earlier plan check must not journal it first.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        adapter.mounts = ({"source": os.path.join(inputs, "..", "inputs"),
                           "target": "/input", "writable": False},)
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(adapter.started, [])
        self.assertEqual(self.row()["execution_runtime"], "not-started")

    def test_the_authorized_root_crosses_the_adapter_seam(self):
        """W19784 second review [P0], the half `_plan_agrees` cannot cover.

        The manager's own check reads an adapter's DECLARED plan, and an
        adapter that declares none -- or one reached by any path other than
        this function -- still has to fail closed on its own. It can only do
        that if it is told which root was proved, so what this observes is the
        value ARRIVING: the adapter's own cases in `test_oci` then decide what
        it does with it.

        Without this the manager's earlier refusal would mask the seam
        entirely, and the adapter would be trusting a plan nobody compared.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        self.assertEqual(adapter.started[0]["input_root"], inputs)

    def test_a_start_with_no_root_says_so_across_the_seam(self):
        """And absence crosses it too, as a value rather than as an omission.
        An adapter cannot refuse a `/input` bind it was never told was
        unauthorized."""
        # `activated()` records the attempt WITHOUT an input digest, which is
        # the only state in which no root can be required -- and this suite's
        # ordinary fixture, so the case reads the same path every other start
        # case here does.
        self.activated()
        adapter = Adapter()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertIn("input_root", adapter.started[0])
        self.assertIsNone(adapter.started[0]["input_root"])

    def test_a_claimed_attempt_will_not_start_without_a_root(self):
        """THE REQUIREMENT IS DERIVED, not optional. `inputs=None` is reachable
        only when the attempt records no input digest -- and an attempt that
        was offered and claimed against an input manifest records one, so from
        that moment there is no way to start without an authorized root.

        An optional operand would have been the hole the review found: a caller
        that could pass nothing would start a runtime over a directory nothing
        established.
        """
        self.delivered()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, Adapter(), attempt_id=ATTEMPT)
        self.assertEqual(caught.exception.code, "precondition")
        self.assertEqual(self.row()["execution_runtime"], "not-started",
                         "a refused authorization still journalled a start")

    def test_a_root_composed_for_another_delivery_never_starts_a_runtime(self):
        """Each root below is internally perfect and composed by the real
        boundary. What refuses is that it is not THIS attempt's -- and it
        refuses BEFORE the start operation is journalled, so there is no
        runtime and nothing to reconcile."""
        storage = input_roots.storage_under(self)
        self.delivered()
        mine = {"work_ref": dict(self.VALID_WORK), "participant": WHO,
                "generation": 1}
        for what, spoiled, elsewhere in (
                ("a superseded generation",
                 dict(mine, generation=mine["generation"] + 1), "other-1"),
                ("another participant",
                 dict(mine, participant="baton.someone"), "other-2"),
                ("another runtime attempt", dict(mine), "other-3")):
            with self.subTest(what=what):
                given, assignment = input_roots.documents(
                    work_ref=spoiled["work_ref"],
                    participant=spoiled["participant"],
                    generation=spoiled["generation"],
                    runtime_attempt_id=(ATTEMPT if what != "another runtime "
                                        "attempt" else elsewhere))
                inputs = assignment_workspace(
                    self.group, storage, elsewhere)["inputs"]
                compose_input_root(
                    inputs, given, assignment,
                    assignment=dict(assignment["assignment_ref"]),
                    runtime_attempt_id=assignment["runtime_attempt_id"])
                with self.assertRaises(ContractRefusal):
                    request_runtime_start(self.store, Adapter(),
                                          attempt_id=ATTEMPT, inputs=inputs)
                self.assertEqual(self.row()["execution_runtime"],
                                 "not-started")
        self.addCleanup(input_roots._forcibly_remove, storage)

    def test_a_root_carrying_another_input_manifest_never_starts(self):
        """The third manager-owned fact: the attempt's own record of what it
        was claimed against. A root whose assignment names the right identity
        but whose input manifest is a different document is a delivery this
        attempt was never offered."""
        storage = input_roots.storage_under(self)
        self.delivered()
        given, assignment = input_roots.documents(
            work_ref=dict(self.VALID_WORK),
            participant=WHO, generation=1, runtime_attempt_id=ATTEMPT,
            policy_digest="sha256:" + "e" * 64)
        inputs = assignment_workspace(
            self.group, storage, "other-input")["inputs"]
        compose_input_root(inputs, given, assignment,
                           assignment=dict(assignment["assignment_ref"]),
                           runtime_attempt_id=ATTEMPT)
        self.addCleanup(input_roots._forcibly_remove, storage)
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, Adapter(), attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(caught.exception.code, "digest")

    def test_an_unactivated_attempt_has_no_assignment_to_authorize_against(
            self):
        self.claimed()
        with self.assertRaises(ContractRefusal) as caught:
            authorize_input_root(self.store, attempt_id=ATTEMPT,
                                 inputs=input_roots.storage_under(self))
        self.assertEqual(caught.exception.code, "precondition")

    def test_the_start_operation_is_journalled_before_the_adapter_is_called(
            self):
        """An axis label is not an effectively-once act.

        A journalled operation is what a restart replays and what the adapter
        can be asked about; a state column records only that somebody once
        intended to start.
        """
        self.activated()
        adapter = Adapter()
        answer = request_runtime_start(self.store, adapter,
                                       attempt_id=ATTEMPT)
        self.assertEqual(answer["decision"], "attached")
        self.assertEqual(answer["runtime_id"], "runtime-1")
        operation_id = adapter.started[0]["operation_id"]
        self.assertTrue(operation_id.startswith("runtime.start:"))
        self.assertIsNotNone(self.store.operation_record(operation_id))
        self.assertEqual(self.row()["execution_runtime"], "running")

    def test_the_labels_carry_all_four_parts_of_the_assignment(self):
        """The frozen host omitted the participant, so two participants'
        runtimes on one Work and generation were indistinguishable."""
        self.activated()
        adapter = Adapter()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        labels = adapter.started[0]["labels"]
        self.assertEqual(labels, self.labels())
        for part in ("authority_uuid", "work_id", "participant", "generation"):
            with self.subTest(part=part):
                self.assertIsNotNone(labels[part])

    def test_a_runtime_cannot_start_without_the_policy_it_is_labelled_with(
            self):
        """W6632 review [P1] made the policy digest a reconciliation label.

        `policy_digest` is nullable on the attempt row, so this is a real
        precondition rather than a shape complaint: a delivery whose policy
        this manager cannot name is one no restart can describe, and the
        refusal says that rather than surfacing as a digest fault about
        `None` from inside the label constructor.
        """
        self.claimed()
        self.store._connection.execute(
            "UPDATE attempts SET policy_digest = NULL "
            "WHERE runtime_attempt_id = ?",
            (ATTEMPT,))
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        adapter = Adapter()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertIn("records no policy digest", caught.exception.message)
        self.assertEqual(adapter.started, [],
                         "nothing may be started for a delivery whose policy "
                         "this manager cannot name")

    def test_an_unactivated_attempt_cannot_start_a_runtime(self):
        self.recorded()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, Adapter(), attempt_id=ATTEMPT)
        self.assertIn("is not activated", caught.exception.message)

    def test_a_second_start_is_refused_rather_than_performed(self):
        self.activated()
        request_runtime_start(self.store, Adapter(), attempt_id=ATTEMPT)
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, Adapter(), attempt_id=ATTEMPT)
        self.assertEqual(caught.exception.code, "already-terminal")

    def test_a_runtime_this_call_mislabelled_is_cancelled_not_ignored(self):
        """It is not absent, it is WRONG, and this call caused it."""
        self.activated()
        adapter = Adapter()
        adapter.start_answer = {"runtime_id": "runtime-1",
                                "labels": dict(self.labels(),
                                               participant="baton.someone")}
        answer = request_runtime_start(self.store, adapter,
                                       attempt_id=ATTEMPT)
        self.assertEqual(answer["decision"], "cancel")
        self.assertIn("different assignment", answer["why"])
        self.assertEqual(self.row()["execution_runtime"], "cancel-requested")

    def test_two_runtimes_with_these_labels_cancel_rather_than_compound(self):
        self.activated()
        adapter = Adapter()
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()},
                           {"runtime_id": "runtime-2",
                            "labels": self.labels()}]
        answer = reconcile_runtime(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(answer["decision"], "cancel")
        self.assertEqual(sorted(answer["runtimes"]),
                         ["runtime-1", "runtime-2"])

    def test_an_empty_listing_with_no_identity_is_still_uncertainty(self):
        """"The adapter reports nothing" and "nothing exists" are different
        facts -- and this is the ONE reconciliation that still cannot tell them
        apart, because there is no runtime to name.

        Review [P0] narrowed this case rather than removing it. An empty
        listing used to be uncertainty ALWAYS, including when the attempt held
        the exact immutable runtime id -- so positive absence was unreachable
        in the ordinary post-removal shape. It is uncertainty now only when
        nothing was started by this call and nothing is recorded.
        """
        self.activated()
        adapter = Adapter()
        adapter.listing = []
        answer = reconcile_runtime(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(answer["decision"], "uncertain")
        self.assertIn("this attempt names none", answer["why"])
        self.assertEqual(self.row()["execution_runtime"], "uncertain")
        # AND NOTHING WAS ASKED, because nothing could be.
        self.assertEqual(adapter.observed, [])

    def test_an_empty_listing_over_a_known_runtime_observes_that_runtime(self):
        """Review [P0]: the ordinary post-removal shape.

        The container is gone, so `ps --all` no longer lists it -- and the
        attempt still holds the exact immutable runtime id. Reconciliation asks
        the adapter about that identity by name, which is the only way positive
        absence is reachable at all.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        self.assertEqual(adapter.observed, [adapter.runtime_id])
        adapter.listing = []
        adapter.observation = {"state": "absent", "why": "no such runtime",
                               "mounts": None}
        answer = reconcile_runtime(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(adapter.observed,
                         [adapter.runtime_id, adapter.runtime_id])
        self.assertEqual(answer["observed"], "destroyed")
        self.assertEqual(self.row()["execution_runtime"], "destroyed")

    def test_an_empty_listing_over_an_unobservable_runtime_stays_uncertain(
            self):
        """AND THE OTHER ANSWER STAYS DISTINCT. Asking is not the same as
        knowing: an adapter that cannot say what the exact runtime is leaves
        the attempt uncertain rather than absent, and the identity is not
        erased."""
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                              inputs=inputs)
        adapter.listing = []
        adapter.observation = {"state": "uncertain",
                               "why": "the daemon did not answer",
                               "mounts": None}
        answer = reconcile_runtime(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(answer["decision"], "uncertain")
        self.assertIn("the daemon did not answer", answer["why"])
        self.assertEqual(self.row()["execution_runtime"], "uncertain")
        self.assertEqual(self.row()["runtime_id"], adapter.runtime_id,
                         "an inconclusive observation erased the identity")

    def test_a_started_runtime_the_adapter_cannot_see_is_uncertain(self):
        """Review [P0]: the exact identity this call minted is ASKED ABOUT.

        It used to be reported uncertain without asking, on the reasoning that
        a runtime the adapter does not list has an unknown fate. That is true
        of the LISTING and not of the runtime: `minted` is an exact identity,
        and an adapter that cannot say what it is answers so. The uncertainty
        is now the adapter's answer rather than this manager's assumption.
        """
        self.activated()
        adapter = Adapter()
        adapter.listing = []
        adapter.observation = {"state": "uncertain",
                               "why": "the daemon did not answer",
                               "mounts": None}
        answer = request_runtime_start(self.store, adapter,
                                       attempt_id=ATTEMPT)
        self.assertEqual(answer["decision"], "uncertain")
        self.assertIn("the daemon did not answer", answer["why"])
        self.assertEqual(adapter.observed, [adapter.runtime_id])

    def test_the_first_attachment_fixes_the_runtime_identity(self):
        """A later inspection must not silently replace what is recorded."""
        self.activated()
        adapter = Adapter()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(self.row()["runtime_id"], "runtime-1")
        adapter.listing = [{"runtime_id": "runtime-9",
                            "labels": self.labels()}]
        answer = reconcile_runtime(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(answer["decision"], "cancel")
        self.assertEqual(self.row()["runtime_id"], "runtime-1")

    def test_reconciling_the_same_runtime_again_is_still_attached(self):
        self.activated()
        adapter = Adapter()
        request_runtime_start(self.store, adapter, attempt_id=ATTEMPT)
        again = reconcile_runtime(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(again["decision"], "attached")
        self.assertEqual(again["runtime_id"], "runtime-1")

    def test_a_failed_attachment_rolls_back_before_a_restart_retry(self):
        """A fault inside the atomic attachment commits neither half of it."""
        self.activated()
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="start-requested")
        adapter = Adapter()
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()}]
        with mock.patch("baton_v12.worker_manager.attempts.observe",
                        side_effect=RuntimeError("crash after attachment")):
            with self.assertRaises(RuntimeError):
                reconcile_runtime(self.store, adapter, attempt_id=ATTEMPT)
        # The observation is INSIDE the journalled transaction, so a crash there
        # commits NOTHING. There is no partial attachment for the reopened
        # manager to repair: its retry performs the attachment and observation
        # as one act.
        self.assertIsNone(self.row()["runtime_id"])
        self.assertEqual(self.row()["execution_runtime"], "start-requested")
        self.store.close()
        self.store = ControlStore.open(self.path, incarnation="manager-2",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)

        answer = reconcile_runtime(self.store, adapter, attempt_id=ATTEMPT)

        self.assertEqual(answer["decision"], "attached")
        self.assertEqual(self.row()["execution_runtime"], "running")


class ARefusedStartIsSettledRatherThanStranded(TheRuntimeIsStartedOnceAndReconciled):
    """W6636 [P0]: the post-claim start failure the composition owns.

    `request_runtime_start` journals the start operation and moves
    `execution_runtime` to `start-requested`, and only then calls the adapter.
    A refusal from that call used to propagate untouched, leaving the attempt
    claimed, activated and stranded: no runtime identity, an axis that is not
    terminal, and `authorize_cleanup` refusing exactly that shape -- "no
    runtime is attached; there is no identity to destroy and no absence to
    prove". A successful atomic claim could end in an attempt no operation in
    this manager could move.

    What the ADAPTER does about its own refusal is not what this manager
    knows: `OciAdapter._refused_start` settles both delivery roots and says so
    in refusal prose, and prose is not a durable manager fact.
    """

    def refused(self, failure=None):
        """An activated attempt with a real input root, and an adapter whose
        start refuses."""
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        # The pair `OciAdapter` actually raises from a declined engine run.
        adapter.start_failure = failure or ContractRefusal(
            "policy", "denied", "the engine refused to start this runtime")
        return adapter, inputs

    def test_the_attempt_does_not_stay_at_start_requested(self):
        """THE DEFECT. The axis stopped at an intention nobody could settle."""
        adapter, inputs = self.refused()
        adapter.listing = []
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertNotEqual(self.row()["execution_runtime"],
                            "start-requested")

    def test_a_runtime_the_failed_start_created_is_attached(self):
        """An engine can create a container and then fail.

        Attaching it is what makes it NAMEABLE by the ordinary destroy
        crossing, which is the only path that force-removes anything -- so
        this is the difference between a leaked container and one an operator
        can clean up.
        """
        adapter, inputs = self.refused()
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()}]
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(self.row()["runtime_id"], "runtime-1")
        self.assertEqual(self.row()["execution_runtime"], "running")
        self.assertIn("attached", str(caught.exception))
        # The reason the start failed is still what an operator reads first.
        self.assertIn("refused to start", str(caught.exception))

    def test_a_start_that_created_nothing_this_manager_can_name_is_uncertain(
            self):
        """FAIL CLOSED, and deliberately not "absent".

        No runtime carries these labels and this attempt names none, so the
        manager cannot say what was created -- and W26294 owns that answer.
        `uncertain` is the honest record, and it is also the one that keeps
        the invariant this ordering exists for: nothing starts a replacement.
        """
        adapter, inputs = self.refused()
        adapter.listing = []
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(self.row()["execution_runtime"], "uncertain")
        self.assertIsNone(self.row()["runtime_id"])
        self.assertIn("uncertain", str(caught.exception))

    def test_no_replacement_is_started_on_either_path(self):
        """One start attempt, one engine call. Settling must never become a
        second launch for one assignment, which is the failure the whole
        ordering is arranged against."""
        adapter, inputs = self.refused()
        adapter.listing = []
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(len(adapter.started), 1)

    def test_the_refusal_keeps_its_own_closed_pair(self):
        """The settlement is not a different thing going wrong.

        Measured against the boundary inventory: retyping every refusal as
        `refused/start-failed` broke three probes, because a malformed start
        ANSWER is `integrity/schema` at `_started` and relabelling it made the
        manager's account disagree with the boundary that found it.
        """
        adapter, inputs = self.refused(ContractRefusal(
            "integrity", "schema", "the adapter's start answer is malformed"))
        adapter.listing = []
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(caught.exception.category, "integrity")
        self.assertEqual(caught.exception.code, "schema")
        self.assertIn("the adapter's start answer is malformed",
                      str(caught.exception))

    def test_a_failed_reconciliation_still_leaves_an_ending(self):
        """RE-REVIEW [P0]: the settlement only settled when it went well.

        A failed reconciliation was caught to EXTEND THE MESSAGE and nothing
        else, so an adapter whose listing was unavailable left the attempt at
        `start-requested` with no identity -- the exact stranded state this
        settlement exists to remove, reached through the one path where the
        manager knows least. An ending recorded only on the happy path is not
        an invariant, and the submitted case checked that both messages
        crossed while never inspecting the durable row.
        """
        adapter, inputs = self.refused()

        class Blind(Adapter):
            def list(self, operands):
                raise ContractRefusal("unavailable", "transport",
                                      "the engine could not be reached")

        blind = Blind()
        blind.start_failure = adapter.start_failure
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, blind, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(self.row()["execution_runtime"], "uncertain")
        self.assertIsNone(self.row()["runtime_id"])
        self.assertIn("recorded uncertain", str(caught.exception))

    def test_an_adapter_without_list_still_leaves_an_ending(self):
        """The capability boundary takes the same path.

        `reconcile_runtime` types `list` and `observe` before asking either,
        so a narrow adapter refuses there -- and that refusal arrives after
        the start operation is journalled, which is what makes it this
        settlement's problem rather than a precondition.
        """
        adapter, inputs = self.refused()

        class Narrow(Adapter):
            list = None

        narrow = Narrow()
        narrow.start_failure = adapter.start_failure
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, narrow, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(self.row()["execution_runtime"], "uncertain")

    def test_a_start_that_faults_rather_than_refuses_still_settles(self):
        """A FAULT IS A FAILED START TOO.

        An adapter that raises something other than a refusal says even less
        about what it created than one that refuses, and it left the same
        stranded attempt. The fault itself is re-raised UNCHANGED -- this
        manager has no account of what it was, and inventing one would be
        worse than the fault.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        adapter.start_failure = RuntimeError("the driver fell over")
        adapter.listing = []
        with self.assertRaises(RuntimeError):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertNotEqual(self.row()["execution_runtime"],
                            "start-requested")
        self.assertEqual(self.row()["execution_runtime"], "uncertain")

    def test_a_fault_after_creation_still_attaches_the_exact_runtime(self):
        """RE-REVIEW [P0]: the fault path settled without reconciling.

        The first correction caught a non-`ContractRefusal` fault and called
        `_settle_unknown_start` directly, which asks the adapter nothing. So a
        driver that CREATED a runtime and then raised left that runtime
        unnamed and outside the ordinary destroy crossing -- even though
        `list` and exact `observe` would have found and identified it
        immediately.

        A fault says LESS about the start result than a typed refusal. That
        does not make exact reconciliation less necessary; it makes it more.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        adapter.start_failure = RuntimeError(
            "the driver failed after creating the runtime")
        adapter.listing = [{"runtime_id": adapter.runtime_id,
                            "labels": self.labels()}]
        with self.assertRaises(RuntimeError):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(self.row()["runtime_id"], adapter.runtime_id)
        self.assertEqual(self.row()["execution_runtime"], "running")
        # THE EXACT IDENTITY WAS ASKED ABOUT, which is what makes the answer
        # an observation rather than a listing membership.
        self.assertEqual(adapter.observed, [adapter.runtime_id])

    def test_a_fault_the_reconciliation_cannot_answer_is_still_uncertain(self):
        """The fallback is RETAINED. Reconciling first does not mean assuming
        it succeeds: a fault whose adapter can say nothing about what exists
        still ends `uncertain` rather than `start-requested`."""
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        adapter.start_failure = RuntimeError("the driver fell over")
        adapter.listing = []
        with self.assertRaises(RuntimeError):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(self.row()["execution_runtime"], "uncertain")
        self.assertIsNone(self.row()["runtime_id"])

    def test_both_kinds_of_failed_start_take_one_settlement_boundary(self):
        """A refusal and a fault differ in what they say about WHY the start
        did not complete, and not at all in what this manager has to do about
        it. Splitting them is how the fault path lost its reconciliation, so
        the two are driven here against the same adapter shape and required to
        reach the same durable row."""
        rows = {}
        for name, failure in (
                ("refusal", ContractRefusal("policy", "denied", "declined")),
                ("fault", RuntimeError("the driver fell over"))):
            case = TheRuntimeStateIsObservedAndNeverInferred(
                methodName="test_the_four_observations_stay_four_answers")
            case.setUp()
            try:
                inputs, _given, _assignment = case.delivered()
                adapter = Adapter()
                adapter.start_failure = failure
                adapter.listing = [{"runtime_id": adapter.runtime_id,
                                    "labels": case.labels()}]
                with case.assertRaises(type(failure)):
                    request_runtime_start(case.store, adapter,
                                          attempt_id=ATTEMPT, inputs=inputs)
                rows[name] = (case.row()["runtime_id"],
                              case.row()["execution_runtime"])
            finally:
                # `doCleanups`, NOT `tearDown`. Review [P2]: this fixture owns
                # its temporary directory and its `ControlStore` through
                # `addCleanup`, and no class here defines `tearDown` at all --
                # so `tearDown()` ran a no-op and released neither. A
                # regression that leaks the manager and store it opened cannot
                # be the durable gate for anything.
                case.doCleanups()
        self.assertEqual(rows["refusal"], rows["fault"], rows)

    def test_a_settlement_never_overwrites_a_truer_observation(self):
        """`uncertain` is written ONLY from `start-requested`.

        A reconciliation that recorded something truer before it failed is
        left alone: this closes a hole, and replacing an observation with
        `uncertain` would open a different one.
        """
        adapter, inputs = self.refused()
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()}]
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(self.row()["execution_runtime"], "running")
        self.assertEqual(self.row()["runtime_id"], "runtime-1")

    def test_a_reconciliation_that_also_fails_reports_both(self):
        """The operator needs the reason the start failed AND the reason the
        manager could not say what exists; replacing the first with the second
        loses the question."""
        adapter, inputs = self.refused()

        class Blind(Adapter):
            def list(self, operands):
                raise ContractRefusal("unavailable", "transport",
                                      "the engine could not be reached")

        blind = Blind()
        blind.start_failure = adapter.start_failure
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, blind, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertIn("refused to start", str(caught.exception))
        self.assertIn("could not be reached", str(caught.exception))


class CancellationFencesBeforeItStops(AttemptCase):

    def attached(self, attempt_id=ATTEMPT):
        self.claimed(attempt_id=attempt_id)
        activate_assignment(self.store, self.port, attempt_id=attempt_id,
                            expect=self.expect())
        self.adapter = Adapter()
        request_runtime_start(self.store, self.adapter,
                              attempt_id=attempt_id)
        return attempt_id

    def test_the_agent_is_ordered_before_the_runtime(self):
        """An agent told to stop after its runtime is already going away never
        hears the order, and the whole point of asking it is the cooperative
        shutdown a kill does not give."""
        order = []
        self.attached()
        agent = Agent()
        agent.cancel = lambda operands: order.append("agent")
        self.adapter.stop = lambda operands: order.append("runtime")
        request_cancellation(self.store, self.port, agent, self.adapter,
                             attempt_id=ATTEMPT)
        self.assertEqual(order, ["agent", "runtime"])

    def test_both_boundaries_receive_the_managers_own_operation_identity(self):
        self.attached()
        agent = Agent()
        answer = request_cancellation(self.store, self.port, agent,
                                      self.adapter, attempt_id=ATTEMPT)
        identity = answer["intent"]["attempt_id"]
        self.assertEqual(identity, ATTEMPT)
        self.assertEqual(agent.cancelled[0]["operation_id"],
                         self.adapter.stopped[0]["operation_id"])
        self.assertTrue(agent.cancelled[0]["operation_id"].startswith(
            "attempt.cancel:"))
        self.assertNotEqual(answer["intent"]["authority_operation_id"],
                            agent.cancelled[0]["operation_id"])

    def test_an_unreachable_agent_does_not_veto_the_stop(self):
        """Persistent agent unreachability is a REASON to stop the runtime.

        The authority has ALREADY fenced and ended the assignment by this point,
        so leaving the runtime alone would leave a fenced runtime running
        indefinitely.
        """
        self.attached()
        agent = Agent()
        agent.failure = RuntimeError("the provider is unreachable")
        with self.assertRaises(RuntimeError):
            request_cancellation(self.store, self.port, agent, self.adapter,
                                 attempt_id=ATTEMPT)
        self.assertEqual(len(self.adapter.stopped), 1)

    def test_neither_failure_hides_the_other(self):
        self.attached()
        agent = Agent()
        agent.failure = RuntimeError("no provider")
        self.adapter.stop_failure = RuntimeError("no runtime")
        with self.assertRaises(ExceptionGroup) as caught:
            request_cancellation(self.store, self.port, agent, self.adapter,
                                 attempt_id=ATTEMPT)
        self.assertEqual(len(caught.exception.exceptions), 2)

    def test_an_attempt_with_no_runtime_orders_nothing(self):
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        agent, adapter = Agent(), Adapter()
        answer = request_cancellation(self.store, self.port, agent, adapter,
                                      attempt_id=ATTEMPT)
        self.assertIs(answer["quiescence"]["ordered"], False)
        self.assertIn("nothing to stop", answer["quiescence"]["why"])
        self.assertEqual(agent.cancelled, [])

    def test_an_unactivated_attempt_has_no_generation_to_fence(self):
        self.recorded()
        with self.assertRaises(ContractRefusal) as caught:
            request_cancellation(self.store, self.port, Agent(), Adapter(),
                                 attempt_id=ATTEMPT)
        self.assertIn("no fixed assignment", caught.exception.message)

    def test_a_session_for_somebody_else_may_not_cancel(self):
        self.attached()
        self.session.participant = "baton.someone"
        port = AuthorityPort(self.session, fake_claim_signature)
        with self.assertRaises(ContractRefusal) as caught:
            request_cancellation(self.store, port, Agent(), Adapter(),
                                 attempt_id=ATTEMPT)
        self.assertEqual(caught.exception.code, "capability")

    def test_a_fence_for_another_generation_orders_nothing(self):
        """The authority may report a well-shaped fence for a different live
        assignment; it is not evidence that this attempt's generation ended."""
        self.attached()
        self.session.fence_answer["assignment"] = self.expect(generation=2)
        agent = Agent()

        with self.assertRaises(ContractRefusal):
            request_cancellation(self.store, self.port, agent, self.adapter,
                                 attempt_id=ATTEMPT)

        self.assertEqual(agent.cancelled, [])
        self.assertEqual(self.adapter.stopped, [])

    def test_a_swapped_pair_of_boundaries_refuses(self):
        """Two adjacent injected objects are easy to swap, so the shapes are
        checked -- a swap refuses instead of cancelling the wrong boundary."""
        self.attached()
        with self.assertRaises(ContractRefusal) as caught:
            request_cancellation(self.store, self.port, self.adapter, Agent(),
                                 attempt_id=ATTEMPT)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))

    def test_a_cancellation_in_flight_is_not_re_announced(self):
        """Moving the axis backwards to repeat an intent the runtime is already
        carrying out changes nothing about where the runtime is."""
        self.attached()
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="cancel-requested")
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="stopping")
        request_cancellation(self.store, self.port, Agent(), self.adapter,
                             attempt_id=ATTEMPT)
        self.assertEqual(self.row()["execution_runtime"], "stopping")


class TheAxesAgreeWithTheStore(AttemptCase):
    """The vocabulary is written in two languages, and they have to agree."""

    def test_every_axis_column_admits_exactly_its_own_vocabulary(self):
        for axis, moves in TRANSITIONS.items():
            with self.subTest(axis=axis):
                self.assertEqual(sorted(ATTEMPT_COLUMNS[axis].allowed),
                                 sorted(moves))

    def test_every_transition_names_a_value_of_its_own_axis(self):
        for axis, moves in TRANSITIONS.items():
            for state, after in moves.items():
                with self.subTest(axis=axis, state=state):
                    for value in after:
                        self.assertIn(value, moves)

    def test_the_map_is_frozen_all_the_way_down(self):
        with self.assertRaises(TypeError):
            TRANSITIONS["output"] = {}
        with self.assertRaises(TypeError):
            TRANSITIONS["output"]["sealed"] = ("open",)


if __name__ == "__main__":
    unittest.main()


class TheRuntimeStateIsObservedAndNeverInferred(TheRuntimeIsStartedOnceAndReconciled):
    """W26294. `list` answers WHICH containers carry an assignment's labels;
    only `observe` answers what one of them IS.

    W6636's composition found reconciliation reading `running` off membership
    in `ps --all` -- a listing that includes exited containers -- so an
    execution attempt recorded a running worker for one that had already
    finished, and the adapter had `observe` all along with nothing calling it.
    """

    def reconciled(self, observation, attempt_id=ATTEMPT):
        inputs, _given, _assignment = self.delivered(attempt_id)
        adapter = Adapter()
        adapter.observation = observation
        request_runtime_start(self.store, adapter, attempt_id=attempt_id,
                              inputs=inputs)
        return adapter

    def axis(self, attempt_id=ATTEMPT):
        return self.row(attempt_id)["execution_runtime"]

    def test_positive_absence_is_recorded_as_destruction(self):
        """`absent` is POSITIVE evidence about one exact identity.

        The adapter answers it only when the engine says that container does
        not exist, which is the certified evidence the transition map's own
        note was waiting for: a reconciliation must be able to record what it
        finds "including positive destruction". What stays forbidden is
        inferring it from a failure to LOOK, and that is `uncertain`, which the
        map still refuses to let become `destroyed`.

        Without this, mapping absence to uncertainty changes no verdict --
        measured -- and the two answers would be indistinguishable through the
        seam the acceptance says must keep them distinct.
        """
        adapter = self.reconciled({"state": "absent", "why": "no such thing",
                                   "mounts": None})
        self.assertEqual(self.axis(), "destroyed")
        self.assertEqual(adapter.observed, [adapter.runtime_id])

    def test_the_four_observations_stay_four_answers(self):
        """Running, quiescent, absent and uncertain remain distinguishable.

        The acceptance's own clause. Asserted as the whole mapping rather than
        one state at a time, so a change that collapsed two of them fails here
        rather than in whichever case happened to cover the survivor.
        """
        self.assertEqual(
            OBSERVED_RUNTIME,
            {"running": "running", "quiescent": "quiescent",
             "absent": "destroyed", "uncertain": "uncertain"})
        self.assertEqual(len(set(OBSERVED_RUNTIME.values())), 4)

    def test_an_answer_that_is_not_a_document_is_uncertain_and_says_so(self):
        """Review [P0] INVERTED THIS CASE'S OUTCOME, and the reason it exists
        survives the inversion.

        It used to require a propagated refusal. That refusal was the defect:
        it left the durable axis at whatever it said before, including
        `running`, so an observation that FAILED was indistinguishable from one
        that answered liveness. Every failed or unrecognised exact observation
        is now a durable `uncertain`.

        WHAT IT STILL ESTABLISHES is the EXACT reason. Measured once already:
        removing the document check left the missing-member check answering the
        same input for a different reason, so a case that only asserted
        "uncertain" would establish nothing. A string has no `state` member
        either, and the reason is what tells the two apart.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        adapter.observation = "not a document"
        answer = request_runtime_start(self.store, adapter,
                                       attempt_id=ATTEMPT, inputs=inputs)
        self.assertEqual(answer["observed"], "uncertain")
        self.assertIn("is a document", answer["why"])
        self.assertEqual(self.row()["execution_runtime"], "uncertain")
        self.assertNotEqual(self.row()["execution_runtime"], "running")

    def test_an_adapter_without_observe_refuses_as_a_capability(self):
        """Typed rather than discovered by `AttributeError`.

        Reconciliation already types `list`; `observe` is now equally required,
        and an adapter that has neither is a narrow adapter this seam cannot
        use. Measured: without the capability check the missing method surfaces
        as an `AttributeError` outside this contract's taxonomy.
        """
        inputs, _given, _assignment = self.delivered()

        class Narrow(Adapter):
            observe = None

        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, Narrow(), attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertIn("capability", str(caught.exception))

    # -- re-review [P1]: the answer is rebuilt, never merged ---------------
    #
    # `_attach` is effectively-once, so every reconciliation after the first
    # REPLAYS the first pass's document. Refreshing `observed` on top of that
    # replay left `why` as old as the attachment, and the two directions fail
    # in opposite ways -- so they are two cases rather than one, and a third
    # walks the whole document across four passes because the members that
    # must NOT move are as much of the contract as the ones that must.

    def attached_twice(self, first, second):
        """One attachment, then a second reconciliation over it."""
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        adapter.observation = first
        opening = request_runtime_start(self.store, adapter,
                                        attempt_id=ATTEMPT, inputs=inputs)
        adapter.observation = second
        return opening, reconcile_runtime(self.store, adapter,
                                          attempt_id=ATTEMPT)

    def test_a_later_inconclusive_observation_carries_its_own_reason(self):
        """First `running`, then a failed observation.

        The replayed document had no reason, because the observation it was
        built from was conclusive. Refreshing `observed` alone therefore
        answered `uncertain` and explained nothing -- and an inconclusive state
        with no reason is the one answer an operator cannot act on.
        """
        opening, answer = self.attached_twice(
            {"state": "running", "why": "it is up", "mounts": None},
            ContractRefusal("unavailable", "transport",
                            "the observer failed"))
        self.assertEqual(opening["observed"], "running")
        self.assertNotIn("why", opening)
        self.assertEqual(answer["observed"], "uncertain")
        self.assertIn("why", answer)
        self.assertIn("the observer failed", answer["why"])
        self.assertEqual(self.row()["execution_runtime"], "uncertain")

    def test_a_later_conclusive_observation_drops_the_stale_reason(self):
        """First a failed observation, then `running` -- the more dangerous
        direction.

        The answer said the runtime is UP while carrying the prose of the
        failure that could not see it. A reader has no way to tell a reason
        that describes the current state from one left over from an earlier
        pass, so a conclusive answer must carry none at all.
        """
        opening, answer = self.attached_twice(
            ContractRefusal("unavailable", "transport",
                            "the original observer failed"),
            {"state": "running", "why": "it is up", "mounts": None})
        self.assertEqual(opening["observed"], "uncertain")
        self.assertIn("why", opening)
        self.assertEqual(answer["observed"], "running")
        self.assertNotIn("why", answer)
        self.assertEqual(self.row()["execution_runtime"], "running")

    def test_the_fixed_identity_survives_every_later_observation(self):
        """Four passes over ONE attachment, checking the WHOLE document.

        The two cases above check the member that was wrong. This one checks
        what must not move while it moves: the attempt, the decision and the
        fixed runtime identity are what the effectively-once attachment is
        authoritative about, and a rebuild that composed any of them from this
        call rather than from the attachment would be a different defect
        wearing the same shape.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        opening = request_runtime_start(self.store, adapter,
                                        attempt_id=ATTEMPT, inputs=inputs)
        fixed = opening["runtime_id"]
        walked = []
        for observation, expected in (
                (ContractRefusal("unavailable", "transport", "no answer"),
                 "uncertain"),
                ({"state": "running", "why": "up", "mounts": None},
                 "running"),
                ({"state": "quiescent", "why": "exited 0", "mounts": None},
                 "quiescent"),
                ("not a document", "uncertain")):
            adapter.observation = observation
            answer = reconcile_runtime(self.store, adapter,
                                       attempt_id=ATTEMPT)
            walked.append(answer["observed"])
            self.assertEqual(answer["attempt_id"], ATTEMPT)
            self.assertEqual(answer["decision"], "attached")
            self.assertEqual(answer["runtime_id"], fixed)
            self.assertEqual(answer["observed"], expected)
            # THE REASON RIDES EXACTLY WHEN THE ANSWER IS INCONCLUSIVE, which
            # is the rule stated as one predicate over the document rather
            # than as four separate expectations.
            self.assertEqual("why" in answer, expected == "uncertain",
                             answer)
            # And the durable axis agrees with what was answered on every
            # pass: the document and the record are one act.
            self.assertEqual(self.row()["execution_runtime"], expected)
        self.assertEqual(
            walked, ["uncertain", "running", "quiescent", "uncertain"])

    def test_the_recorded_attachment_keeps_the_reason_it_was_made_with(self):
        """The JOURNALLED document, not the returned one.

        Rebuilding the answer made it independent of what the attachment
        stored, which is right -- and it also meant nothing was left checking
        the stored document at all. That is a real coverage loss and it showed
        up as a mutation that stopped being caught: dropping `why` from the
        `_attach` call changed no answer any case looked at.

        The stored document is what an exact retry replays and what an
        operator reads out of the operation journal, so an attachment made
        from an inconclusive observation has to carry its reason there too.
        """
        inputs, _given, _assignment = self.delivered()
        adapter = Adapter()
        adapter.observation = ContractRefusal(
            "unavailable", "transport", "the observer failed")
        answer = request_runtime_start(self.store, adapter,
                                       attempt_id=ATTEMPT, inputs=inputs)
        runtime = answer["runtime_id"]
        found, stored = self.store.replay(
            f"attempt.attach:{ATTEMPT}:{runtime}",
            manager_signature("attempt.attach",
                              {"attempt_id": ATTEMPT,
                               "runtime_id": runtime}),
            kind="attempt.attach")
        self.assertTrue(found)
        self.assertEqual(stored["observed"], "uncertain")
        self.assertIn("why", stored)
        self.assertIn("the observer failed", stored["why"])


class TheFailedStartReachesTheRuledEnding(
        ARefusedStartIsSettledRatherThanStranded):
    """W32648's second half: the cleanup crossing the record authorizes.

    Approver ruling M33800. A start that created a container and then failed
    has an exact runtime, NO worker disposition this manager may invent, NO
    frozen result and NO intake receipt -- so `authorize_cleanup`, whose whole
    authorization is that receipt, has no way through. The regression this
    Work replaces got through by observing a disposition and manufacturing a
    frozen output, which is the fabrication the finding exists to remove.

    THE ORDER IS THE RULING'S and each case drives one part of it: fence at the
    authority, remove the exact attached runtime, positively observe absence,
    settle the delivery roots, LEAVE the untrusted result directory where it
    is, and end at `retained`.
    """

    def failed(self, failure=None, listing=True):
        """An attempt whose start created a runtime and then failed."""
        adapter, inputs = self.refused(failure=failure)
        if listing:
            adapter.listing = [{"runtime_id": "runtime-1",
                                "labels": self.labels()}]
        else:
            adapter.listing = []
        with self.assertRaises(Exception):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        return adapter

    def ended(self):
        """THE ASSIGNMENT IS OVER, which this ending requires before it runs."""
        self.session.live_assignment = None

    def custodian(self, **overrides):
        """W34998's capability, and ONLY it: an adapter carrying `destroy`
        instead would let this crossing reach the receipt-authorized path."""
        class Custodian:
            def __init__(self):
                self.commands = []

            def destroy_failed_start(self, command):
                self.commands.append(dict(command))
                return {"runtime_id": command["runtime_id"],
                        "state": "absent",
                        "why": "the engine answered that this exact identity "
                               "does not exist",
                        "credentials": {"lifecycle_state": "not-delivered"},
                        "launch": {"lifecycle_state": "not-delivered"},
                        **overrides}
        return Custodian()

    def settled(self, adapter=None, **overrides):
        from baton_v12.worker_manager import authorize_failed_start_cleanup
        return authorize_failed_start_cleanup(
            self.store, self.port, adapter or self.custodian(**overrides),
            attempt_id=ATTEMPT, retention_policy_digest="sha256:" + "7" * 64)

    def test_the_ending_is_retained_and_nothing_was_fabricated(self):
        """THE ACCEPTANCE, in one case.

        No caller wrote a worker disposition and no output was frozen, and the
        cleanup axis still reaches a terminal ending.
        """
        self.failed()
        self.ended()
        answered = self.settled()
        self.assertEqual(answered["cleanup"], "retained")
        self.assertEqual(answered["state"], "absent")
        self.assertEqual(self.row()["cleanup"], "retained")
        self.assertEqual(self.row()["execution_runtime"], "destroyed")
        # THE TWO THINGS THIS ENDING MUST NEVER TOUCH.
        self.assertEqual(self.row()["worker_disposition"], "none")
        self.assertEqual(self.row()["output"], "open")

    def test_the_record_is_what_authorizes_it(self):
        """Not an intake receipt, and the body says which.

        The digest that crosses is the manager's own account of the start that
        failed -- read back from the journal it was written to, not recomposed
        -- and it arrives in `failed_start_record_digest`, never in
        `intake_receipt_digest`.
        """
        from baton_v12.worker_manager import attempts as attempts_module
        from baton_v12.contracts import digest
        self.failed()
        self.ended()
        custodian = self.custodian()
        self.settled(custodian)
        body = custodian.commands[0]
        self.assertNotIn("intake_receipt_digest", body)
        # THE DIGEST IS OVER THE DECODED RECORD -- the document this manager
        # composed -- rather than over whatever bytes the journal happens to
        # store it as.
        _, committed = self.store.replay(
            attempts_module.start_failure_operation_id(self.row()),
            self.store.operation_record(
                attempts_module.start_failure_operation_id(
                    self.row()))["signature"],
            kind="runtime.start-failed")
        self.assertEqual(body["failed_start_record_digest"], digest(committed))
        self.assertEqual(body["runtime_id"], "runtime-1")

    def test_the_record_must_name_the_runtime_being_destroyed(self):
        """A failed-start record for one runtime authorizes no sibling.

        The journal is the independent durable account of what the failed
        start created.  If the adopted attempt row now names another runtime,
        cleanup must refuse before crossing the adapter rather than combining
        the old authorization digest with the new target identity.
        """
        worker_manager.configure_workspace_group(self.store, os.getgid())
        self.failed()
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ? WHERE runtime_attempt_id = ?",
            ("runtime-sibling", ATTEMPT))
        self.ended()
        custodian = self.custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertEqual(custodian.commands, [])

    def test_without_the_record_there_is_no_authorization(self):
        """A runtime attached by something other than a failed start is not
        this ending's to remove."""
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="running")
        self.ended()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled()
        self.assertIn("holds no committed failed-start record",
                      caught.exception.message)

    def test_a_row_of_another_kind_authorizes_nothing(self):
        """An identity is not a warrant.

        The record is looked up by an identity DERIVED from the attempt, so a
        committed row sitting at that identity under another kind would have
        authorized a destroy on the strength of being findable. The kind is
        checked because a store is data this process did not write on this run.
        """
        self.failed()
        self.ended()
        from baton_v12.worker_manager import attempts as attempts_module
        operation_id = attempts_module.start_failure_operation_id(self.row())
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            beside.execute(
                "UPDATE operations SET kind = ? WHERE operation_id = ?",
                ("runtime.start", operation_id))
        finally:
            beside.close()
        custodian = self.custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("rather than a failed-start record",
                      caught.exception.message)
        self.assertEqual(custodian.commands, [])

    def test_the_assignment_is_fenced_before_anything_is_destroyed(self):
        """The ruling's ordering, and the adapter is the witness."""
        self.failed()
        custodian = self.custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian)
        self.assertIn("still the live assignment", caught.exception.message)
        self.assertEqual(custodian.commands, [],
                         "a live assignment reached the adapter")
        self.assertEqual(self.row()["cleanup"], "pending")

    def test_an_uncertain_attempt_has_nothing_to_remove(self):
        """A failed start reaches `uncertain` exactly when reconciliation
        could not establish what exists -- so this is the case, not an edge."""
        self.failed(listing=False)
        self.assertEqual(self.row()["execution_runtime"], "uncertain")
        self.ended()
        custodian = self.custodian()
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(custodian)
        self.assertEqual(caught.exception.code, "quiescence-unknown")
        self.assertEqual(custodian.commands, [])
        self.assertEqual(self.row()["cleanup"], "pending")

    def test_a_surviving_runtime_is_a_failed_cleanup_and_not_an_ending(self):
        self.failed()
        self.ended()
        answered = self.settled(state="running",
                                why="the engine still reports this identity")
        self.assertEqual(answered["cleanup"], "failed")
        self.assertEqual(self.row()["cleanup"], "failed")

    def test_an_unresolved_provider_settles_nothing(self):
        """Delivery roots are settled on positive absence and on nothing
        else, which is the owner this crossing REUSES rather than repeats."""
        self.failed()
        self.ended()
        answered = self.settled(
            launch={"lifecycle_state": "unresolved",
                    "why": "the launch root could not be proved gone"})
        self.assertNotIn("cleanup", answered)
        self.assertEqual(self.row()["cleanup"], "pending")

    def test_an_exact_retry_replays_and_a_changed_policy_collides(self):
        from baton_v12.worker_manager import authorize_failed_start_cleanup
        self.failed()
        self.ended()
        first = self.settled()
        again = self.settled()
        self.assertEqual(again, first)
        # A DIFFERENT POLICY IS A DIFFERENT ACT, and it arrives after an
        # ending: the terminal-cleanup refusal is what it meets.
        with self.assertRaises(ContractRefusal) as caught:
            authorize_failed_start_cleanup(
                self.store, self.port, self.custodian(), attempt_id=ATTEMPT,
                retention_policy_digest="sha256:" + "8" * 64)
        self.assertEqual(caught.exception.code, "already-terminal")

    def test_a_restart_between_the_removal_and_the_ending_converges(self):
        """The journal is written after the engine call, so a crash between
        them leaves cleanup `pending` -- and the next authorization runs the
        removal again, which is safe because a removal is force-then-inspect
        and an identity already gone answers absent."""
        self.failed()
        self.ended()
        custodian = self.custodian()
        restarted = ControlStore.open(self.path, incarnation="manager-2",
                                      clock=lambda: NOW)
        self.addCleanup(restarted.close)
        from baton_v12.worker_manager import authorize_failed_start_cleanup
        answered = authorize_failed_start_cleanup(
            restarted, self.port, custodian, attempt_id=ATTEMPT,
            retention_policy_digest="sha256:" + "7" * 64)
        self.assertEqual(answered["cleanup"], "retained")
        self.assertEqual(self.row()["cleanup"], "retained")

    def test_the_untrusted_result_directory_is_left_where_it_is(self):
        """M33800's custody boundary: the existing unique per-attempt
        directory begins untrusted and stays untrusted. This ending deletes
        nothing and creates no second result."""
        self.failed()
        # THE ATTEMPT'S OWN WORKSPACE, allocated through the canonical
        # boundary exactly as a delivery's is -- so what this case proves is
        # left alone is a real per-attempt directory rather than a temporary
        # one it invented.
        roots = assignment_workspace(self.group,
                                     input_roots.storage_under(self),
                                     "result-custody")
        place = os.path.join(roots["workspace"], "result-attempt-1")
        os.makedirs(place, exist_ok=True)
        with open(os.path.join(place, "sentinel.txt"), "wb") as handle:
            handle.write(b"whatever the worker got to")
        self.ended()
        self.settled()
        with open(os.path.join(place, "sentinel.txt"), "rb") as handle:
            self.assertEqual(handle.read(), b"whatever the worker got to")
        self.assertEqual(
            [dict(one) for one in self.store._connection.execute(
                "SELECT * FROM outputs")], [])
        self.assertEqual(
            [dict(one) for one in self.store._connection.execute(
                "SELECT * FROM intakes")], [])

    def test_a_sibling_attempt_is_untouched(self):
        self.failed()
        self.recorded("attempt-sibling")
        self.ended()
        self.settled()
        sibling = self.row("attempt-sibling")
        self.assertEqual(sibling["cleanup"], "pending")
        self.assertEqual(sibling["execution_runtime"], "not-started")


class TheFailedStartIsDurablyRecorded(ARefusedStartIsSettledRatherThanStranded):
    """W32648, approver ruling M33800: the manager-owned failure record.

    Attaching the runtime closed the identity leak; it did not leave an
    authorized ENDING.  Intake requires a frozen result and a receipt, and
    output freeze requires a terminal `worker_disposition` already proved on
    the attempt -- so the only way to reach cleanup was to observe a
    disposition the manager cannot know.  A container created before a fault
    may also have run code, which is exactly why `unable` would be this
    manager inventing a worker's account of itself.

    So the failure becomes its own journalled act.  THE JOURNAL IS THE RECORD
    and no new table is: `store.transact` stores the sealed document as the
    operation's result, so it is durable, replayable, and collides on any
    changed fact -- which is the effectively-once guarantee the acceptance
    asks for rather than a mechanism invented here.
    """

    def records(self):
        return [row for row in self.store._connection.execute(
            "SELECT * FROM operations WHERE kind = 'runtime.start-failed'")]

    def record(self):
        found = self.records()
        self.assertEqual(len(found), 1, [dict(one) for one in found])
        return json.loads(dict(found[0])["result"])

    def test_a_refused_start_is_journalled_with_its_exact_typed_pair(self):
        adapter, inputs = self.refused()
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()}]
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        record = self.record()
        self.assertEqual(record["attempt_id"], ATTEMPT)
        self.assertEqual(record["failure"], {
            "kind": "refusal", "category": "policy", "code": "denied",
            "message": "the engine refused to start this runtime"})
        # THE RUNTIME THE RECONCILIATION ATTACHED, so the record and the
        # attempt row agree about what the destroy crossing will name.
        self.assertEqual(record["runtime_id"], "runtime-1")
        self.assertEqual(record["runtime_id"], self.row()["runtime_id"])
        started = [dict(one) for one in self.store._connection.execute(
            "SELECT * FROM operations WHERE kind = 'runtime.start'")]
        self.assertEqual(len(started), 1, started)
        self.assertEqual(record["start_operation_id"],
                         started[0]["operation_id"])

    def test_a_fault_is_recorded_as_a_fault_and_not_as_a_refusal(self):
        """The original typed fault, preserved rather than reworded.

        The closed pairing has no `refused/start-failed`, and this module's own
        history says why -- a wrapper that retyped every failed start as one
        broke three boundary probes.  So a fault is recorded as a fault, with
        its own class and text.
        """
        adapter, inputs = self.refused(failure=RuntimeError("the socket went"))
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()}]
        with self.assertRaises(RuntimeError):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(self.record()["failure"], {
            "kind": "fault", "fault": "RuntimeError",
            "message": "the socket went"})

    def test_the_record_never_writes_a_worker_disposition(self):
        """The distinction the whole record exists for."""
        adapter, inputs = self.refused()
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()}]
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertEqual(self.row()["worker_disposition"], "none")
        self.assertEqual(self.row()["output"], "open")

    def test_an_exact_retry_replays_the_one_record(self):
        """Effectively once.  A second identical failure is the same act."""
        adapter, inputs = self.refused()
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()}]
        for _ in range(2):
            with self.assertRaises(ContractRefusal):
                request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                      inputs=inputs)
        self.assertEqual(len(self.records()), 1)

    def test_a_changed_failure_fact_collides_and_the_first_record_stands(self):
        """The acceptance's rule, and the first spelling of this case asserted
        its opposite.

        RE-REVIEW [P0]: the operation id hashed the attached runtime and the
        typed failure, so a changed fact chose a DIFFERENT id and never reached
        the journal's collision guard -- and this case required the two rows,
        which made it durable evidence for the wrong contract.

        The id is now stable for the one start act and the changeable facts are
        in the signature, so a changed fact arrives at the same id with another
        signature and fails closed. The first account -- written when the
        manager knew most -- is the one that stands.
        """
        adapter, inputs = self.refused()
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()}]
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        first = self.record()

        # THE SAME START ACT, A DIFFERENT TYPED FAILURE.
        with self.assertRaises(ContractRefusal) as caught:
            attempts_module._record_and_raise_start_failure(
                self.store, ATTEMPT,
                {"kind": "refusal", "category": "integrity", "code": "schema",
                 "message": "a different failure entirely"})
        self.assertEqual(caught.exception.category, "refused")
        self.assertEqual(caught.exception.code, "operation-collision")
        # ONE ROW, AND IT IS THE FIRST ONE.
        self.assertEqual(len(self.records()), 1)
        self.assertEqual(self.record(), first)

    def test_the_recorder_reports_a_collision_rather_than_raising_it(self):
        """The recorder runs while another failure is on its way out.

        So the collision is appended to what the caller is already reporting
        rather than replacing it -- a recorder that threw would substitute its
        own problem for the one that actually happened.
        """
        adapter, inputs = self.refused()
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()}]
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        said = attempts_module._record_start_failure(
            self.store, ATTEMPT,
            {"kind": "refusal", "category": "integrity", "code": "schema",
             "message": "a different failure entirely"})
        self.assertIn("already holds a different failure record", said)
        self.assertEqual(len(self.records()), 1)

    def test_a_start_nothing_could_reconcile_still_records_the_failure(self):
        """`uncertain` is an ending too, and it is recorded as one.

        The record names `runtime_id: None`, which is the honest statement that
        nothing was established -- not a claim that nothing was created.
        """
        adapter, inputs = self.refused()
        adapter.listing = ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            "the engine could not be listed")
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        record = self.record()
        self.assertIsNone(record["runtime_id"])
        self.assertEqual(record["execution_runtime"], "uncertain")
        self.assertEqual(self.row()["execution_runtime"], "uncertain")

    def test_the_refusal_an_operator_reads_names_the_record(self):
        adapter, inputs = self.refused()
        adapter.listing = [{"runtime_id": "runtime-1",
                            "labels": self.labels()}]
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, adapter, attempt_id=ATTEMPT,
                                  inputs=inputs)
        self.assertIn("the start failure is journalled as",
                      caught.exception.message)
        self.assertIn("runtime.start-failed:", caught.exception.message)
