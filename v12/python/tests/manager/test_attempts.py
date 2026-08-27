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
from baton_v12.worker_manager.attempts import authorize_input_root
from baton_v12.worker_manager.schema import ATTEMPT_COLUMNS
from baton_v12.worker_manager.workspaces import (assignment_workspace,
                                                 compose_input_root)

from . import input_roots
from .test_offers import (FakeSession, NOW, PROFILE, UUID, WHO, WORK,
                          fake_claim_signature)


class Adapter:
    """The narrow runtime adapter, with every answer a test may need to set."""

    def __init__(self, runtime_id="runtime-1"):
        self.runtime_id = runtime_id
        self.started = []
        self.stopped = []
        self.listing = None
        self.start_answer = None
        self.stop_failure = None

    def start(self, operands):
        self.started.append(operands)
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
                "issued_at, expires_at, state, intent_digest, accepted_at, "
                "settle_by, claim_operation_id, claim_signature) VALUES "
                "('offer-2', ?, ?, ?, ?, 'm', 'd', 'd', ?, 'v', 1, ?, ?, "
                "'claimed', 'i', ?, ?, 'claim:x', 's')",
                (WORK, UUID, WHO, ATTEMPT, PROFILE, NOW, NOW, NOW, NOW))
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
                              "authority_uuid": work_ref["authority_uuid"]}
        self.session.claim_answer = dict(live)
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
        inputs = assignment_workspace(storage, attempt_id)["inputs"]
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
                inputs = assignment_workspace(storage, elsewhere)["inputs"]
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
        inputs = assignment_workspace(storage, "other-input")["inputs"]
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

    def test_an_empty_listing_is_uncertainty_and_the_retry_path_is_closed(self):
        """"The adapter reports nothing" and "nothing exists" are different
        facts."""
        self.activated()
        adapter = Adapter()
        adapter.listing = []
        answer = reconcile_runtime(self.store, adapter, attempt_id=ATTEMPT)
        self.assertEqual(answer["decision"], "uncertain")
        self.assertIn("certified adapter evidence", answer["why"])
        self.assertEqual(self.row()["execution_runtime"], "uncertain")

    def test_a_started_runtime_the_adapter_cannot_see_is_uncertain(self):
        self.activated()
        adapter = Adapter()
        adapter.listing = []
        answer = request_runtime_start(self.store, adapter,
                                       attempt_id=ATTEMPT)
        self.assertEqual(answer["decision"], "uncertain")
        self.assertIn("a second start could leave two runtimes", answer["why"])

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
