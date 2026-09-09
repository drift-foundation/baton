"""W32649 — one runtime lane, across a predecessor and a successor.

`posture_slots` is keyed `(runtime_attempt_id, posture)`, so a successor got a
different slot and no start precondition consulted a predecessor whose
container was absent while its deliveries, custody or retryable cleanup were
still unsettled.  The suite that covered the ordering could start a successor
only AFTER cleanup -- but the same successor would also have started BEFORE it,
so the order was a property of the test rather than an enforced invariant.

WHY THE WINDOW EXISTS AT ALL, since a lane is only worth having if it does.
The authority's claim slot and this manager's cleanup answer different
questions at different times: an assignment may END -- releasing the claim, so
the Work is claimable again -- while roots, deliveries and custody are still
being taken down.  Every case below lives in that window.

THE IDENTITY IS THE POINT OF THE WORK, and it is measured rather than asserted:
it is `(authority_uuid, work_id, principal, effective_scope)`, so two endpoint
addresses the authority maps to one principal contend for ONE lane, and the
attempt id and the generation -- both of which change between a predecessor and
its successor -- are deliberately absent.  W16821 separated the principal from
the endpoint and W16823 carried it onto the attempt row; this reads what they
established rather than parsing a participant prefix, which is the failure the
bound acceptance names by name.
"""

import copy
import os
import sqlite3
import tempfile
import threading
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (ControlStore, accept_offer,
                                      activate_assignment, authorize_cleanup,
                                      issue_offer, lanes, observe,
                                      record_attempt, request_runtime_start,
                                      runtime_lane, submit_claim)
from baton_v12.worker_manager import decide_retention
from baton_v12.worker_manager import schema
from baton_v12.worker_manager.schema import RUNTIME_LANE_COLUMNS

from .test_attempts import Adapter as RuntimeAdapter
from .test_intake import Custodian, IntakeCase, RETENTION
from .test_output import ATTEMPT, AUTHORITY, JOB, POLICY
from .test_offers import NOW, PRINCIPAL, SCOPE, WHO


class CancellingAgent:
    """The agent capability `request_cancellation` announces the fence to."""

    def __init__(self):
        self.cancelled = []

    def cancel(self, operands):
        self.cancelled.append(dict(operands))
        return {"acknowledged": True}


class LaneCase(IntakeCase):
    """W6629's whole arc, asked one question it was not asked."""

    def attempt_row(self, attempt_id=ATTEMPT):
        """This suite reads OTHER attempts' rows too, which the shared fixture
        does not: it was written for one attempt, and a lane spans two."""
        found = self.store._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (attempt_id,)).fetchone()
        return None if found is None else {k: found[k] for k in found.keys()}

    def lanes(self):
        found = self.store._connection.execute(
            "SELECT * FROM runtime_lanes ORDER BY lane_id").fetchall()
        return [{key: row[key] for key in row.keys()} for row in found]

    def reference(self, attempt_id=ATTEMPT):
        return lanes.lane_reference(self.attempt_row(attempt_id))

    def successor_start(self, attempt_id="attempt-successor",
                        principal=PRINCIPAL):
        """A second attempt over the SAME assignment, activated by hand.

        By hand because the offer path allows one live offer per Work and this
        window is precisely the one where the authority would let a second
        claim through -- which is the state the lane is about. The row is
        written with the columns `activate_assignment` writes, so what the
        lane reads is what activation would have given it.
        """
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            row = self.attempt_row()
            beside.execute(
                "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
                "adapter_digest, profile_digest, input_digest, policy_digest, "
                "created_at, work_id, authority_uuid, assignment_participant, "
                "assignment_generation, assignment_claim_event_seq, "
                "assignment_principal, assignment_scope, assignment_role, "
                "assignment_grant, assignment_policy_generation, "
                "observation_seq) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
                (attempt_id, row["adapter_name"], row["adapter_digest"],
                 row["profile_digest"], None,
                 row["policy_digest"], row["created_at"], row["work_id"],
                 row["authority_uuid"], row["assignment_participant"],
                 (row["assignment_generation"] or 0) + 1,
                 (row["assignment_claim_event_seq"] or 0) + 2,
                 principal, row["assignment_scope"], row["assignment_role"],
                 row["assignment_grant"], row["assignment_policy_generation"]))
        finally:
            beside.close()
        return attempt_id

    def cleanup_settled(self, attempt_id=ATTEMPT, **endings):
        """Drive the whole cleanup to its ending, as `test_intake` does."""
        self.ended()
        return authorize_cleanup(
            self.store, self.port,
            Custodian(destroyed={"state": "absent",
                                 "why": "the engine answered that this exact "
                                        "identity does not exist",
                                 "credentials":
                                     {"lifecycle_state": "not-delivered"},
                                 "launch":
                                     {"lifecycle_state": "not-delivered"},
                                 **endings}),
            attempt_id=attempt_id, retention_policy_digest=RETENTION)


