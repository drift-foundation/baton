"""W275774 — basic host expiry: revoke, stop, POSITIVELY CONFIRM, settle.

Review 16:37:09Z selected this. The content is the ORDER, because expiry is not
self-executing: an overdue generation stops being entitled to act, and the container
it governs may still be running with the workspace still mounted writable.

  1. REVOKE first and durably, so the old holder is refused at its next
     journal-guarded step instead of racing the reclaim.
  2. STOP and observe through the adapter -- external I/O, between transactions and
     never inside one.
  3. POSITIVE CONFIRMATION or nothing.
  4. SETTLE, the ordinary return.

An unknown outcome leaves the generation revoked and the resource HELD. Real
disposable stores through the intake suite's own fixtures, controlled custodian, no
live engine, no container created or signalled.
"""
import os
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts, intake, tokens

from tests.manager.test_intake import (ATTEMPT, RETENTION, Custodian,
                                       RetainedAndCompleteAreDifferentEndings)


class TheOverdueResourceIsReclaimed(RetainedAndCompleteAreDifferentEndings):

    def held(self, disposition="discard-after-intake"):
        """One governed generation over this attempt's own workspace object."""
        self.retained_ready(disposition)
        self.ended()
        attempts.pin_boundary_identity(self.store, attempt_id=ATTEMPT,
                                       source=(66, 111), workspace=(66, 4242))
        attempt = attempts._require_attempt(self.store, ATTEMPT)
        governance = tokens.workspace_governance()
        operation = attempts._start_operation_id(attempt)
        reservation = governance.reserve(self.store, attempt,
                                        operation=operation)
        container = attempt["runtime_id"]
        reservation.bind(container)()
        reservation.settle(container)
        return governance, tokens.domain_of("workspace", "66:4242"), operation

    def overdue(self):
        """Move this store's clock past the token lifetime."""
        self.store._clock = lambda: "2026-08-24T01:00:00.000Z"

    def stopping(self, **kwargs):
        """The cleanup double plus the one verb a reclaim needs.

        A reclaim STOPS the container rather than performing a receipt-bound
        destroy, so the double has to offer that verb; the intake suite's custodian
        is built for cleanup and does not.

        AND THE VERB IS `stop_expired` SINCE REVIEW 20:07:17Z. The expiry stop is its
        own capability now: `stop` is the cancellation's, owned by
        `attempts._order_quiescence`, and a capability with two crossing owners is
        what the boundary inventory refuses. A double still offering `stop` here would
        make the reclaim refuse for want of the capability, which is exactly what the
        correction intends for a caller that has not been updated.
        """
        custodian = Custodian(**kwargs)
        self.stopped = []
        custodian.stop_expired = lambda command: self.stopped.append(command)
        # AND THE OBSERVATION, because a reclaim confirms rather than assumes: the
        # positive answer is the engine saying this exact identity is gone.
        observed = kwargs.pop("observed", "absent")
        custodian.observe = lambda runtime_id: {
            "runtime_id": runtime_id, "state": observed,
            "why": "the engine answered about this exact identity"}
        return custodian

    def reclaimed(self, governance, **kwargs):
        return intake.reclaim_expired_resource(
            self.store, self.stopping(**kwargs), attempt_id=ATTEMPT,
            govern=governance)

    # -- nothing happens to a live generation ---------------------------------

    def test_a_live_generation_is_not_reclaimed(self):
        governance, domain, _ = self.held()
        answer = self.reclaimed(governance)
        self.assertEqual(answer["reclaimed"], "not-overdue")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)
        self.assertFalse(tokens.token_of(self.store, domain, 1)["revoked"])

    def test_a_live_generation_cannot_be_revoked_directly_either(self):
        """The lifetime would be advisory if a sweep could shorten it."""
        governance, domain, operation = self.held()
        attempt = attempts._require_attempt(self.store, ATTEMPT)
        with self.assertRaises(ContractRefusal) as caught:
            governance.revoke(self.store, attempt, operation=operation)
        self.assertIn("is not overdue", caught.exception.message)

    # -- the four acts, in order ----------------------------------------------

    def test_an_overdue_resource_is_revoked_and_stopped_but_HELD(self):
        """WHAT THE RECLAIM ACTUALLY ESTABLISHES, and a gap this case found.

        The reclaim revokes the entitlement and stops the container, and the engine
        positively confirms the runtime is gone. It STILL does not return the
        resource, because a reclaim normalizes nothing: it has no committed custody
        of the governed roots, so it has no basis for reporting that no writer
        survives. Asserting `returned` here is what I first wrote, and it was wrong.

        That is safe and it is deliberately incomplete: the reclaim's job is to
        withdraw the entitlement and stop the execution, and the RETURN belongs to
        the ending that normalizes the roots -- proved in the next case.
        """
        governance, domain, _ = self.held()
        self.overdue()
        answer = self.reclaimed(governance)
        self.assertEqual(answer["reclaimed"], "held")
        self.assertEqual(answer["state"], "absent",
                         "the container was positively confirmed gone")
        self.assertIn("no writer-absence proof exists yet", answer["why"])
        self.assertTrue(tokens.token_of(self.store, domain, 1)["revoked"],
                        "the entitlement is withdrawn even so")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1,
                         "and the resource stays held until a writer-absence proof")

    def test_the_normalizing_ending_then_returns_what_the_reclaim_stopped(self):
        """THE TWO HALVES TOGETHER, which is the honest shape of basic expiry.

        The reclaim withdraws the entitlement and stops the container; the ordinary
        ending normalizes the roots under this manager's custody and returns the
        resource on that proof. Neither half invents the other's evidence.
        """
        governance, domain, _ = self.held()
        self.overdue()
        self.reclaimed(governance)
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)
        # THE ENDING, governed, over the runtime the reclaim already stopped.
        intake.authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION, govern=governance)
        self.assertEqual(tokens.outstanding(self.store, domain), [],
                         "the normalizing ending returns the reclaimed resource")
        second = governance.reserve(
            self.store, {"runtime_attempt_id": "attempt-2",
                         "workspace_device": 66, "workspace_inode": 4242},
            operation="runtime.start:attempt-2")
        self.assertEqual(second.token["generation"], 2)

    def test_the_revoked_generation_may_no_longer_act(self):
        """THE POINT OF REVOKING FIRST: the old holder loses at the journal.

        A holder that wakes up mid-reclaim must not be able to admit an activation
        or bind anything, and the refusal names the revocation rather than some
        incidental later rule.
        """
        governance, domain, _ = self.held()
        self.overdue()
        governance.revoke(self.store,
                          attempts._require_attempt(self.store, ATTEMPT),
                          operation=attempts._start_operation_id(
                              attempts._require_attempt(self.store, ATTEMPT)))
        stale = {"domain": domain, "generation": 1,
                 "owner": tokens.token_of(self.store, domain, 1)["owner"]}
        with self.assertRaises(ContractRefusal) as caught:
            tokens.admit_activation(self.store, stale, container="runtime-1")
        self.assertIn("REVOKED", caught.exception.message)

    def test_the_REVOKE_lifecycle_CHECKS_HAPPEN_UNDER_ITS_OWN_LOCK(self):
        """REVIEW 19:13:42Z: THE REVOKE LIFECYCLE CHECKS BELONG INSIDE ITS WRITE.

        They were outside it. `generation_of`, the return check and the expiry check
        all ran before `BEGIN IMMEDIATE` and only the replay record was read under
        the lock, so the unstable half was an ABSENCE again -- exactly as
        `admit_activation`'s was before review 15:19:45Z corrected it. A caller
        suspended after reading `returned` as false could resume and withdraw the
        entitlement of a generation that had since been returned and replaced.

        THE ASSERTION IS DISCRIMINATING, which my first attempt at this case was
        not. Hooking the replay read and interleaving a return proves only that a
        nested transaction cannot start -- and the replay read was already inside
        the lock before this correction, so that case passed either way. What
        actually moved is WHERE THE TERMINAL FACT IS READ, so this observes exactly
        that: when `token_of` reads this generation's RETURNED record, is this
        connection inside a transaction? Under the old order it was not.

        AND THE NESTED-TRANSACTION HALF IS KEPT BESIDE IT for what it does prove:
        no same-connection work can slip a terminal fact into the window. For a
        SEPARATE connection the exclusion is `BEGIN IMMEDIATE`'s write lock rather
        than anything asserted here.
        """
        import sqlite3

        governance, domain, operation = self.held()
        self.overdue()
        attempt = attempts._require_attempt(self.store, ATTEMPT)
        honest = self.store.operation_record
        seen = {}

        def watching(operation_id):
            if operation_id == tokens._returned_id(domain, 1) \
                    and "locked" not in seen:
                seen["locked"] = self.store._connection.in_transaction
            return honest(operation_id)

        self.store.operation_record = watching
        try:
            governance.revoke(self.store, attempt, operation=operation)
        finally:
            self.store.operation_record = honest
        self.assertTrue(seen.get("locked"),
                        "the return check is read under the revoke's own lock")
        self.assertTrue(tokens.token_of(self.store, domain, 1)["revoked"])

        # AND NOTHING TERMINAL CAN LAND IN THE WINDOW EITHER. A second overdue
        # generation, so the replay record of this one is not already written.
        token = tokens.token_of(self.store, domain, 1)
        evidence = {"domain": domain, "generation": 1,
                    "launch": token["launch"], "container": token["container"],
                    "stopped": True, "helpers": []}
        attempted = []

        def interleaving(operation_id):
            answer = honest(operation_id)
            if operation_id == tokens._revoked_id(domain, 1) and not attempted:
                attempted.append("tried")
                tokens.returned(self.store, token, cessation=evidence)
            return answer

        self.store.operation_record = interleaving
        try:
            with self.assertRaises(sqlite3.OperationalError) as caught:
                governance.revoke(self.store, attempt, operation=operation)
        finally:
            self.store.operation_record = honest
        self.assertIn("within a transaction", str(caught.exception))
        self.assertEqual(attempted, ["tried"], "the window was actually reached")
        self.assertFalse(tokens.token_of(self.store, domain, 1)["returned"],
                         "no return landed inside the revoke's transaction")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)

    # -- and the unknown hold -------------------------------------------------

    def test_an_unproved_cessation_leaves_the_resource_held(self):
        """THE UNKNOWN HOLD. A runtime still RUNNING after its destroy proves nothing,
        so the generation stays revoked and the resource stays held -- which is why
        the revocation is not conditional on the confirmation succeeding."""
        governance, domain, _ = self.held()
        self.overdue()
        answer = self.reclaimed(
            governance,
            # EVERY MEMBER NAMED, because this double deliberately does not fill
            # them in -- a case about the outcome must still state the deliveries.
            destroyed={"state": "running", "why": "the engine reports it up",
                       "credentials": {"lifecycle_state": "not-delivered"},
                       "launch": {"lifecycle_state": "not-delivered"}})
        self.assertEqual(answer["reclaimed"], "held")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1,
                         "an unproved cessation must not free the resource")
        self.assertTrue(tokens.token_of(self.store, domain, 1)["revoked"],
                        "and the entitlement stays withdrawn")

    def test_a_repeated_reclaim_is_idempotent(self):
        """Revoking twice replays the same revocation; nothing escalates."""
        governance, domain, _ = self.held()
        self.overdue()
        first = self.reclaimed(governance)
        again = self.reclaimed(governance)
        self.assertEqual(again["reclaimed"], first["reclaimed"])
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)
        self.assertTrue(tokens.token_of(self.store, domain, 1)["revoked"])

    # -- the rule the reclaim itself must obey --------------------------------

    def test_no_engine_call_happens_inside_a_database_transaction(self):  # noqa
        """DB-1 ASKED AT THE RECLAIM, because this is the one act that both writes
        the journal and calls the engine. The revocation commits and closes, the
        engine is asked, and only then does the settlement open its own
        transaction."""
        governance, _, _ = self.held()
        self.overdue()
        observed = []
        custodian = self.stopping()
        honest = custodian.stop_expired
        watched_observe = custodian.observe

        def stopping(command):
            observed.append(("stop", self.store._connection.in_transaction))
            return honest(command)

        def observing(runtime_id):
            observed.append(("observe", self.store._connection.in_transaction))
            return watched_observe(runtime_id)

        custodian.stop_expired = stopping
        custodian.observe = observing
        intake.reclaim_expired_resource(
            self.store, custodian, attempt_id=ATTEMPT, govern=governance)
        self.assertEqual([one[0] for one in observed], ["stop", "observe"],
                         "the shutdown and its confirmation both happen")
        self.assertEqual([one for one in observed if one[1]], [],
                         "the engine was asked while a transaction was open")

    def test_no_filesystem_call_happens_inside_a_database_transaction(self):
        governance, _, _ = self.held()
        self.overdue()
        observed = []
        honest = {name: getattr(os, name) for name in
                  ("stat", "lstat", "open", "scandir")}

        def watching(name):
            def call(*args, **named):
                observed.append((name, self.store._connection.in_transaction))
                return honest[name](*args, **named)
            return call

        for name in honest:
            setattr(os, name, watching(name))
        try:
            intake.reclaim_expired_resource(
                self.store, self.stopping(), attempt_id=ATTEMPT,
                govern=governance)
        finally:
            for name, call in honest.items():
                setattr(os, name, call)
        self.assertEqual([one for one in observed if one[1]], [],
                         "no filesystem call may run inside a transaction here")


