"""W275776 — a manager restart at each external-effect cut, on the CONNECTED path.

Owner brief 275776 asks for the complete G1 lifecycle verified on the actual connected path
with a controlled engine, not isolated helper callbacks. So the composition here is Child A's
ACCEPTED connected fixture -- real offer/accept/record/claim/activate rows, a real allocation
under configured storage, boundary identities pinned from real `os.stat`, and
`attempts.request_runtime_start` with control-bound governance -- and this file adds exactly
one thing to it: the manager DIES at a chosen cut and a fresh `ControlStore` handle stands in
for the restart, with no process-local state carried across.

The cuts are REC-3's own list, narrowed to the ones this Work owns: before launch; after a
possible launch whose reply was lost; after a launch the manager never settled at all because
it was killed; and with the engine unreachable afterwards.

What each case asserts is section 17's Recovery row -- "Manager restart at each selected
external-effect cut preserves identities, unknowns and custody, with no duplicate
container/provider dispatch" -- and TOK-10's "restart recovery processes overdue and uncertain
tokens before admitting conflicts".

Real disposable stores, real allocations, the suites' own controlled adapter doubles. No live
engine, no provider, no container created or signalled outside the double. Run standalone.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "finding-v12-token-lifecycle"))

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (ControlStore, attempts, load_manifest,
                                      reconcile_runtime, request_runtime_start,
                                      tokens)

from tests.manager import input_roots
from tests.manager.test_offers import NOW, WHO
from tests.manager.test_output import ATTEMPT, AUTHORITY, JOB, OutputCase

from test_connected_lifecycle import (Counting,
                                      TheGovernedStartAndItsOwnEnding as Connected)


class Lost(Counting):
    """The engine created the container and the adapter's reply never came back.

    The crossing REALLY happens -- `Counting.start` records it and answers -- and then the
    reply is lost, which is REC-3's "after possible launch with lost reply".
    """

    def start(self, operands, **named):
        answered = super().start(operands, **named)
        self.lost = dict(answered)
        raise OSError("the adapter's reply never came back")


class Killed(Counting):
    """The same crossing, and then the MANAGER DIES before anything settles it.

    `KeyboardInterrupt` is not an `Exception`, so `request_runtime_start`'s fault settlement
    does not run at all -- which is what a killed process leaves behind, and the cut a
    restart has to resolve from the record alone.
    """

    def start(self, operands, **named):
        answered = super().start(operands, **named)
        self.lost = dict(answered)
        raise KeyboardInterrupt("the manager process was killed here")


class Unreachable(Counting):
    """The engine cannot be asked at all: TOK-10's unavailable Docker control."""

    def list(self, operands):
        raise OSError("the engine is unreachable")

    def observe(self, runtime_id, **named):
        raise OSError("the engine is unreachable")


class RestartCase(Connected):
    """Child A's connected composition, cut at one boundary and then restarted."""

    def prepared(self):
        """Everything a governed start needs, and nothing started yet."""
        OutputCase.attempt(self, quiescent=False, disposition=None)
        inputs, _ = input_roots.composed(
            self, self.storage,
            given=load_manifest(self.store, self.input_digest, "inputManifest"),
            work_ref={"authority_uuid": AUTHORITY, "work_id": JOB},
            participant=WHO, generation=1, runtime_attempt_id=ATTEMPT)
        self.pinned = self.pin(ATTEMPT, inputs)
        self.domain = tokens.domain_of("workspace", self.pinned)
        return inputs

    def starting(self, runtime, inputs):
        """The REAL governed start, with whatever the engine double does to it."""
        try:
            request_runtime_start(self.store, runtime, attempt_id=ATTEMPT,
                                  inputs=inputs, govern=self.governance())
            return None
        except BaseException as failure:            # recorded, never swallowed
            return failure

    def restarted(self):
        """A fresh manager over the same store: no process-local state at all."""
        self.store.close()
        fresh = ControlStore.open(self.path, incarnation="manager-restarted",
                                  clock=lambda: NOW)
        self.addCleanup(fresh.close)
        self.store = fresh
        return fresh

    def axis(self):
        row = self.row_of(ATTEMPT)
        return row["execution_runtime"], row["runtime_id"]