class TheIdentityIsTheAssignmentAndNotTheAttempt(LaneCase):

    def test_the_lane_is_the_four_authority_owned_parts(self):
        self.attempt()
        reference = self.reference()
        self.assertEqual(sorted(reference), sorted(lanes.LANE_PARTS))
        self.assertEqual(reference["authority_uuid"], AUTHORITY)
        self.assertEqual(reference["work_id"], JOB)
        self.assertEqual(reference["principal"], PRINCIPAL)
        self.assertEqual(reference["effective_scope"], SCOPE)
        # NEITHER OF THE TWO THAT CHANGE BETWEEN ATTEMPTS is in it, which is
        # what makes the lane span them at all.
        self.assertNotIn(ATTEMPT, str(reference))
        self.assertNotIn("generation", reference)

    def test_the_lane_is_not_keyed_on_the_endpoint_spelling(self):
        """The acceptance's own sentence, as a measurement.

        Two endpoint addresses the authority maps to ONE principal compute one
        lane id. A lane keyed on the participant would compute two -- which is
        the defect W16821 exists to remove, arriving in the manager.
        """
        row = dict(self.attempt_row(self.attempt()))
        mine = lanes._lane_id(lanes.lane_reference(row))
        theirs = lanes._lane_id(lanes.lane_reference(
            dict(row, assignment_participant="review.claude")))
        self.assertEqual(mine, theirs)
        # ...and two distinct PRINCIPALS are isolated, which is the other half.
        other = lanes._lane_id(lanes.lane_reference(
            dict(row, assignment_principal="principal:somebody-else")))
        self.assertNotEqual(mine, other)
        # As is a distinct effective scope.
        self.assertNotEqual(mine, lanes._lane_id(lanes.lane_reference(
            dict(row, assignment_scope="scope:elsewhere"))))

    def test_an_unactivated_attempt_belongs_to_no_lane(self):
        from baton_v12.worker_manager import record_attempt
        record_attempt(self.store, attempt_id="loose", adapter_name="acp",
                       adapter_digest="sha256:" + "a" * 64,
                       profile_digest=self.attempt_row(self.attempt())
                       ["profile_digest"])
        with self.assertRaises(ContractRefusal) as caught:
            lanes.lane_reference(self.attempt_row("loose"))
        self.assertIn("belongs to no lane", caught.exception.message)

    def test_the_name_is_derived_and_survives_a_restart(self):
        """DERIVED rather than minted, so nothing has to be remembered.

        A restarted manager recomputes the same lane from the same attempt row,
        which is what lets two managers racing one successor contend at all
        instead of each inserting a name of its own.
        """
        self.attempt()
        before = lanes._lane_id(self.reference())
        reopened = ControlStore.open(self.path, incarnation="manager-2",
                                     clock=lambda: NOW_LATER)
        self.addCleanup(reopened.close)
        row = reopened._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (ATTEMPT,)).fetchone()
        self.assertEqual(
            lanes._lane_id(lanes.lane_reference({k: row[k]
                                                for k in row.keys()})),
            before)


NOW_LATER = "2026-08-24T00:20:00.000Z"


class TheLaneIsTakenBeforeAnythingIsCreated(LaneCase):

    def test_a_start_occupies_the_lane_in_the_same_write(self):
        self.attempt()
        held = self.lanes()
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["holder"], ATTEMPT)
        self.assertEqual(held[0]["principal"], PRINCIPAL)
        self.assertEqual(held[0]["lane_id"], lanes._lane_id(self.reference()))
        # THE ROW IS OWNED like any other persisted row this manager reads.
        self.assertEqual(sorted(held[0]), sorted(RUNTIME_LANE_COLUMNS))

    def test_a_second_start_neither_double_takes_nor_leaks(self):
        """Crash/retry must neither leak nor double-release capacity.

        A second `INSERT` under one holder would fail the lane's primary key
        and turn an ordinary retry into an unrecognisable refusal. It never
        gets there: the execution axis is already past `not-started`, so the
        second start is refused as the ALREADY-TERMINAL precondition it is,
        before the lane is touched at all -- and the lane is still held exactly
        once, by the attempt that took it.
        """
        self.attempt()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, RuntimeAdapter(),
                                  attempt_id=ATTEMPT, inputs=None)
        self.assertEqual(caught.exception.code, "already-terminal")
        held = self.lanes()
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["holder"], ATTEMPT)

    def test_releasing_a_lane_twice_frees_nothing_extra(self):
        """The other half of "neither leak nor double-release".

        A release is a delete bound to the holder, so a second one removes
        nothing and says so -- which is what a crash between the delete and
        the commit has to be safe against.
        """
        self.attempt()
        reference = self.reference()
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            self.assertTrue(lanes._release_lane(
                beside, attempt_id=ATTEMPT, reference=reference, why="first"))
            self.assertFalse(lanes._release_lane(
                beside, attempt_id=ATTEMPT, reference=reference,
                why="again"))
        finally:
            beside.close()
        self.assertEqual(self.lanes(), [])