class ARunningAttemptHasNoIntakeReceipt(
        __import__("tests.manager.test_intake", fromlist=["x"])
        .TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence):
    """THE P1 FROM REVIEW 16:55:05Z, as my own case.

    My earlier fixture called `retained_ready` and `ended` first, so every expiry
    case ran against an attempt that already HAD an intake receipt -- and the real
    subject of expiry, a worker still running, never reached the code. Against a
    running attempt the first cut reused `destroy_operation`, which is receipt-bound,
    and so it committed the revocation and then refused on that schema BEFORE any
    shutdown was attempted: revoked, and nothing stopped. The worst ordering
    available.

    The reclaim now carries its OWN operation identity rather than borrowing a
    cleanup's, and it stops the container through `stop` instead of the receipt-bound
    `destroy`. The ordinary cleanup's receipt contract is untouched, and no intake is
    fabricated.
    """

    def governed(self):
        self.running_attempt()
        attempts.pin_boundary_identity(self.store, attempt_id=ATTEMPT,
                                       source=(66, 111), workspace=(66, 4242))
        attempt = self.attempt_row()
        governance = tokens.workspace_governance()
        reservation = governance.reserve(
            self.store, attempt,
            operation=attempts._start_operation_id(attempt))
        reservation.bind(attempt["runtime_id"])()
        reservation.settle(attempt["runtime_id"])
        return governance, tokens.domain_of("workspace", "66:4242")

    def test_a_running_attempt_with_no_receipt_is_still_shut_down(self):
        governance, domain = self.governed()
        self.assertIsNone(intake.intake_receipt_of(self.store, ATTEMPT),
                          "the whole point: a running attempt has no receipt")
        self.store._clock = lambda: "2026-08-24T01:00:00.000Z"
        adapter = self.Abandoner()
        stopped = []
        adapter.stop_expired = lambda command: stopped.append(command)
        answer = intake.reclaim_expired_resource(
            self.store, adapter, attempt_id=ATTEMPT, govern=governance)
        # THE SHUTDOWN WAS ATTEMPTED, which is what the first cut never reached.
        self.assertEqual(len(stopped), 1,
                         "expiry revoked permission and never attempted shutdown")
        self.assertEqual(stopped[0]["runtime_id"],
                         self.attempt_row()["runtime_id"])
        self.assertTrue(stopped[0]["operation_id"].startswith("resource.reclaim:"),
                        "the shutdown is correlated by the reclaim's own identity")
        self.assertTrue(tokens.token_of(self.store, domain, 1)["revoked"])
        self.assertEqual(answer["reclaimed"], "held")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)

    def test_the_reclaim_identity_is_derived_and_stable(self):
        governance, _ = self.governed()
        attempt = self.attempt_row()
        first = intake.reclaim_operation_id(attempt, 1)
        self.assertEqual(first, intake.reclaim_operation_id(attempt, 1))
        self.assertNotEqual(first, intake.reclaim_operation_id(attempt, 2))

    def test_a_refused_stop_is_not_a_cessation(self):
        governance, domain = self.governed()
        self.store._clock = lambda: "2026-08-24T01:00:00.000Z"
        adapter = self.Abandoner()

        def refusing(command):
            raise ContractRefusal("refused", "capability",
                                  "the engine is unreachable")

        adapter.stop_expired = refusing
        answer = intake.reclaim_expired_resource(
            self.store, adapter, attempt_id=ATTEMPT, govern=governance)
        self.assertEqual(answer["reclaimed"], "held")
        self.assertIn("the stop was refused", answer["why"])
        self.assertTrue(tokens.token_of(self.store, domain, 1)["revoked"],
                        "the entitlement still goes; only the cessation is unknown")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)