class ARestartFindsTheUncertainTokenItMustReconcile(RestartCase):

    def test_a_lost_reply_leaves_the_activation_unsettled_and_findable(self):
        inputs = self.prepared()
        runtime = Lost()
        failure = self.starting(runtime, inputs)
        self.assertIsInstance(failure, OSError)
        self.assertEqual(len(runtime.started), 1, "more than one crossing happened")
        fresh = self.restarted()
        held = tokens.unresolved(fresh, self.domain)
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["generation"], 1)
        self.assertEqual(held[0]["container"], runtime.runtime_id)
        self.assertEqual(held[0]["execution"], ATTEMPT)
        self.assertFalse(held[0]["expired"])

    def test_a_KILLED_manager_leaves_the_same_findable_state(self):
        """The harder cut: nothing settled, so the attempt row still says only that a
        start was requested -- and the TOKEN is what remembers the container."""
        inputs = self.prepared()
        runtime = Killed()
        failure = self.starting(runtime, inputs)
        self.assertIsInstance(failure, KeyboardInterrupt)
        self.assertEqual(self.axis(), ("start-requested", None))
        fresh = self.restarted()
        held = tokens.unresolved(fresh, self.domain)
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["container"], runtime.runtime_id,
                         "the token forgot which container it bound")
        self.assertEqual(held[0]["launch"],
                         attempts._start_operation_id(self.row_of(ATTEMPT)))

    def test_nothing_unresolved_before_a_launch_is_attempted(self):
        """REC-3's first cut: a restart before launch has nothing to reconcile, and the
        reader says so rather than inventing a candidate."""
        self.prepared()
        fresh = self.restarted()
        self.assertEqual(tokens.unresolved(fresh, self.domain), [])

    def test_a_settled_activation_is_not_unresolved(self):
        """The ordinary successful start: the activation is settled, so a restart has
        nothing to ask about -- the reader must not sweep healthy executions."""
        inputs = self.prepared()
        runtime = Counting()
        self.assertIsNone(self.starting(runtime, inputs))
        fresh = self.restarted()
        self.assertEqual(tokens.unresolved(fresh, self.domain), [])
        self.assertTrue(tokens.token_of(fresh, self.domain, 1)["activation_started"])


class BeforeAdmission(Counting):
    """The engine created the container; the manager died BEFORE the admission was asked.

    `Reservation.bind` journals the launch and binds the container and THEN answers the
    admission callable, so a kill between those two is this cut -- and the container the
    engine created is inert, because nothing ever started it.
    """

    def start(self, operands, *, bind=None, **named):
        self.crossed = getattr(self, "crossed", [])
        self.crossed.append(dict(operands))
        if bind is not None:
            bind(self.runtime_id)                  # journal + bind_container commit
        raise KeyboardInterrupt("killed before the admission was asked")


class Unbound(Counting):
    """Killed between the journalled launch and the container binding."""

    def start(self, operands, *, bind=None, **named):
        self.crossed = getattr(self, "crossed", [])
        self.crossed.append(dict(operands))
        raise KeyboardInterrupt("killed before the container was bound")


class Mismatched(Counting):
    """The engine reports a DIFFERENT container for this attempt's labels."""

    def list(self, operands):
        return [{"runtime_id": "somebody-elses-runtime",
                 "labels": dict(operands["labels"])}]


class EveryUNSETTLEDLAUNCHCutIsVisibleAfterARestart(RestartCase):
    """W275776 review 2026-09-27T11-45-17Z, R2: the earlier cut needed its own treatment.

    The reader selected only `admitted-unsettled`, so a manager killed after the launch was
    journalled and the container bound -- but before the admission was asked -- left a bound,
    possibly inert container that no restart visited. Measured at that exact cut, then the
    reader was widened to every UNSETTLED LAUNCH, with each entry naming which cut it is.
    """

    def test_the_PRE_ADMISSION_cut_is_selected_and_named(self):
        inputs = self.prepared()
        runtime = BeforeAdmission()
        self.assertIsInstance(self.starting(runtime, inputs), KeyboardInterrupt)
        self.assertEqual(len(runtime.crossed), 1)
        fresh = self.restarted()
        state = tokens.token_of(fresh, self.domain, 1)
        # THE STATE THIS CUT REALLY LEAVES, asserted rather than assumed: bound, never
        # admitted, nothing settled.
        self.assertEqual(state["container"], runtime.runtime_id)
        self.assertFalse(state["activating"])
        self.assertIsNone(state["activation_started"])
        held = tokens.unresolved(fresh, self.domain)
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["cut"], "bound-not-admitted")
        self.assertEqual(held[0]["container"], runtime.runtime_id)
        self.assertEqual(held[0]["execution"], ATTEMPT)

    def test_the_UNBOUND_cut_is_selected_with_nothing_to_observe_by_id(self):
        inputs = self.prepared()
        runtime = Unbound()
        self.assertIsInstance(self.starting(runtime, inputs), KeyboardInterrupt)
        fresh = self.restarted()
        held = tokens.unresolved(fresh, self.domain)
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["cut"], "launched-unbound")
        self.assertIsNone(held[0]["container"])
        self.assertEqual(held[0]["launch"],
                         attempts._start_operation_id(self.row_of(ATTEMPT)))

    def test_the_admitted_cut_is_still_named_as_itself(self):
        inputs = self.prepared()
        self.starting(Killed(), inputs)
        fresh = self.restarted()
        self.assertEqual(tokens.unresolved(fresh, self.domain)[0]["cut"],
                         "admitted-unsettled")

    def test_a_settled_activation_is_still_never_selected(self):
        inputs = self.prepared()
        self.assertIsNone(self.starting(Counting(), inputs))
        fresh = self.restarted()
        self.assertEqual(tokens.unresolved(fresh, self.domain), [])

    def test_no_cut_releases_the_resource_or_permits_a_replacement(self):
        """Every cut holds: TOK-10's "before admitting conflicts" for all three."""
        for engine in (Unbound, BeforeAdmission, Killed):
            with self.subTest(cut=engine.__name__):
                self.setUp()
                inputs = self.prepared()
                self.starting(engine(), inputs)
                fresh = self.restarted()
                self.assertEqual(len(tokens.outstanding(fresh, self.domain)), 1)
                with self.assertRaises(ContractRefusal) as caught:
                    tokens.acquire(fresh, self.domain,
                                   operation="runtime.start:other",
                                   execution="attempt-other",
                                   attempt="attempt-other")
                self.assertIn("outstanding baton", caught.exception.message)