class ASuccessorWaitsForItsPredecessor(LaneCase):
    """The invariant the previous suite could only observe by ordering."""

    def test_a_successor_reaches_no_engine_while_cleanup_is_open(self):
        """THE ACCEPTANCE'S FIRST CASE, and the engine is the witness.

        The predecessor's runtime is gone and its cleanup is not settled. A
        successor is refused BEFORE the adapter is called at all, which the
        adapter itself proves by having been asked nothing.
        """
        self.attempt()
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="destroyed")
        successor = self.successor_start()
        runtime = RuntimeAdapter()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, runtime, attempt_id=successor,
                                  inputs=None)
        self.assertIn("still holds this Work's runtime lane",
                      caught.exception.message)
        self.assertIn(ATTEMPT, caught.exception.message)
        self.assertEqual(runtime.started, [],
                         "a refused successor reached the adapter")
        self.assertEqual(len(self.lanes()), 1)

    def test_a_real_successor_claim_reaches_no_engine_or_delivery(self):
        """The bound acceptance's real offer/claim/activation arc.

        A claimed offer is not one of the two states held by the live-offer
        index, so the predecessor does not prevent the manager from issuing a
        second offer after the authority has ended and reassigned the Work.
        Drive that public arc rather than approximating activation with a row.
        The lane refusal must arrive before the missing input-root refusal,
        proving the claimed delivery is not authorized, and before the engine.
        """
        self.attempt()
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="destroyed")
        successor = "attempt-real-successor"
        assignment = {
            "work_ref": {"authority_uuid": AUTHORITY, "work_id": JOB},
            "participant": WHO, "generation": 2}
        self.session.claim_answer = {
            "assignment": dict(assignment), "claim_event": 3,
            "decision": dict(self.session.claim_answer["decision"])}
        self.session.live_assignment = dict(assignment)
        issued = issue_offer(
            self.store, self.port, offer_id="offer-real-successor",
            work_id=JOB, runtime_attempt_id=successor,
            input_digest=self.input_digest, policy_digest=POLICY,
            profile_digest=self.attempt_row()["profile_digest"],
            profile_name="reference",
            mint_bearer=lambda: "bearer-real-successor")
        accept_offer(
            self.store, self.port, offer_id=issued["offer_id"],
            decision="accept", bearer="bearer-real-successor", now=NOW,
            runtime_attempt_id=successor,
            work_ref={"authority_uuid": AUTHORITY, "work_id": JOB})
        record_attempt(
            self.store, attempt_id=successor, adapter_name="acp",
            adapter_digest=self.attempt_row()["adapter_digest"],
            profile_digest=self.attempt_row()["profile_digest"],
            input_digest=self.input_digest,
            policy_digest=self.attempt_row()["policy_digest"])
        submit_claim(self.store, self.port, offer_id=issued["offer_id"])
        activate_assignment(self.store, self.port, attempt_id=successor,
                            expect=assignment)

        runtime = RuntimeAdapter()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, runtime, attempt_id=successor,
                                  inputs=None)
        self.assertIn("still holds this Work's runtime lane",
                      caught.exception.message)
        self.assertNotIn("no input root was named", caught.exception.message)
        self.assertEqual(runtime.started, [])

    def test_a_blocked_successor_authorizes_no_input_root(self):
        """The lane is asked BEFORE anything durable, not merely before the
        engine.

        Authorizing an input root is a journalled act, so a successor that
        cannot start must not perform one. With the early check in place the
        refusal NAMES the lane; without it the input-root boundary answers
        first and a durable authorization has already been attempted -- which
        is why the ordering is a rule rather than a preference.
        """
        self.attempt()
        successor = self.successor_start()
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            beside.execute(
                "UPDATE attempts SET input_digest = ? "
                "WHERE runtime_attempt_id = ?",
                (self.input_digest, successor))
        finally:
            beside.close()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, RuntimeAdapter(),
                                  attempt_id=successor, inputs=None)
        self.assertIn("still holds this Work's runtime lane",
                      caught.exception.message)
        self.assertNotIn("no input root was named", caught.exception.message)

    def test_a_settled_cleanup_releases_the_lane_and_the_successor_starts(
            self):
        self.retained_ready("discard-after-intake")
        settled = self.cleanup_settled()
        self.assertEqual(settled["cleanup"], "complete")
        self.assertEqual(self.lanes(), [])
        successor = self.successor_start()
        runtime = RuntimeAdapter()
        request_runtime_start(self.store, runtime, attempt_id=successor,
                              inputs=None)
        held = self.lanes()
        self.assertEqual([one["holder"] for one in held], [successor])
        # AND IT IS THE SAME LANE, which is the whole cross-attempt claim.
        self.assertEqual(held[0]["lane_id"],
                         lanes._lane_id(self.reference()))

    def test_a_failed_cleanup_keeps_the_lane(self):
        """A destroy the runtime survived is a settled FAILURE, not an ending.

        Releasing here would hand a successor a lane while a container is
        still running, which is the exact overlap this Work exists to prevent.
        """
        self.retained_ready("discard-after-intake")
        settled = self.cleanup_settled(
            state="running", why="the engine still reports this identity")
        self.assertEqual(settled["cleanup"], "failed")
        self.assertEqual([one["holder"] for one in self.lanes()], [ATTEMPT])

    def test_an_unresolved_provider_keeps_the_lane(self):
        """The predecessor whose CONTAINER is gone and whose delivery is not.

        This is the case the finding describes in its own words, and before
        the lane nothing consulted it.
        """
        self.retained_ready("discard-after-intake")
        settled = self.cleanup_settled(
            launch={"lifecycle_state": "unresolved",
                    "why": "the launch root could not be proved gone"})
        # NOT AN ENDING at all: the destroy left a provider unresolved, so
        # the axis never moved and the answer says so.
        self.assertNotIn("cleanup", settled)
        self.assertEqual(self.attempt_axis("cleanup"), "pending")
        self.assertEqual([one["holder"] for one in self.lanes()], [ATTEMPT])
        successor = self.successor_start()
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, RuntimeAdapter(),
                                  attempt_id=successor, inputs=None)

    def test_retained_material_still_releases_the_lane(self):
        """`retained` and `failed` are different endings and are ruled apart.

        Retained material lives in CUSTODY -- a manager-owned sibling the
        worker never sees -- so a successor collides with nothing, and holding
        the lane for it would stop the Work forever on a policy decision.
        """
        self.retained_ready("retain")
        settled = self.cleanup_settled()
        self.assertEqual(settled["cleanup"], "retained")
        self.assertEqual(self.lanes(), [])

    def test_a_cancelled_attempt_keeps_the_lane_until_cleanup_ends(self):
        from baton_v12.worker_manager import request_cancellation
        self.attempt()
        self.session.fence_answer = {
            "cause": "cancelled",
            "assignment": dict(self.session.claim_answer["assignment"]),
            "phase": "block", "gate": "runtime-quiescence:1", "fenced": True}
        request_cancellation(self.store, self.port, CancellingAgent(),
                             RuntimeAdapter(), attempt_id=ATTEMPT,
                             reason="operator")
        self.assertEqual([one["holder"] for one in self.lanes()], [ATTEMPT])

    def test_an_uncertain_observation_keeps_the_lane(self):
        self.attempt()
        observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                value="uncertain")
        self.assertEqual([one["holder"] for one in self.lanes()], [ATTEMPT])
        successor = self.successor_start()
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, RuntimeAdapter(),
                                  attempt_id=successor, inputs=None)

    def test_the_predecessor_check_owns_the_lane_relation_it_reads(self):
        """A corrupt capacity row is not ordinary predecessor contention.

        Runtime start reads persisted lanes before either projection does. A
        split stored name and identity must be refused at that adoption too;
        reporting it as a legitimate holder would permanently block the Work
        while hiding the store-integrity failure behind an ordinary busy lane.
        """
        self.attempt()
        successor = self.successor_start(principal="principal:somebody-else")
        self.store._connection.execute(
            "UPDATE runtime_lanes SET lane_id = ? WHERE holder = ?",
            ("lane:" + "0" * 64, ATTEMPT))
        runtime = RuntimeAdapter()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, runtime, attempt_id=successor,
                                  inputs=None)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertEqual(runtime.started, [])