class TheRevokedResourceHasItsOwnEnding(RetainedAndCompleteAreDifferentEndings):
    """W275774 review 17:44:30Z's executable milestone.

    THE GAP MY OWN CASES EXPOSED: a reclaim revokes and stops but normalizes nothing,
    and the ordinary cleanup is authorized by an intake RECEIPT that a reclaimed
    running attempt never had. So a revoked resource could sit held with NO operation
    able to free it -- the reclaim lacking the custody proof, the cleanup lacking its
    authorization. This ending is the one that can do both.
    """

    def revoked(self):
        """One governed generation, overdue, reclaimed: revoked and stopped."""
        self.retained_ready("discard-after-intake")
        self.ended()
        attempts.pin_boundary_identity(self.store, attempt_id=ATTEMPT,
                                       source=(66, 111), workspace=(66, 4242))
        attempt = attempts._require_attempt(self.store, ATTEMPT)
        governance = tokens.workspace_governance()
        operation = attempts._start_operation_id(attempt)
        reservation = governance.reserve(self.store, attempt, operation=operation)
        reservation.bind(attempt["runtime_id"])()
        reservation.settle(attempt["runtime_id"])
        self.store._clock = lambda: "2026-08-24T01:00:00.000Z"
        governance.revoke(self.store, attempt, operation=operation)
        return governance, tokens.domain_of("workspace", "66:4242")

    def custodian(self, observed="absent"):
        custodian = Custodian()
        custodian.observe = lambda runtime_id: {
            "runtime_id": runtime_id, "state": observed,
            "why": "the engine answered about this exact identity"}
        return custodian

    def settled(self, governance, **kwargs):
        return intake.settle_revoked_resource(
            self.store, self.custodian(**kwargs), attempt_id=ATTEMPT,
            govern=governance)

    # -- the ending that closes the gap ---------------------------------------

    def test_a_revoked_resource_is_normalized_and_returned(self):
        governance, domain = self.revoked()
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)
        answer = self.settled(governance)
        self.assertEqual(answer["settled"], "returned")
        self.assertEqual(tokens.outstanding(self.store, domain), [],
                         "the revoked resource is free once its roots are held")

    def test_replacement_becomes_possible_only_after_the_proof(self):
        """A REPLACEMENT ONLY AFTER PROOF, which is the review's own phrasing."""
        governance, domain = self.revoked()
        with self.assertRaises(ContractRefusal):
            governance.reserve(
                self.store, {"runtime_attempt_id": "attempt-2",
                             "workspace_device": 66, "workspace_inode": 4242},
                operation="runtime.start:attempt-2")
        self.settled(governance)
        second = governance.reserve(
            self.store, {"runtime_attempt_id": "attempt-2",
                         "workspace_device": 66, "workspace_inode": 4242},
            operation="runtime.start:attempt-2")
        self.assertEqual(second.token["generation"], 2)

    # -- and everything it refuses to assume ----------------------------------

    def test_an_unrevoked_generation_is_not_settled_by_this_ending(self):
        """This ending settles a withdrawn entitlement; it does not withdraw one."""
        self.retained_ready("discard-after-intake")
        self.ended()
        attempts.pin_boundary_identity(self.store, attempt_id=ATTEMPT,
                                       source=(66, 111), workspace=(66, 4242))
        attempt = attempts._require_attempt(self.store, ATTEMPT)
        governance = tokens.workspace_governance()
        reservation = governance.reserve(
            self.store, attempt,
            operation=attempts._start_operation_id(attempt))
        reservation.bind(attempt["runtime_id"])()
        reservation.settle(attempt["runtime_id"])
        with self.assertRaises(ContractRefusal) as caught:
            self.settled(governance)
        self.assertIn("has not been revoked", caught.exception.message)

    def test_a_runtime_that_is_not_ABSENT_NOW_holds_the_resource(self):
        """ASKED AGAIN RATHER THAN REMEMBERED.

        The reclaim's absence was true at the reclaim's instant. A container can be
        restarted by a hand outside this manager, and normalizing under a running
        writer is the one thing this ending must never do -- so it re-asks, and a
        running answer holds.
        """
        governance, domain = self.revoked()
        answer = self.settled(governance, observed="running")
        self.assertEqual(answer["settled"], "held")
        self.assertIn("not positively absent now", answer["why"])
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)

    def test_an_uncertain_observation_holds_too(self):
        governance, domain = self.revoked()
        answer = self.settled(governance, observed="uncertain")
        self.assertEqual(answer["settled"], "held")
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1)

    def test_a_second_settlement_is_idempotent(self):
        governance, domain = self.revoked()
        self.settled(governance)
        again = self.settled(governance)
        self.assertEqual(again["settled"], "already-returned")
        self.assertEqual(tokens.outstanding(self.store, domain), [])

    def test_the_stale_holder_can_do_nothing_throughout(self):
        """NO OLD WRITABLE RESTART: every act a stale holder could attempt is
        refused while the generation is revoked, and the refusal names it."""
        governance, domain = self.revoked()
        stale = {"domain": domain, "generation": 1,
                 "owner": tokens.token_of(self.store, domain, 1)["owner"]}
        # EVERY ACT IS REFUSED, AND EACH ONE NAMES THE RULE THAT ANSWERS FIRST.
        # Measured rather than assumed, and my first version of this case asserted
        # the revocation for all three and was wrong twice: this generation already
        # journalled its launch at reservation, so a late launch collides at that
        # identity, and a binding naming some other launch is refused for that
        # instead. Both are correct refusals about different rules, and stating the
        # nearest one is more honest than staging the fixture until the revocation
        # happens to be the first check reached.
        for what, act, names in (
            ("a late launch",
             lambda: tokens.journal_launch(self.store, stale, "launch:late"),
             "already recorded with a different kind or signature"),
            ("a late binding",
             lambda: tokens.bind_container(self.store, stale, "runtime-late",
                                           launch="launch:late"),
             "not the launch this token journalled"),
            # AND THE ACTIVATION, which is the act that reaches the revocation --
            # the one that would actually run a container.
            ("a late activation",
             lambda: tokens.admit_activation(self.store, stale,
                                             container="runtime-1"),
             "REVOKED"),
        ):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    act()
                self.assertIn(names, caught.exception.message)