class TheEVIDENCEARestartActsOnIsExactOrItHolds(RestartCase):
    """R2: exact live, mismatched and unavailable evidence, and the expiry ordering."""

    def test_a_DIFFERENT_container_under_these_labels_is_a_contradiction_to_hold(self):
        """AN OBSERVATION OF CURRENT BEHAVIOUR, and deliberately not a claim that it is right.

        I expected `reconcile_runtime` to refuse a runtime whose id differs from the one the
        token bound. It ATTACHES it. My previous wording called that "the accepted design
        because measurement found it", and W275776 review 2026-09-27T11-52-29Z rejects that
        reasoning, correctly: measuring what the code does today is not authority to
        substitute a container bound to another token identity, and neither Child A's nor
        Child B's acceptance covers a cross-identity recovery path nobody reviewed.

        So this case RECORDS the behaviour and asserts the two facts that matter either way:
        the token's binding is not rewritten, and the resource stays held. Whether attaching
        a differently-identified container is correct is an open question for the worker proof
        below, not something this file settles.

        What IS true and worth asserting is the disagreement that remains: the TOKEN
        authorized `runtime-1` and the engine now reports another container under the same
        labels, so the resource's stop/expiry path and the attempt's attachment name
        different objects. The token's binding is NOT rewritten by reconciliation, and the
        recovery pass reports that contradiction and holds -- it is exactly the
        "contradictory observation" the review says must not be resolved by guessing.
        """
        inputs = self.prepared()
        runtime = Killed()
        self.starting(runtime, inputs)
        fresh = self.restarted()
        bound = tokens.token_of(fresh, self.domain, 1)["container"]
        answered = reconcile_runtime(fresh, Mismatched(), attempt_id=ATTEMPT)
        self.assertEqual(answered["decision"], "attached")
        self.assertNotEqual(answered["runtime_id"], bound)
        # THE TOKEN'S BINDING IS UNTOUCHED: one generation bound one container, and a
        # reconciliation does not re-authorize another.
        self.assertEqual(tokens.token_of(fresh, self.domain, 1)["container"], bound)
        self.assertEqual(len(tokens.outstanding(fresh, self.domain)), 1)

    def test_a_RENEWED_deadline_is_what_a_restart_reads(self):
        """Child B's arbitration, from a fresh handle: the restart must judge the
        generation against the deadline the renewal moved, not the original grant."""
        inputs = self.prepared()
        self.starting(Killed(), inputs)
        row = self.row_of(ATTEMPT)
        renewed = tokens.renew(self.store, {"domain": self.domain, "generation": 1,
                                            "owner": tokens.token_of(
                                                self.store, self.domain, 1)["owner"]},
                               execution=ATTEMPT,
                               operation=attempts._start_operation_id(row),
                               expected_revision=0, seconds=1800)
        fresh = self.restarted()
        held = tokens.unresolved(fresh, self.domain)
        self.assertEqual(held[0]["expires_at"], renewed["expires_at"])
        self.assertEqual(held[0]["revision"], 1)
        self.assertFalse(held[0]["expired"])

    def test_an_expired_unsettled_launch_is_reported_as_expired_and_still_held(self):
        """The ordering TOK-6 keeps: expiry begins revocation, it does not free anything.
        The unresolved report says `expired` and the resource is still outstanding."""
        inputs = self.prepared()
        self.starting(Killed(), inputs)
        fresh = self.restarted()
        beyond = "2026-08-25T00:00:00.000Z"
        later = ControlStore.open(self.path, incarnation="manager-later",
                                  clock=lambda: beyond)
        self.addCleanup(later.close)
        held = tokens.unresolved(later, self.domain)
        self.assertEqual(len(held), 1)
        self.assertTrue(held[0]["expired"])
        self.assertEqual(len(tokens.outstanding(later, self.domain)), 1)
        # AND A REVOCATION IS AVAILABLE, which is the supported order: revoke, stop,
        # confirm, settle -- never a silent replacement.
        answered = tokens.revoke(later, self.pinned, "workspace",
                                 execution=ATTEMPT,
                                 operation=attempts._start_operation_id(
                                     self.row_of(ATTEMPT)))
        self.assertEqual(answered["generation"], 1)
        self.assertTrue(tokens.token_of(later, self.domain, 1)["revoked"])
        # A REVOKED GENERATION IS NO LONGER A RECOVERY CANDIDATE: its entitlement is
        # withdrawn and the reclaim path owns it from here.
        self.assertEqual(tokens.unresolved(later, self.domain), [])