class TwoAddressesOneLaneAndTwoPrincipalsAreIsolated(LaneCase):

    def test_a_second_principal_on_this_work_still_waits(self):
        """The hole the KEY alone leaves, and the interlock that closes it.

        The authority's claim slot is per principal, so a Work whose
        assignment ended may be reclaimed by a DIFFERENT principal while this
        manager's cleanup is open. That successor's lane is a different row --
        the key isolates them, which is what the acceptance requires -- so the
        predecessor interlock is asked of the WORK rather than of the lane.
        """
        self.attempt()
        successor = self.successor_start(principal="principal:somebody-else")
        self.assertNotEqual(
            lanes._lane_id(self.reference(successor)),
            lanes._lane_id(self.reference()),
            "two principals must not share a lane")
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, RuntimeAdapter(),
                                  attempt_id=successor, inputs=None)
        self.assertIn("still holds this Work's runtime lane",
                      caught.exception.message)

    def test_another_work_is_not_blocked_by_this_one(self):
        """The other half: a lane protects an assignment's MATERIAL.

        Two Works held by one principal are two sets of roots with nothing
        between them, so blocking across them would be capacity nobody asked
        for.
        """
        self.attempt()
        elsewhere = self.successor_start(attempt_id="attempt-other-work")
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            beside.execute(
                "UPDATE attempts SET work_id = ? WHERE runtime_attempt_id = ?",
                (f"{AUTHORITY[:8]}-W2", elsewhere))
        finally:
            beside.close()
        request_runtime_start(self.store, RuntimeAdapter(),
                              attempt_id=elsewhere, inputs=None)
        self.assertEqual(sorted(one["holder"] for one in self.lanes()),
                         sorted([elsewhere, ATTEMPT]))