class TheServingLoopDrivesTheExpiryPass(unittest.TestCase):
    """W275774 review 17:09:10Z: WIRE ACTUAL SERVING EXPIRY.

    `serve` owns only WHEN the pass happens. Composing a runtime adapter for an
    attempt is the deployment's act, not the job manager's -- which is why the pass
    is injected exactly as the clock, the wait and the stopping predicate are. These
    cases drive the real `manager.serve` with controlled injections and assert the
    order and the failure behaviour, which is all this seam decides.
    """

    def serving(self, *, ticks=3, reclaim=None, store=None, operations=None):
        from baton_v12.job_manager import manager

        remaining = [ticks]

        def should_continue():
            remaining[0] -= 1
            return remaining[0] >= 0

        order = []

        def sweeping(_store, _operations, *, now):
            order.append(("sweep", now))
            return {"observed_at": now}

        honest = manager.sweep
        manager.sweep = sweeping
        honest_reconcile = manager.reconcile
        manager.reconcile = lambda *a, **k: {"observed_at": k.get("now")}
        try:
            manager.serve(store, operations, clock=lambda: "2026-08-24T00:00:00.000Z",
                          sleep=lambda _seconds: None,
                          should_continue=should_continue,
                          reclaim=None if reclaim is None
                          else (lambda **named: (order.append(("reclaim",
                                                               named["now"])),
                                                 reclaim(**named))[1]))
        finally:
            manager.sweep = honest
            manager.reconcile = honest_reconcile
        return order

    def test_the_pass_runs_once_per_tick_after_the_sweep(self):
        seen = []
        order = self.serving(ticks=3, reclaim=lambda **named: seen.append(named))
        self.assertEqual([one[0] for one in order],
                         ["sweep", "reclaim", "sweep", "reclaim",
                          "sweep", "reclaim"],
                         "the reclaim must follow the sweep within each tick")
        self.assertEqual(len(seen), 3)
        self.assertEqual(seen[0]["now"], "2026-08-24T00:00:00.000Z")

    def test_an_absent_pass_leaves_the_loop_exactly_as_it_was(self):
        order = self.serving(ticks=2, reclaim=None)
        self.assertEqual([one[0] for one in order], ["sweep", "sweep"])

    def test_a_refusing_pass_ends_the_run_rather_than_skipping_expiry(self):
        """A loop that silently skipped expiry would hold resources forever with
        nothing in the record to say why."""
        def refusing(**named):
            raise ContractRefusal("refused", "capability",
                                  "the reclaim pass cannot proceed")

        with self.assertRaises(ContractRefusal):
            self.serving(ticks=3, reclaim=refusing)

    def test_a_pass_that_is_not_callable_is_refused_before_the_first_tick(self):
        """Driven WITHOUT the helper, deliberately: the helper wraps the pass in a
        lambda, so routing this through it would have handed `serve` something
        callable and the capability check would never have been reached. Measured --
        the case passed for that reason until this was corrected."""
        from baton_v12.job_manager import manager

        honest = manager.reconcile
        manager.reconcile = lambda *a, **k: {"observed_at": k.get("now")}
        try:
            with self.assertRaises(ContractRefusal):
                manager.serve(None, None, clock=lambda: "2026-08-24T00:00:00.000Z",
                              sleep=lambda _seconds: None,
                              should_continue=lambda: False,
                              reclaim="not a capability")
        finally:
            manager.reconcile = honest


if __name__ == "__main__":
    unittest.main()