class ReconcilingFromThatSetAttachesWithoutASecondCrossing(RestartCase):

    def test_the_restarted_manager_attaches_the_exact_container_it_bound(self):
        """The whole point of the reader: a restart can now ASK the engine about the
        execution it did not finish, through the accepted reconciliation, and the answer
        attaches the exact container -- with no second create and no second start."""
        inputs = self.prepared()
        runtime = Killed()
        self.starting(runtime, inputs)
        crossings = len(runtime.started)
        fresh = self.restarted()
        held = tokens.unresolved(fresh, self.domain)
        self.assertEqual(len(held), 1)
        # THE ENGINE IS ASKED THROUGH THE ACCEPTED PATH, with a live adapter that lists
        # what the previous process created.
        listing = Counting()
        listing.started = list(runtime.started)          # the same engine's memory
        answered = reconcile_runtime(fresh, listing, attempt_id=held[0]["execution"])
        # THE ANSWER'S OWN MEMBERS, read from `documents` rather than guessed: an
        # attachment names the decision, the runtime and what was observed.
        self.assertEqual(answered["decision"], "attached")
        self.assertEqual(answered["runtime_id"], held[0]["container"])
        self.assertEqual(self.axis(), ("running", held[0]["container"]))
        # NO DUPLICATE DISPATCH: reconciliation asks and attaches, it never starts.
        self.assertEqual(len(listing.started), crossings)
        self.assertEqual(len(tokens.outstanding(fresh, self.domain)), 1,
                         "reconciliation must not release the resource")

    def test_an_unreachable_engine_keeps_the_hold_and_names_the_execution(self):
        """TOK-10: unavailable Docker control leaves an ACTIONABLE HELD state. The
        reconciliation fails, nothing is attached, the resource stays held -- and the
        reader still names the exact execution an operator has to resolve."""
        inputs = self.prepared()
        runtime = Killed()
        self.starting(runtime, inputs)
        fresh = self.restarted()
        with self.assertRaises(OSError):
            reconcile_runtime(fresh, Unreachable(), attempt_id=ATTEMPT)
        self.assertEqual(self.axis(), ("start-requested", None))
        held = tokens.unresolved(fresh, self.domain)
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["execution"], ATTEMPT)
        self.assertEqual(held[0]["container"], runtime.runtime_id)
        self.assertEqual(len(tokens.outstanding(fresh, self.domain)), 1)

    def test_the_hold_still_excludes_a_conflicting_acquisition(self):
        """TOK-10's "before admitting conflicts": while the launch is unresolved, no
        second execution may take the resource, restart or no restart."""
        inputs = self.prepared()
        self.starting(Killed(), inputs)
        fresh = self.restarted()
        with self.assertRaises(ContractRefusal) as caught:
            tokens.acquire(fresh, self.domain, operation="runtime.start:other",
                           execution="attempt-other", attempt="attempt-other")
        self.assertIn("outstanding baton", caught.exception.message)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(
        unittest.TestSuite(loader.loadTestsFromTestCase(case) for case in
                           (ARestartFindsTheUncertainTokenItMustReconcile,
                            EveryUNSETTLEDLAUNCHCutIsVisibleAfterARestart,
                            TheEVIDENCEARestartActsOnIsExactOrItHolds,
                            ReconcilingFromThatSetAttachesWithoutASecondCrossing))
    ).wasSuccessful())