class OneWinnerAndEveryOtherFailsClosed(LaneCase):

    def test_concurrent_successors_produce_exactly_one_holder(self):
        """The compare-and-swap, driven by real threads on one store file.

        The lane's primary key is what decides this, so the losers receive an
        ordinary refusal rather than a raw integrity error -- and exactly one
        row exists afterwards.
        """
        self.retained_ready("discard-after-intake")
        self.cleanup_settled()
        self.assertEqual(self.lanes(), [])
        names = [self.successor_start(attempt_id=f"racer-{one}")
                 for one in range(3)]
        # ALL THREE OVER ONE LANE: same Work, same principal, same scope.
        self.assertEqual(
            len({lanes._lane_id(self.reference(one)) for one in names}), 1)
        outcomes, ready = [], threading.Barrier(len(names))
        lock = threading.Lock()

        def racer(attempt_id):
            store = ControlStore.open(self.path, incarnation=attempt_id,
                                      clock=lambda: NOW_LATER)
            try:
                ready.wait(10)
                request_runtime_start(store, RuntimeAdapter(),
                                      attempt_id=attempt_id, inputs=None)
                with lock:
                    outcomes.append(("started", attempt_id))
            except ContractRefusal as refused:
                with lock:
                    outcomes.append(("refused", refused.message))
            except BaseException as failure:            # pragma: no cover
                with lock:
                    outcomes.append(("faulted", repr(failure)))
            finally:
                store.close()

        threads = [threading.Thread(target=racer, args=(one,))
                   for one in names]
        for one in threads:
            one.start()
        for one in threads:
            one.join(30)
        self.assertFalse(any(one.is_alive() for one in threads))
        self.assertNotIn("faulted", [one for one, _ in outcomes], outcomes)
        started = [one for kind, one in outcomes if kind == "started"]
        self.assertEqual(len(started), 1, outcomes)
        self.assertEqual([one["holder"] for one in self.lanes()], started)

    def test_concurrent_principals_still_produce_one_work_holder(self):
        """The in-transaction Work interlock, not the lane primary key.

        These attempts deliberately hash to different lane ids. Both may pass
        the optimistic read before either write commits, so only the decisive
        predecessor check inside `_occupy_lane` can keep the Work serial.
        """
        self.retained_ready("discard-after-intake")
        self.cleanup_settled()
        names = [self.successor_start(attempt_id="principal-racer-1"),
                 self.successor_start(attempt_id="principal-racer-2",
                                      principal="principal:somebody-else")]
        self.assertEqual(
            len({lanes._lane_id(self.reference(one)) for one in names}), 2)
        outcomes, ready = [], threading.Barrier(len(names))
        lock = threading.Lock()

        def racer(attempt_id):
            store = ControlStore.open(self.path, incarnation=attempt_id,
                                      clock=lambda: NOW_LATER)
            try:
                ready.wait(10)
                request_runtime_start(store, RuntimeAdapter(),
                                      attempt_id=attempt_id, inputs=None)
                with lock:
                    outcomes.append(("started", attempt_id))
            except ContractRefusal as refused:
                with lock:
                    outcomes.append(("refused", refused.message))
            except BaseException as failure:            # pragma: no cover
                with lock:
                    outcomes.append(("faulted", repr(failure)))
            finally:
                store.close()

        threads = [threading.Thread(target=racer, args=(one,))
                   for one in names]
        for one in threads:
            one.start()
        for one in threads:
            one.join(30)
        self.assertFalse(any(one.is_alive() for one in threads))
        self.assertNotIn("faulted", [one for one, _ in outcomes], outcomes)
        started = [one for kind, one in outcomes if kind == "started"]
        self.assertEqual(len(started), 1, outcomes)
        self.assertEqual([one["holder"] for one in self.lanes()], started)

    def test_a_release_is_bound_to_the_holder(self):
        """A sibling's late cleanup does not free the lane in use.

        Two attempts share a lane over their lifetimes, so a release matched
        on the lane alone would let a predecessor's delayed settlement free
        the lane its successor is executing in.
        """
        self.attempt()
        reference = self.reference()
        beside = sqlite3.connect(self.path, isolation_level=None)
        try:
            self.assertFalse(lanes._release_lane(
                beside, attempt_id="somebody-else", reference=reference,
                why="a sibling's late cleanup"))
        finally:
            beside.close()
        self.assertEqual([one["holder"] for one in self.lanes()], [ATTEMPT])

    def test_a_conflicting_persisted_row_is_owned_before_race_refusal(self):
        """The primary-key loser path also adopts the whole stored lane.

        Move the stored Work while retaining the derived lane name. The
        predecessor query no longer selects the row, so acquisition reaches
        the primary-key conflict. That read must diagnose the split identity,
        not turn corrupt capacity into an ordinary race loser.
        """
        self.attempt()
        successor = self.successor_start()
        self.store._connection.execute(
            "UPDATE runtime_lanes SET work_id = ? WHERE holder = ?",
            (f"{AUTHORITY[:8]}-W-corrupt", ATTEMPT))
        runtime = RuntimeAdapter()
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, runtime, attempt_id=successor,
                                  inputs=None)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertEqual(runtime.started, [])


class TheProjectionExplainsTheHolderAndTheBlocker(LaneCase):

    def test_it_names_this_attempts_own_occupancy(self):
        self.attempt()
        answered = runtime_lane(self.store, ATTEMPT)
        self.assertEqual(answered["attempt_id"], ATTEMPT)
        self.assertEqual(answered["holder"], ATTEMPT)
        self.assertTrue(answered["held_by_this_attempt"])
        self.assertEqual(answered["blocked_by"], [])
        self.assertEqual(sorted(answered["lane"]),
                         sorted(("lane_id",) + lanes.LANE_PARTS))

    def test_it_names_the_blocking_predecessor_and_which_relation(self):
        """`blocked` without saying by WHICH relation is not a diagnosis.

        A predecessor under another principal holds a different lane, so
        `holder` for the successor's own lane is `None` -- and an operator
        looking only there would see a free lane and an unexplained refusal.
        """
        self.attempt()
        successor = self.successor_start(principal="principal:somebody-else")
        answered = runtime_lane(self.store, successor)
        self.assertIsNone(answered["holder"])
        self.assertFalse(answered["held_by_this_attempt"])
        self.assertEqual([one["holder"] for one in answered["blocked_by"]],
                         [ATTEMPT])
        self.assertEqual(answered["blocked_by"][0]["principal"], PRINCIPAL)

    def test_no_caller_operand_selects_a_principal_or_a_scope(self):
        """The acceptance's "without exposing a mutable caller-selected"
        half, proved structurally rather than by filtering.

        Every lane value is read from the attempt row, which was written from
        the authority's own closed claim result. There is nothing to filter
        because there is no operand to supply one.
        """
        import inspect
        self.assertEqual(sorted(inspect.signature(runtime_lane).parameters),
                         ["attempt_id", "store"])
        for member in ("principal", "effective_scope", "scope", "lane_id"):
            self.assertNotIn(
                member,
                inspect.signature(request_runtime_start).parameters, member)

    def test_a_persisted_lane_must_derive_from_its_stored_identity(self):
        """The projection does not invent an answer from a split identity.

        `lane_id` is stored beside the four values it hashes. Those five
        members are one relation, not five independent well-typed strings. An
        adopted row whose id no longer derives from its authority-owned parts
        cannot truthfully answer who holds this attempt's lane.
        """
        self.attempt()
        self.store._connection.execute(
            "UPDATE runtime_lanes SET lane_id = ? WHERE holder = ?",
            ("lane:" + "0" * 64, ATTEMPT))
        with self.assertRaises(ContractRefusal) as caught:
            runtime_lane(self.store, ATTEMPT)
        self.assertEqual(caught.exception.category, "integrity")
        self.assertEqual(caught.exception.code, "schema")


    def test_the_relation_is_owned_on_the_by_work_path_too(self):
        """BOTH read paths, because they are two queries and one relation.

        The regression above enters through `_holder_of`, which looks a lane up
        by the RECOMPUTED name. A row belonging to another principal on this
        Work is never looked up that way at all -- it is found by Work -- so a
        guard placed only on the first path would leave the second answering
        `blocked_by` out of a row whose identity does not hold together.
        """
        self.attempt()
        successor = self.successor_start(principal="principal:somebody-else")
        self.store._connection.execute(
            "UPDATE runtime_lanes SET principal = ? WHERE holder = ?",
            ("principal:not-the-one-this-name-derives-from", ATTEMPT))
        with self.assertRaises(ContractRefusal) as caught:
            runtime_lane(self.store, successor)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("ONE relation", caught.exception.message)

    def test_a_whole_consistent_row_is_still_read(self):
        """The other half: a guard that refuses everything is not a guard.

        Every part of this row is what the lane's own occupancy wrote, so the
        derived name and the stored name agree and the projection answers.
        """
        self.attempt()
        answered = runtime_lane(self.store, ATTEMPT)
        self.assertEqual(answered["holder"], ATTEMPT)
        self.assertEqual(answered["lane"]["lane_id"],
                         lanes._lane_id(self.reference()))


if __name__ == "__main__":
    unittest.main()


# W119476: a lone surrogate is text Python holds and no store can keep. The
# same value `test_text_sweep` sweeps the surface with, spelled here because
# this module drives one boundary directly rather than the whole surface.
SURROGATE = "\ud800"


class ThePublicLaneReferenceOwnsItsInput(LaneCase):
    """W119476: `lane_reference` is EXPORTED, so its input is a caller's.

    THE MEASURED GAP. Both this module and `worker_manager` export it, and it
    subscripted whatever it was handed: `[]` escaped as a raw `TypeError`, `{}`
    as a raw `KeyError`, and a list in any of the five consumed members was
    accepted -- four of them coming back out INSIDE a lane reference, while a
    malformed `runtime_attempt_id` was ignored entirely on the active path. The
    docstring said the input was read from an attempt row rather than supplied
    by a caller, and a comment cannot establish provenance. Nine direct calls
    are retained in the parent record's `evidence/revalidation-119463.json`.

    WHAT THESE CASES ARE NOT. They do not assert that a valid reference proves a
    live Authority assignment, and they do not touch occupancy: every case here
    calls the projection alone. The lifecycle compatibility half is the class
    below, and every existing case in this module is the rest of it.
    """

    # The five members the projection consumes, and one valid value for each.
    # Written out rather than taken from a row so the MINIMAL input -- the one
    # no production caller sends -- is exercised as its own shape.
    MINIMAL = {"runtime_attempt_id": "attempt-probe",
               "authority_uuid": AUTHORITY, "work_id": JOB,
               "assignment_principal": PRINCIPAL, "assignment_scope": SCOPE}

    def refused(self, supplied):
        """One direct call that must refuse, with its input left alone.

        The preservation half is asked only of values that HAVE members to
        preserve: an `object()` is not equal to a copy of itself, so comparing
        one would be asserting against identity rather than against this
        boundary leaving its input alone.
        """
        before = copy.deepcopy(supplied) if type(supplied) in (dict, list) \
            else None
        with self.assertRaises(ContractRefusal) as caught:
            lanes.lane_reference(supplied)
        if before is not None:
            self.assertEqual(supplied, before, "the input was mutated")
        return caught.exception

    # -- what a valid caller still gets --------------------------------------

    def test_the_minimal_valid_input_answers_the_unchanged_projection(self):
        answered = lanes.lane_reference(dict(self.MINIMAL))
        self.assertEqual(answered,
                         {"authority_uuid": AUTHORITY, "work_id": JOB,
                          "principal": PRINCIPAL, "effective_scope": SCOPE})
        self.assertEqual(sorted(answered), sorted(lanes.LANE_PARTS))

    def test_a_complete_active_attempt_row_is_still_accepted_whole(self):
        """The shape every production caller sends: `boundaries.row` answers a
        dict carrying exactly `ATTEMPT_COLUMNS`, and the optional half of this
        contract is what keeps that working unchanged."""
        row = self.attempt_row(self.attempt())
        self.assertEqual(sorted(row), sorted(schema.ATTEMPT_COLUMNS))
        self.assertEqual(lanes.lane_reference(row), self.reference())

    def test_the_answer_is_a_fresh_document_the_caller_cannot_reach_back_into(
            self):
        supplied = dict(self.MINIMAL)
        answered = lanes.lane_reference(supplied)
        answered["principal"] = "principal:rewritten"
        self.assertEqual(supplied["assignment_principal"], PRINCIPAL)
        self.assertEqual(lanes.lane_reference(supplied)["principal"],
                         PRINCIPAL)

    # -- the inactive refusal, preserved exactly -----------------------------

    def test_a_well_shaped_unactivated_input_keeps_its_precondition_refusal(
            self):
        caught = self.refused(dict(self.MINIMAL, assignment_principal=None))
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertIn("belongs to no lane", caught.message)

    def test_a_real_unactivated_row_with_null_parts_refuses_the_same_way(self):
        """The row `record_attempt` writes carries null Work, Authority, scope
        AND principal. It is not malformed; it is unactivated, and reporting it
        as malformed would be this correction breaking the one refusal the
        boundary already had."""
        record_attempt(self.store, attempt_id="unactivated", adapter_name="acp",
                       adapter_digest="sha256:" + "a" * 64,
                       profile_digest=self.attempt_row(self.attempt())
                       ["profile_digest"])
        row = self.attempt_row("unactivated")
        self.assertIsNone(row["work_id"])
        self.assertIsNone(row["authority_uuid"])
        self.assertIsNone(row["assignment_scope"])
        caught = self.refused(row)
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertIn("belongs to no lane", caught.message)

    # -- what used to escape as a raw Python exception -----------------------

    def test_a_non_document_is_refused_rather_than_subscripted(self):
        """`[]` produced `TypeError: list indices must be integers`, and an
        exception nobody typed is not a refusal an operator can act on."""
        for supplied in ([], (), "attempt-1", 1, None, object()):
            with self.subTest(supplied=type(supplied).__name__):
                caught = self.refused(supplied)
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "schema"))
                self.assertIn("a runtime lane attempt", caught.message)

    def test_an_empty_document_names_every_member_it_needs(self):
        """`{}` produced `KeyError: 'assignment_principal'` -- the name of the
        one member that happened to be read first, rather than the contract."""
        caught = self.refused({})
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        for name in lanes.LANE_INPUT:
            self.assertIn(name, caught.message)

    def test_each_required_member_is_named_when_it_is_the_missing_one(self):
        for name in lanes.LANE_INPUT:
            with self.subTest(missing=name):
                supplied = dict(self.MINIMAL)
                del supplied[name]
                caught = self.refused(supplied)
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "schema"))
                self.assertIn(name, caught.message)

    # -- the members that were accepted and returned -------------------------

    def test_a_malformed_consumed_member_refuses_instead_of_travelling(self):
        """The four that came back INSIDE the answer, and the fifth that was
        ignored. Each one is named by the boundary label rather than by the
        value, so a refusal says which member it is about."""
        for name in lanes.LANE_INPUT:
            for spoiled in ([], {}, 1, True, ""):
                with self.subTest(member=name, spoiled=repr(spoiled)):
                    caught = self.refused(dict(self.MINIMAL,
                                               **{name: spoiled}))
                    self.assertEqual((caught.category, caught.code),
                                     ("integrity", "schema"))
                    self.assertIn(f"a runtime lane attempt's {name}",
                                  caught.message)

    def test_unstorable_text_is_refused_where_the_document_is_owned(self):
        """A lone surrogate is caught one step EARLIER than the member rules,
        by the ownership that copies the document at all -- so its refusal
        names the document rather than the member. That is the right boundary
        for it: text that does not round-trip is not a fact about which member
        happened to carry it."""
        for name in lanes.LANE_INPUT:
            with self.subTest(member=name):
                caught = self.refused(dict(self.MINIMAL,
                                           **{name: SURROGATE}))
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "schema"))
                self.assertIn("not encodable", caught.message)

    def test_a_malformed_attempt_id_refuses_on_the_inactive_branch_too(self):
        """It was read only inside the inactive refusal, so an ACTIVE call with
        an unstorable one answered a lane and never mentioned it. Both branches
        prove it now, and the inactive branch proves it FIRST -- a malformed
        member is integrity/schema even when the attempt is also unactivated."""
        caught = self.refused(dict(self.MINIMAL, runtime_attempt_id=[]))
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        caught = self.refused(dict(self.MINIMAL, runtime_attempt_id=[],
                                   assignment_principal=None))
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        self.assertIn("runtime_attempt_id", caught.message)

    def test_a_malformed_member_beats_the_inactive_refusal(self):
        """Ordering, stated as its own case: an unactivated attempt carrying a
        malformed non-null member is malformed input, not an ordinary
        precondition. Reporting it as the latter would hide the value nobody
        can store behind an answer an operator reads as routine."""
        caught = self.refused(dict(self.MINIMAL, assignment_principal=None,
                                   authority_uuid=[]))
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        self.assertIn("authority_uuid", caught.message)

    # -- the closed member set -----------------------------------------------

    def test_known_attempt_metadata_is_optional_and_not_an_error(self):
        """A complete row carries far more than five members; the contract
        names the rest as metadata it does not read rather than refusing the
        callers that legitimately send them."""
        supplied = dict(self.MINIMAL, adapter_name="acp",
                        assignment_participant=WHO, cleanup="pending",
                        assignment_generation=1, runtime_id=None)
        self.assertEqual(lanes.lane_reference(supplied)["principal"],
                         PRINCIPAL)

    def test_a_member_this_build_does_not_name_is_refused(self):
        caught = self.refused(dict(self.MINIMAL, lane_id="lane:invented"))
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        self.assertIn("lane_id", caught.message)

    # -- an activated attempt carries all four parts or it is not one --------

    def test_an_activated_input_missing_a_reference_part_is_refused(self):
        """A principal with no Work is a broken relation rather than an
        unactivated attempt: the table's CHECK keeps the four activation
        columns together, so three quarters of a lane is integrity/schema and
        not the ordinary precondition."""
        for name in ("authority_uuid", "work_id", "assignment_scope"):
            with self.subTest(absent=name):
                caught = self.refused(dict(self.MINIMAL, **{name: None}))
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "schema"))
                self.assertIn(name, caught.message)

    # -- the rules are the attempt columns' own ------------------------------

    def test_each_consumed_member_is_held_to_its_own_column_rule(self):
        """`lane_reference` spells `text` and `identity` out rather than
        dispatching through `ATTEMPT_COLUMNS`, so that the inventory can still
        discover each member read. That leaves one thing to pin: the two must
        agree, and a column whose kind changes must not leave this boundary
        quietly checking the old one.

        Driven rather than asserted from the source: an `identity` member and a
        `text` member differ in nothing this fixture can see today, so what is
        measured is that every consumed member IS refused by its column's kind
        and that the kinds themselves are the two this boundary implements.
        """
        for name in lanes.LANE_INPUT:
            with self.subTest(member=name):
                kind = schema.ATTEMPT_COLUMNS[name].kind
                self.assertIn(kind, ("text", "identity"))
                caught = self.refused(dict(self.MINIMAL, **{name: 1}))
                self.assertEqual((caught.category, caught.code),
                                 ("integrity", "schema"))
                self.assertIn(f"a runtime lane attempt's {name}",
                              caught.message)

    def test_every_consumed_member_stays_visible_to_the_inventory(self):
        """The correction must not buy stronger checking with less discovery.

        `LANE_INPUT` is the contract a reader sees; the receiving-boundary
        catalog derives its entries from the member READS in the body. This
        holds the two together, so a later refactor that replaced the five
        literal reads with a loop would fail here rather than silently emptying
        the catalog this Work's parent has to account for.
        """
        import ast
        import inspect

        source = inspect.getsource(lanes.lane_reference)
        read = {node.slice.value
                for node in ast.walk(ast.parse(source.lstrip()))
                if isinstance(node, ast.Subscript)
                and isinstance(node.slice, ast.Constant)
                and type(node.slice.value) is str}
        for name in lanes.LANE_INPUT:
            self.assertIn(name, read)

    # -- and nothing about a lane was decided by any of it -------------------

    def test_the_projection_touches_no_store_and_no_lane(self):
        """It resolves no Authority, consults no store and occupies nothing: a
        valid typed reference is not proof of a live Authority assignment, and
        this is the case that says so."""
        self.attempt()
        before = self.lanes()
        self.assertEqual(len(before), 1)
        for _ in range(3):
            lanes.lane_reference(dict(self.MINIMAL))
        self.assertEqual(self.lanes(), before)
        # AND A REFERENCE A CALLER COMPOSED NAMES A LANE NOBODY HOLDS. The
        # principal is deliberately not this attempt's: a valid typed answer
        # is a projection of what was supplied, never evidence of occupancy.
        invented = lanes.lane_reference(
            dict(self.MINIMAL, assignment_principal="principal:invented"))
        self.assertIsNone(lanes._holder_of(self.store, invented))
        self.assertEqual(self.lanes(), before)


class TheValidatedBoundaryLeavesEveryLifecycleCallerAlone(LaneCase):
    """W119476's compatibility half: the four production call sites.

    Each one obtains its row from `_require_attempt` or `_attempt_of`, both of
    which come through `boundaries.row` and answer a dict carrying exactly
    `ATTEMPT_COLUMNS`. That is what the optional half of the input contract
    exists for, and these drive it rather than asserting it.
    """

    def test_a_start_still_occupies_the_lane_through_the_validated_input(self):
        self.attempt()
        [held] = self.lanes()
        self.assertEqual(held["holder"], ATTEMPT)
        self.assertEqual(held["lane_id"], lanes._lane_id(self.reference()))

    def test_the_public_projection_still_reads_the_same_lane(self):
        self.attempt()
        answered = runtime_lane(self.store, ATTEMPT)
        self.assertTrue(answered["held_by_this_attempt"])
        self.assertEqual(answered["lane"]["lane_id"],
                         lanes._lane_id(self.reference()))

    def test_cleanup_still_releases_the_lane_through_the_same_helper(self):
        """The two intake release sites reach `lane_reference` with an
        `_attempt_of` row, so a settled cleanup still gives the lane back."""
        self.retained_ready("discard-after-intake")
        self.assertEqual(len(self.lanes()), 1)
        settled = self.cleanup_settled()
        self.assertEqual(settled["cleanup"], "complete")
        self.assertEqual(self.lanes(), [])
