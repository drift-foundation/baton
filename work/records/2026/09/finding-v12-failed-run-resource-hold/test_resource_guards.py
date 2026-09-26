"""R3: a held resource is not deleted, reused or adopted behind the hold.

Owner 260900 selected R3; owner 262043 granted the caller-ownership extension
and review-2026-09-25T02-39-02Z directs the first guarded entry with focused
tests before the full four-entry matrix. This module is that first increment.

WHAT IS GUARDED HERE: `workspaces.discard_workspace`, the DELETION boundary. It
is first because it is the act a hold most obviously has to stop and because it
has no product call site, so guarding it proves the mechanism without moving
seven callers in the same step. The other three entries follow, and the matrix
below is written to grow into them rather than be replaced.

THE SOURCE CORRECTION THIS MODULE IS BUILT ON. The two custody roots of one
attempt are NOT siblings: `custody._derived_root` puts the result root at
`<home>/workspace/result-<attempt>`, INSIDE the workspace. So they overlap as
ancestor and descendant, and a guard that checked one root would leave the act
free to remove the ancestor of a held descendant. Every case here is written
against that layout rather than the sibling layout I first assumed.

WHAT IS REAL: the manager's own `workspaces` entries, its own `ControlStore`
journal, real directories on the owner-selected disk-backed root, and holds
recorded by real `custody_act` submissions through the accepted fake engine
port. No daemon, container, image or live provider is reached, and nothing is
inspected on or cleaned from any engine.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from baton_v12.contracts import ContractRefusal                # noqa: E402
from baton_v12.worker_manager import custody                   # noqa: E402
from baton_v12.worker_manager import workspaces                # noqa: E402

from test_hold_clearance import OnlyExactSettlementClearsOneHold  # noqa: E402
from test_hold_admission import TheHoldAdmitsExactlyOneSubmitter  # noqa: E402


class AHeldResourceIsNotRemoved(OnlyExactSettlementClearsOneHold):
    """The deletion boundary, against a real standing hold."""

    def storage_of(self, control):
        """The configured workspace store's own recorded place."""
        return workspaces.configured_workspace_storage(control).place

    def home_of(self, control, attempt_id):
        return os.path.join(self.storage_of(control), attempt_id)

    # -- the guard itself ----------------------------------------------------

    def test_a_held_attempt_home_is_not_removed(self):
        """THE POSITIVE REFUSAL: a standing hold stops the deletion."""
        control, _composed, attempt_id, held = self.held_episode("guard-hold")
        home = self.home_of(control, attempt_id)
        self.assertTrue(os.path.isdir(home), home)

        with self.assertRaises(ContractRefusal) as caught:
            workspaces.discard_workspace(self.storage_of(control), attempt_id,
                                         control=control)
        message = caught.exception.message
        self.assertIn("FROZEN", message)
        self.assertIn("no deletion", message)
        self.assertIn(held["helper_identity"], message)
        # AND THE BYTES ARE STILL THERE -- measured, not inferred from the
        # refusal. A guard that refused after removing would satisfy the
        # assertion above and none of the point.
        self.assertTrue(os.path.isdir(home), "the held home was removed")

    def test_the_held_root_keeps_its_own_bytes_through_the_refusal(self):
        """Every path under the home survives, walked and compared."""
        control, _composed, attempt_id, _held = self.held_episode(
            "guard-bytes")
        home = self.home_of(control, attempt_id)
        sentinel = os.path.join(home, "workspace",
                                "operator-must-see-this.txt")
        with open(sentinel, "w", encoding="utf-8") as writing:
            writing.write("the held tree is untouched\n")
        before = self.walked(home)
        self.assertTrue(before, "the fixture left nothing to compare")

        with self.assertRaises(ContractRefusal):
            workspaces.discard_workspace(self.storage_of(control), attempt_id,
                                         control=control)
        self.assertEqual(self.walked(home), before,
                         "the held home's bytes changed")

    @staticmethod
    def walked(place):
        """Every path and its bytes under one root."""
        found = {}
        for current, _directories, files in os.walk(place):
            for name in sorted(files):
                one = os.path.join(current, name)
                try:
                    with open(one, "rb") as reading:
                        found[os.path.relpath(one, place)] = reading.read()
                except OSError:                          # pragma: no cover
                    found[os.path.relpath(one, place)] = None
        return found

    # -- the overlap the source correction forced -----------------------------

    def test_a_hold_on_the_result_root_protects_its_ancestor_workspace(self):
        """THE OVERLAP, which is why the guard reads BOTH roots.

        The result root is `<home>/workspace/result-<attempt>` -- inside the
        workspace, not beside it. The fixture's hold is on `result`, and the
        deletion this refuses would have removed the whole home INCLUDING the
        workspace that contains the held tree. A guard keyed on the acting
        root alone would have let it through.
        """
        control, _composed, attempt_id, _held = self.held_episode(
            "guard-overlap")
        # THE LAYOUT IS ASSERTED rather than assumed from the docstring.
        home = self.home_of(control, attempt_id)
        workspace = os.path.join(home, "workspace")
        result = os.path.join(workspace, f"result-{attempt_id}")
        self.assertTrue(os.path.isdir(workspace), workspace)
        self.assertTrue(os.path.isdir(result),
                        f"the result root is not inside the workspace: "
                        f"{result}")

        # THE HOLD IS ON `result`, and the refusal names that root.
        [standing] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(standing["cleared"])
        self.assertEqual(custody.custody_holds(control, attempt_id,
                                               "workspace"), [])
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.discard_workspace(self.storage_of(control), attempt_id,
                                         control=control)
        self.assertIn("result root", caught.exception.message)
        self.assertTrue(os.path.isdir(result))

    # -- exact clearance releases exactly one episode -------------------------

    def test_an_exact_clearance_releases_the_resource_and_nothing_else(self):
        """The other half: a reconciled hold stops refusing.

        A guard that never released would be a leak dressed as safety, so the
        positive direction is asserted too -- with the SAME attempt, so the
        only thing that changed is the clearance.
        """
        control, _composed, attempt_id, held = self.held_episode(
            "guard-release")
        with self.assertRaises(ContractRefusal):
            workspaces.discard_workspace(self.storage_of(control), attempt_id,
                                         control=control)
        self.clearing(control, attempt_id, held)
        [cleared] = custody.custody_holds(control, attempt_id, "result")
        self.assertTrue(cleared["cleared"])
        # AND NOW IT PROCEEDS.
        self.assertTrue(workspaces.discard_workspace(
            self.storage_of(control), attempt_id, control=control))
        self.assertFalse(os.path.isdir(self.home_of(control, attempt_id)))

    def test_clearing_one_root_leaves_the_other_root_held(self):
        """ONE CLEARANCE, ONE EPISODE -- across the two overlapping roots.

        THIS CASE'S PREMISE CHANGED WITH THE [P1] OVERLAP FIX, and the change is
        the point rather than an inconvenience. It used to record a second
        uncleared episode on `workspace` while the fixture's `result` episode
        stood. THAT STATE IS NO LONGER REACHABLE THROUGH A REAL ACT: claiming an
        episode now requires every OVERLAPPING root to be free, so the second
        claim refuses and writes nothing -- which is exactly the protection
        review 2026-09-25T04-25-17Z demanded, and a fixture that wrote the row
        directly would be manufacturing a state the product forbids.

        So the reachable form is asserted instead: the second hold is taken
        AFTER the first is cleared, and clearing the first must not have
        released anything else. Every closing assertion is unchanged.
        """
        control, composed, attempt_id, held = self.held_episode("guard-two")

        # THE OVERLAP REFUSES A SECOND CLAIM, and records nothing.
        with self.assertRaises(ContractRefusal) as blocked:
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="workspace")
        self.assertIn("the two roots of one attempt overlap",
                      blocked.exception.message)
        self.assertEqual(custody.custody_holds(control, attempt_id,
                                               "workspace"), [])

        # THE RESULT EPISODE'S OWN TOKEN, which is the first submission -- R2
        # refuses an answer about another submission however ordinary it looks.
        self.clearing(control, attempt_id, held,
                      settlement=self.answered(held,
                                               submission=self.submitted(0)))
        self.assertTrue(custody.custody_holds(control, attempt_id,
                                              "result")[0]["cleared"])

        # AND NOW THE OTHER ROOT CAN BE HELD, through the same real act.
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="workspace")
        [other] = custody.custody_holds(control, attempt_id, "workspace")
        self.assertFalse(other["cleared"])
        # CLEARING THE RESULT EPISODE RELEASED ONLY ITSELF.
        self.assertTrue(custody.custody_holds(control, attempt_id,
                                              "result")[0]["cleared"])
        self.assertFalse(custody.custody_holds(control, attempt_id,
                                               "workspace")[0]["cleared"])
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.discard_workspace(self.storage_of(control), attempt_id,
                                         control=control)
        self.assertIn("workspace root", caught.exception.message)
        self.assertTrue(os.path.isdir(self.home_of(control, attempt_id)))

    # -- an unaffected attempt stays usable ----------------------------------

    def test_an_unheld_attempt_is_not_affected_by_another_ones_hold(self):
        """The guard is per resource, not a deployment-wide freeze."""
        control, _composed, attempt_id, _held = self.held_episode(
            "guard-unaffected")
        storage = self.storage_of(control)
        other = "attempt-" + "e" * 32
        workspaces.assignment_workspace(
            workspaces.configured_workspace_group(control), storage, other)
        self.assertTrue(os.path.isdir(os.path.join(storage, other)))
        self.assertEqual(custody.custody_holds(control, other, "result"), [])

        # THE HELD ONE REFUSES...
        with self.assertRaises(ContractRefusal):
            workspaces.discard_workspace(storage, attempt_id, control=control)
        # ...AND THE OTHER ONE DOES NOT.
        self.assertTrue(workspaces.discard_workspace(storage, other,
                                                     control=control))
        self.assertFalse(os.path.isdir(os.path.join(storage, other)))
        self.assertTrue(os.path.isdir(self.home_of(control, attempt_id)))

    # -- the second exported deletion path -----------------------------------

    def test_a_held_attempt_keeps_its_execution_roots(self):
        """`discard_execution_roots`, the other exported removal.

        It takes `inputs` and `workspace` -- and `workspace` CONTAINS
        `result-<attempt>`, so the fixture's hold on `result` covers a tree
        this would delete.
        """
        control, _composed, attempt_id, _held = self.held_episode(
            "guard-exec")
        home = self.home_of(control, attempt_id)
        result = os.path.join(home, "workspace", f"result-{attempt_id}")
        self.assertTrue(os.path.isdir(result), result)

        with self.assertRaises(ContractRefusal) as caught:
            workspaces.discard_execution_roots(self.storage_of(control),
                                               attempt_id, control=control)
        self.assertIn("FROZEN", caught.exception.message)
        self.assertTrue(os.path.isdir(result),
                        "the held result tree was removed")
        self.assertTrue(os.path.isdir(os.path.join(home, "workspace")))

    def test_the_second_path_also_refuses_an_unrelated_store(self):
        """The store binding applies to both exported removals, not one."""
        import tempfile

        from baton_v12.worker_manager import ControlStore
        from tests.job_manager import fixtures

        control, _composed, attempt_id, _held = self.held_episode(
            "guard-exec-store")
        storage = self.storage_of(control)
        with tempfile.TemporaryDirectory(dir="/var/tmp/baton-w257624",
                                         prefix="guard-exec-store-") as room:
            with ControlStore.open(os.path.join(room, "other.sqlite3"),
                                   incarnation="unrelated",
                                   clock=lambda: fixtures.NOW) as unrelated:
                with self.assertRaises(ContractRefusal) as caught:
                    workspaces.discard_execution_roots(storage, attempt_id,
                                                       control=unrelated)
        # THE UNCONFIGURED STORE IS REFUSED EARLIER AND HARDER than my own
        # binding check: `configured_workspace_storage` is the deployment's own
        # record, and a store that configured nothing has no place to compare.
        # Measured rather than assumed -- I expected my message and got the
        # stronger one.
        self.assertIn("no configured workspace store",
                      caught.exception.message)
        self.assertTrue(os.path.isdir(self.home_of(control, attempt_id)))

    # -- serialization against the R1 hold commit ----------------------------
    #
    # IMPLEMENTED IN THE PRODUCT, NOT YET PROVED HERE. Both exported removals
    # now run their hold read and their effect inside `ControlStore.transact`,
    # the same `BEGIN IMMEDIATE` lock `_claim_episode` takes, so a racing claim
    # either commits first and is read, or waits until the tree is gone. The
    # failure window is stated in `_serialized_removal`'s docstring.
    #
    # The controlled two-handle race case for it is NOT in this module: my first
    # attempt never reached the transaction and I took it out rather than hand
    # over a red module or a case that passes for the wrong reason. It is the
    # next thing this matrix needs.

    # -- the overlapping roots admit ONE act at a time -----------------------
    #
    # W257624 R3 [P1], review 2026-09-25T04-25-17Z and owner 264494. The two
    # roots of one attempt are nested, so "is this root free" was the wrong
    # question: with the workspace held, the ending's first act reached the
    # result root, SUBMITTED a helper and settled its episode, and only then
    # refused. `custody._standing_overlap` now answers for every overlapping
    # root, in both the preliminary read and the locked re-read.

    def claiming_refused(self, control, composed, attempt_id, which):
        """Try one real claim and return its refusal."""
        with self.assertRaises(ContractRefusal) as caught:
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id, which=which)
        return caught.exception

    def test_an_ancestor_hold_refuses_a_claim_on_the_nested_root(self):
        """ANCESTOR-HELD: the workspace is held, the nested result is claimed.

        This is the reviewer's measured fault at the custody boundary itself:
        the result root lives INSIDE the workspace, so a helper normalizing it
        is a helper inside a held tree. The claim must refuse having submitted
        nothing.
        """
        control, composed, attempt_id = self.unresolved_custody("overlap-anc")
        # A REAL WORKSPACE HOLD -- the request crossed, nothing answered.
        self.claiming_refused(control, composed, attempt_id, "workspace")
        self.assertEqual([(one["episode"], one["cleared"]) for one in
                          custody.custody_holds(control, attempt_id,
                                                "workspace")],
                         [(0, False)])
        crossed = self.engine_effects()

        refusal = self.claiming_refused(control, composed, attempt_id, "result")
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("workspace root carries", refusal.message)
        self.assertIn("acting on the result root", refusal.message)
        self.assertIn("the two roots of one attempt overlap", refusal.message)
        # NOTHING WAS RECORDED AND NOTHING CROSSED. A later refusal cannot undo
        # a submission, so the only safe place to stop is before it.
        self.assertEqual(custody.custody_holds(control, attempt_id, "result"),
                         [])
        self.assertEqual(self.engine_effects(), crossed,
                         "a helper submitted inside a held ancestor")

    def test_a_descendant_hold_refuses_a_claim_on_the_containing_root(self):
        """DESCENDANT-HELD: the result is held, the containing workspace is
        claimed.

        The same containment read the other way round. Normalizing the
        workspace would remove or rewrite the very tree the held result root
        sits in, so the direction of nesting does not soften it.
        """
        control, composed, attempt_id, _held = self.held_episode("overlap-desc")
        crossed = self.engine_effects()

        refusal = self.claiming_refused(control, composed, attempt_id,
                                        "workspace")
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("result root carries", refusal.message)
        self.assertIn("acting on the workspace root", refusal.message)
        self.assertEqual(custody.custody_holds(control, attempt_id,
                                               "workspace"), [])
        self.assertEqual(self.engine_effects(), crossed,
                         "a helper submitted over a held descendant")

    def test_two_racers_on_the_overlapping_roots_admit_exactly_one(self):
        """COMPETING ORDERINGS, under the serialization boundary.

        Two real thread-owned handles claim the TWO DIFFERENT roots of one
        attempt at once. Before the fix both would have won, because each asked
        only about its own root. Exactly one may win now, and the loser must
        refuse having submitted nothing -- whichever order the scheduler picks,
        which is why the assertions name neither.
        """
        import threading

        control, composed, attempt_id = self.unresolved_custody("overlap-race")
        crossed = len(self.engine_effects())
        start = threading.Barrier(2, timeout=20)
        answers, guard = [], threading.Lock()

        def racing(which):
            store = self.reopened(f"overlap-racer-{which}")
            try:
                start.wait()
                try:
                    custody.normalize_directory(store, composed,
                                                assignment_id=attempt_id,
                                                which=which)
                    answered = (which, "settled")
                except ContractRefusal as refusal:
                    answered = (which, "refused", refusal.message)
                except BaseException as other:           # pragma: no cover
                    answered = (which, type(other).__name__, str(other)[:160])
                with guard:
                    answers.append(answered)
            finally:
                store.close()

        racers = [threading.Thread(target=racing, name=f"racer-{which}",
                                   args=(which,))
                  for which in custody.CUSTODY_ROOTS]
        for one in racers:
            one.start()
        for one in racers:
            one.join(timeout=30)
        for one in racers:
            self.assertFalse(one.is_alive(), "a racer never joined")

        # EXACTLY ONE EPISODE EXISTS ACROSS BOTH ROOTS, and exactly one
        # submission crossed -- the winner's. The severed engine means the
        # winner also refuses, so neither answer says "settled"; what separates
        # them is the durable episode and the engine ledger.
        self.assertEqual(len(answers), 2, answers)
        standing = [(root, one["episode"], one["cleared"])
                    for root in custody.CUSTODY_ROOTS
                    for one in custody.custody_holds(control, attempt_id, root)]
        self.assertEqual(len(standing), 1, standing)
        self.assertEqual(len(self.engine_effects()) - crossed, 1,
                         "two helpers submitted over one overlapping tree")
        overlapped = [one for one in answers
                      if len(one) > 2 and "overlap" in one[2]]
        self.assertEqual(len(overlapped), 1,
                         f"exactly one racer must lose to the overlap: "
                         f"{answers}")

    def test_the_overlap_is_within_one_attempt_and_not_across_attempts(self):
        """UNRELATED-RESOURCE CONCURRENCY: two attempts share no tree.

        The containment being closed is physical and lives inside ONE assignment
        home, so it must not have become a deployment-wide freeze. This asks the
        admission read itself -- the function that changed -- about a second
        real attempt's BOTH roots while the first is held, and then removes two
        unrelated homes from two real handles AT ONCE to show the serialization
        boundary is not a global one.

        It reads `_standing_overlap` directly rather than composing a second
        worker adapter: the question is exactly what that read answers, and a
        second adapter would add fixture the case does not need.
        """
        import threading

        control, _composed, attempt_id, _held = self.held_episode("overlap-two")
        storage = self.storage_of(control)
        group = workspaces.configured_workspace_group(control)
        others = ["attempt-" + letter * 32 for letter in ("a", "b")]
        for other in others:
            workspaces.assignment_workspace(group, storage, other)

        # THE HELD ATTEMPT IS HELD ON BOTH ITS ROOTS, by overlap...
        for which in custody.CUSTODY_ROOTS:
            self.assertIsNotNone(
                custody._standing_overlap(control, attempt_id, which),
                f"the held attempt's {which} root must be refused")
        # ...AND THE OTHER ATTEMPTS ARE FREE ON BOTH OF THEIRS.
        for other in others:
            for which in custody.CUSTODY_ROOTS:
                self.assertIsNone(
                    custody._standing_overlap(control, other, which),
                    f"{other}'s {which} root was refused by another attempt's "
                    f"hold")

        # AND TWO UNRELATED REMOVALS PROCEED CONCURRENTLY, on their own handles.
        removed, guard = [], threading.Lock()
        start = threading.Barrier(2, timeout=20)

        def removing(other):
            store = self.reopened(f"unrelated-{other[-1]}")
            try:
                start.wait()
                try:
                    answer = ("answered", workspaces.discard_workspace(
                        storage, other, control=store))
                except BaseException as failure:          # pragma: no cover
                    answer = (type(failure).__name__, str(failure)[:160])
                with guard:
                    removed.append(answer)
            finally:
                store.close()

        threads = [threading.Thread(target=removing, args=(other,),
                                    name=f"remover-{other[-1]}")
                   for other in others]
        for one in threads:
            one.start()
        for one in threads:
            one.join(timeout=30)
        for one in threads:
            self.assertFalse(one.is_alive(), "an unrelated remover never joined")
        self.assertEqual(removed, [("answered", True), ("answered", True)],
                         removed)
        for other in others:
            self.assertFalse(os.path.isdir(os.path.join(storage, other)))
        # AND THE HELD ATTEMPT IS UNTOUCHED THROUGHOUT.
        self.assertTrue(os.path.isdir(self.home_of(control, attempt_id)))

    # -- the two write-lock race orderings -----------------------------------
    #
    # Reviews 2026-09-25T03-28-01Z and T03-40-38Z: both orderings, SEPARATE
    # REAL THREAD-OWNED HANDLES, bounded events at the ACTUAL boundary, and
    # then -- T03-40-38Z -- EXACT acceptance rather than "any exception".
    #
    # WHY THE HANDLES ARE THE THREADS' OWN, learned by getting it wrong:
    # passing the fixture's store into a thread raises "SQLite objects created
    # in a thread can only be used in that same thread". That is not a test
    # inconvenience -- it is why this contest is between two managers holding
    # two connections. Each thread OPENS AND CLOSES ITS OWN, inside itself.
    #
    # THE WINNER'S EVENT IS INSIDE THE LOCK. Two earlier attempts hooked a
    # module function from outside and never reached the transaction at all.
    # What is wrapped is ONE HANDLE'S OWN `transact`, pausing after its action
    # has run and BEFORE it commits -- so the paused handle is the handle
    # holding `BEGIN IMMEDIATE`. No global patch, no thread-name gating.
    #
    # AND THE CONTENDER ANNOUNCES ITSELF. `is_alive` alone cannot distinguish
    # "blocked on the lock" from "still opening its store", so the contender
    # signals when its handle is READY and again when it is AT THE OPERATION
    # BOUNDARY -- about to enter the transaction it cannot have. Only then is it
    # timed. `_BUSY_TIMEOUT_MS` is 5000, so 1.5s leaves it genuinely blocked
    # rather than timed out, and releasing inside that window lets it go on to
    # observe the winner's committed state.
    #
    # BARRIERS ARE RELEASED AND BOTH THREADS JOINED IN `finally`, so a failed
    # intermediate assertion cannot strand a lock holder for the full 20s.

    def engine_effects(self):
        """Every argv this fixture's fake provider was actually handed.

        The provider records submissions on the argv, which is where R2's
        attribution comes from; counting them is how a case proves an act did
        or did not reach the engine.
        """
        seen = []
        for engine in self.engines:
            seen.extend(getattr(engine, "submissions", []))
        return list(seen)

    @staticmethod
    def pausing(store, arrived, proceed):
        """Hold THIS handle inside its own write lock, once."""
        real, once = store.transact, []

        def transacting(operation_id, kind, signature, action):
            def acting(connection):
                answer = action(connection)
                if not once:
                    once.append(True)
                    arrived.set()
                    if not proceed.wait(timeout=20):     # pragma: no cover
                        raise AssertionError("the lock holder was not released")
                return answer

            return real(operation_id, kind, signature, acting)

        store.transact = transacting

    @staticmethod
    def announcing(store, entered):
        """Signal when THIS handle is at the operation boundary, once."""
        real, once = store.transact, []

        def transacting(operation_id, kind, signature, action):
            if not once:
                once.append(True)
                entered.set()
            return real(operation_id, kind, signature, action)

        store.transact = transacting

    def test_a_claim_cannot_commit_while_the_removal_holds_the_lock(self):
        """ORDERING ONE: the removal reaches the lock first.

        Its handle is held inside its transaction -- guard read taken, tree
        removed, not yet committed -- while a second real handle, announced at
        its own operation boundary, tries to claim a new uncertainty episode on
        the same root. It CANNOT get in: `_claim_episode` needs the same
        `BEGIN IMMEDIATE`. When it finally runs, the home is gone, and the
        exact refusal it takes -- with NO submission reaching the engine -- is
        asserted rather than merely being some exception.
        """
        import threading

        control, composed, attempt_id, held = self.held_episode("race-removal")
        storage = self.storage_of(control)
        home = self.home_of(control, attempt_id)
        self.clearing(control, attempt_id, held)
        before = self.engine_effects()

        arrived, proceed = threading.Event(), threading.Event()
        ready, entered = threading.Event(), threading.Event()
        opened = threading.Event()
        removals, claims = [], []

        def removing():
            store = self.reopened("race-remover")
            try:
                self.pausing(store, arrived, proceed)
                ready.set()
                removals.append(("answered", workspaces.discard_workspace(
                    storage, attempt_id, control=store)))
            except BaseException as other:              # pragma: no cover
                removals.append((type(other).__name__, str(other)[:200]))
            finally:
                store.close()

        def claiming():
            store = self.reopened("race-claimant")
            try:
                self.announcing(store, entered)
                opened.set()
                custody.normalize_directory(store, composed,
                                            assignment_id=attempt_id,
                                            which="result")
                claims.append(("settled", None))
            except BaseException as other:
                claims.append((type(other).__name__, str(other)[:200]))
            finally:
                store.close()

        remover = threading.Thread(target=removing, name="remover")
        claimant = threading.Thread(target=claiming, name="claimant")
        try:
            remover.start()
            self.assertTrue(ready.wait(timeout=20),
                            f"the remover's handle never opened: {removals}")
            self.assertTrue(arrived.wait(timeout=20),
                            f"the removal never reached its lock: {removals}")
            claimant.start()
            self.assertTrue(opened.wait(timeout=20),
                            f"the claimant's handle never opened: {claims}")
            self.assertTrue(entered.wait(timeout=20),
                            f"the claimant never reached the operation "
                            f"boundary: {claims}")
            # THE WRITE LOCK IS HELD, so no episode can be committed here.
            claimant.join(timeout=1.5)
            self.assertTrue(claimant.is_alive(),
                            f"a claim ran to completion while the removal held "
                            f"the write lock: {claims}")
        finally:
            proceed.set()
            remover.join(timeout=30)
            claimant.join(timeout=30)
        self.assertFalse(remover.is_alive(), "the remover never joined")
        self.assertFalse(claimant.is_alive(), "the claimant never joined")

        # THE REMOVAL WON CLEANLY -- its own answer, and the home is gone.
        self.assertEqual(removals, [("answered", True)], removals)
        self.assertFalse(os.path.isdir(home), "the home survived the removal")

        # AND THE LOSER'S OUTCOME IS EXACTLY THIS REFUSAL, not any exception: a
        # ProgrammingError or a fixture fault must fail this case.
        self.assertEqual(len(claims), 1, claims)
        kind, message = claims[0]
        self.assertEqual(kind, "ContractRefusal", claims)
        self.assertIn("does not exist", message)
        self.assertIn("a custody root is a directory this manager created",
                      message)
        # NOTHING REACHED THE ENGINE. The loser refused before submitting, so
        # the provider was handed nothing new -- this is the part that makes the
        # ordering safe rather than merely ordered.
        self.assertEqual(self.engine_effects(), before,
                         "the losing claim submitted to the engine anyway")

        # THE DURABLE STATE, EXACTLY AS RECORDED. The cleared episode 0 stays
        # cleared, and the loser's claim left episode 1 standing: it committed
        # its claim when the lock came free and only then found the root gone.
        #
        # I AM NAMING THAT RATHER THAN SMOOTHING IT. An episode whose helper was
        # never created is real durable residue: R2's settlement path wants an
        # accountable engine answer about a helper that does not exist.
        #
        # AND I OVERSTATED THE REMEDY, which review 2026-09-25T04-06-46Z
        # corrected. I wrote that an operator direct act can retire it. THAT IS
        # NOT AN ESTABLISHED SUPPORTED RECOVERY COMMAND -- `CUSTODY_DIRECT_ACT`
        # is a clearance SHAPE this module's product accepts, not a deployed
        # operator path anyone has demonstrated end to end. So what this case
        # records is an UNRESOLVED RECOVERY GAP, not a gap with a known answer.
        # Whether a pre-submission refusal should release its own claim is an R1
        # question and R1 is accepted; this observes, it does not change it.
        self.assertEqual([(one["episode"], one["cleared"]) for one in
                          custody.custody_holds(control, attempt_id, "result")],
                         [(0, True), (1, False)])

    def test_a_removal_cannot_proceed_while_a_claim_holds_the_lock(self):
        """ORDERING TWO: the claim reaches the lock first.

        The claimant's handle is held inside ITS transaction with the new
        episode written and uncommitted; the removal -- announced at its own
        operation boundary -- cannot take its guard read at all, because that
        read is inside the transaction it cannot start. When the claimant
        commits and the removal finally runs, its read sees the freshly
        committed episode and refuses BY NAME, and the tree survives.

        THIS IS THE ORDERING A QUERY-THEN-MUTATE GUARD GETS WRONG: a read taken
        before the lock is a read taken before this episode existed.
        """
        import threading

        control, composed, attempt_id, held = self.held_episode("race-claim")
        storage = self.storage_of(control)
        home = self.home_of(control, attempt_id)
        self.clearing(control, attempt_id, held)
        before = self.engine_effects()

        arrived, proceed = threading.Event(), threading.Event()
        ready, entered = threading.Event(), threading.Event()
        opened = threading.Event()
        claims, removals = [], []

        def claiming():
            store = self.reopened("race-claim-holder")
            try:
                self.pausing(store, arrived, proceed)
                ready.set()
                custody.normalize_directory(store, composed,
                                            assignment_id=attempt_id,
                                            which="result")
                claims.append(("settled", None))
            except BaseException as other:
                claims.append((type(other).__name__, str(other)[:200]))
            finally:
                store.close()

        def removing():
            store = self.reopened("race-remover")
            try:
                self.announcing(store, entered)
                opened.set()
                removals.append(("answered", workspaces.discard_workspace(
                    storage, attempt_id, control=store)))
            except ContractRefusal as refusal:
                removals.append(("refused", refusal.message))
            except BaseException as other:              # pragma: no cover
                removals.append((type(other).__name__, str(other)[:200]))
            finally:
                store.close()

        claimant = threading.Thread(target=claiming, name="claimant")
        remover = threading.Thread(target=removing, name="remover")
        try:
            claimant.start()
            self.assertTrue(ready.wait(timeout=20),
                            f"the claimant's handle never opened: {claims}")
            self.assertTrue(arrived.wait(timeout=20),
                            f"the claim never reached its lock: {claims}")
            remover.start()
            self.assertTrue(opened.wait(timeout=20),
                            f"the remover's handle never opened: {removals}")
            self.assertTrue(entered.wait(timeout=20),
                            f"the removal never reached the operation "
                            f"boundary: {removals}")
            # THE CLAIMANT HOLDS THE LOCK, so the removal cannot take its guard
            # read, let alone act on the answer.
            remover.join(timeout=1.5)
            self.assertTrue(remover.is_alive(),
                            f"a removal ran to completion while a claim held "
                            f"the write lock: {removals}")
            self.assertTrue(os.path.isdir(home), "the home went while blocked")
        finally:
            proceed.set()
            claimant.join(timeout=30)
            remover.join(timeout=30)
        self.assertFalse(claimant.is_alive(), "the claimant never joined")
        self.assertFalse(remover.is_alive(), "the remover never joined")

        # THE WINNER'S OWN OUTCOME, EXACTLY. Its act submitted and this
        # fixture's provider is severed, so it refuses for THAT reason -- the
        # episode it committed is the durable record of the unanswered act.
        self.assertEqual(len(claims), 1, claims)
        kind, message = claims[0]
        self.assertEqual(kind, "ContractRefusal", claims)
        self.assertIn("did not answer accountably", message)
        # ONE submission crossed, the winner's own; the blocked removal made
        # none, so the engine saw exactly one new effect.
        after = self.engine_effects()
        self.assertEqual(len(after), len(before) + 1, after)
        self.assertEqual(after[:len(before)], before)

        # THE EPISODE IS COMMITTED -- a second, uncleared one on this root.
        self.assertEqual([(one["episode"], one["cleared"]) for one in
                          custody.custody_holds(control, attempt_id, "result")],
                         [(0, True), (1, False)])
        [standing] = [one for one in
                      custody.custody_holds(control, attempt_id, "result")
                      if not one["cleared"]]

        # AND THE REMOVAL SAW THAT EPISODE, from inside its own lock, and
        # refused by naming it -- not some other hold and not a lock error.
        self.assertEqual(len(removals), 1, removals)
        self.assertEqual(removals[0][0], "refused", removals)
        self.assertIn("FROZEN", removals[0][1])
        self.assertIn("uncertainty episode 1", removals[0][1])
        self.assertIn(standing["held"]["helper_identity"], removals[0][1])
        self.assertTrue(os.path.isdir(home),
                        "the removal proceeded past a committed hold")

    # -- the operand is required --------------------------------------------

    def test_the_store_operand_cannot_be_omitted(self):
        """A GUARD THAT CAN BE FORGOTTEN IS NOT ONE.

        `control` is keyword-only and required, so the old two-argument call
        does not silently delete behind a hold -- it does not compile as a
        call at all. And a caller that passes something that is not a store is
        refused rather than treated as "no holds".
        """
        control, _composed, attempt_id, _held = self.held_episode(
            "guard-required")
        storage = self.storage_of(control)
        with self.assertRaises(TypeError):
            workspaces.discard_workspace(storage, attempt_id)
        for wrong in (None, object(), "a store"):
            with self.subTest(control=type(wrong).__name__):
                with self.assertRaises(ContractRefusal) as caught:
                    workspaces.discard_workspace(storage, attempt_id,
                                                 control=wrong)
                self.assertIn("control store", caught.exception.message)
        self.assertTrue(os.path.isdir(self.home_of(control, attempt_id)))

    # -- restart ------------------------------------------------------------

    def test_a_reopened_manager_is_bound_by_the_same_hold(self):
        """RESTART: the guard reads durable state, not process memory."""
        control, _composed, attempt_id, _held = self.held_episode(
            "guard-restart")
        storage = self.storage_of(control)
        control.close()

        reopened = self.reopened("guard-restart-again")
        self.addCleanup(reopened.close)
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.discard_workspace(storage, attempt_id,
                                         control=reopened)
        self.assertIn("FROZEN", caught.exception.message)
        self.assertTrue(os.path.isdir(os.path.join(storage, attempt_id)))


class TheAdoptionToUseWindowOnTheEndingPath(TheHoldAdmitsExactlyOneSubmitter):
    """Owner 262703's ONE milestone: the hold-after-check/before-use window.

    THE PATH, TRACED RATHER THAN ASSUMED. `single_worker.abandon_attempt`
    (tools/single_worker.py:2432) adopts the attempt's roots -- the lookup R3
    just gave a required store -- and then hands them on:

        adopted_assignment_workspace(...)        the check
          -> self._adapter(roots, ...).observe(...)   an engine question
          -> self._credential(attempt_id, state, roots, ...)
          -> intake.abandon_attempt(self.control, self.port, adapter, ...)
               -> the composed custody acts over the roots
               -> intake.py:_settle -> discard_execution_roots(...)

    The FIRST RESOURCE MUTATION of the adopted tree on this path is inside
    `intake.abandon_attempt`: the custody act, and then the removal. Everything
    before it reads. So the window the owner named is real and bounded -- it
    opens when the lookup answers and closes at whichever of those two gates
    the path reaches first.

    WHAT IS REAL AND WHAT IS FAKE: real `ControlStore`s, two real handles, real
    directories on a disk-backed root, and the accepted FAKE engine port. No
    daemon, container or image is reached by these cases.

    AND THE RACE IS INJECTED BY ORDERING, NOT BY THREADS. The window is a
    sequence, not a contention: a hold that commits between the answer and the
    use. Hooking the lookup to commit one there reproduces exactly that, every
    run, with no barrier to time out -- the write-lock contention itself is
    already proved by the two orderings above.
    """

    def ending(self, incarnation):
        """The accepted faulted attempt this path ends."""
        held, stage = self.faulted_with_stage(incarnation)
        return held[1], held[2], held[2]._worker, held[5], stage

    def holding(self, control, worker, attempt_id, lookup=None):
        """Commit ONE uncleared episode on the result root, as a real act does.

        Uses the fixture's own severing path and a SECOND real handle, so the
        episode under test is one `custody_act` recorded rather than a row this
        module wrote. The severing is spent on this submission alone, so the
        ending's own later acts still answer.
        """
        # THE LOOKUP IS AN OPERAND because the window case has this function
        # called from INSIDE a hook on the module-level name; reaching for that
        # name again would re-enter the hook and recurse, which is what it did.
        lookup = lookup or workspaces.adopted_assignment_workspace
        roots = lookup(worker.given["workspace_storage"], attempt_id,
                       control=control)
        composed = worker._adapter(roots, None, None, None)
        opened = self.reopened(f"window-{attempt_id[:12]}")
        self.addCleanup(opened.close)
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(opened, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        [episode] = [one for one in
                     custody.custody_holds(control, attempt_id, "result")
                     if not one["cleared"]]
        return episode

    def roots_of(self, worker, attempt_id):
        home = os.path.join(worker.given["workspace_storage"], attempt_id)
        return {name: os.path.join(home, name)
                for name in ("inputs", "workspace")}

    def test_a_hold_arriving_inside_the_window_still_stops_the_ending(self):
        """THE MILESTONE. The hold lands AFTER the lookup answered.

        The lookup is hooked to commit a real uncleared episode the instant it
        has answered -- which is the window, exactly -- and the ending then
        runs with roots it proved unheld and that are now held.
        """
        control, operations, worker, attempt_id, stage = self.ending("window-1")
        severed = self.severing(after=1)
        present = self.roots_of(worker, attempt_id)
        home = os.path.dirname(present["workspace"])
        # EVERY PATH AND ITS BYTES, so "no unintended effect" is measured over
        # the whole attempt home rather than asserted about two directories.
        walked = self.walked(home)
        before = self.vectors()
        held = workspaces.adopted_assignment_workspace
        injected = []

        def looking(*arguments, **operands):
            answer = held(*arguments, **operands)
            if not injected:                     # ONCE, inside the window
                injected.append(None)            # claim the slot FIRST
                injected[0] = self.holding(control, worker, attempt_id,
                                           lookup=held)
            return answer

        workspaces.adopted_assignment_workspace = looking
        self.addCleanup(setattr, workspaces,
                        "adopted_assignment_workspace", held)
        caught = None
        try:
            answered = ("answered", operations.abandon_attempt(
                attempt_id=attempt_id, reason=self.REASON, stage=stage))
        except ContractRefusal as refusal:
            caught, answered = refusal, ("refused", refusal.message)
        self.assertEqual(len(injected), 1, "the window was never entered")

        # AND THE GATE THAT STOPPED IT IS NAMED -- but only as far as the
        # evidence goes, which review 2026-09-25T04-25-17Z had to correct me on.
        # This message comes from `_claim_episode`'s OUTER PRELIMINARY READ, not
        # from its locked re-read, so it says the claim gate refused and NOT that
        # this schedule exercised the write lock. The lock coverage is proved
        # separately by the two orderings in `AHeldResourceIsNotRemoved`; it is
        # not inferable from this string, and I previously inferred it.
        #
        # WHAT THE WORDING DOES DISTINGUISH is which gate answered: the claim
        # gate says "no submission, no reclamation", the lookup guard says "no
        # adoption".
        self.assertEqual(answered[0], "refused", answered)
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertIn("no submission, no reclamation", answered[1])
        self.assertIn("FROZEN", answered[1])
        self.assertIn(injected[0]["held"]["helper_identity"], answered[1])
        for name, place in present.items():
            self.assertTrue(os.path.isdir(place),
                            f"the {name} root was removed behind a hold")
        # NOT ONE BYTE OF THE ADOPTED TREE CHANGED. Nothing on this path writes
        # into the home before the gate -- not the credential step, not the
        # runtime teardown.
        self.assertEqual(self.walked(home), walked,
                         "the ending changed the adopted tree behind a hold")
        # THE EPISODE STILL STANDS, unreconciled and unsettled by this path.
        self.assertEqual([(one["episode"], one["cleared"]) for one in
                          custody.custody_holds(control, attempt_id, "result")],
                         [(0, False)])
        # AND THE ENGINE SAW EXACTLY THIS, measured rather than guessed. My
        # first expectation here was wrong and the real ledger is the point:
        #
        #   run 1      the INJECTED custody submission, and only it. The
        #              ending's own custody act never submitted -- the hold
        #              stopped it before it could.
        #   ps 2, inspect 2   the fake's listings and inspections, which are
        #              questions and change nothing.
        #   rm 1       the attempt's RUNTIME container, destroyed on this path
        #              before the tree gates are reached. That is a container,
        #              NOT the adopted tree, and the tree assertions above are
        #              what say the tree was untouched.
        self.assertEqual(len(severed), 1, severed)
        counted = dict(self.vectors())
        for verb, count in before.items():
            counted[verb] = counted.get(verb, 0) - count
        self.assertEqual({verb: count for verb, count in counted.items()
                          if count},
                         {"ps": 2, "run": 1, "inspect": 2, "rm": 1}, counted)

    def test_a_hold_standing_before_the_lookup_refuses_the_lookup_itself(self):
        """THE OTHER ORDERING: the hold is already there.

        Then the guard R3 gave the lookup is what answers, and the ending never
        reaches a use at all.
        """
        control, operations, worker, attempt_id, stage = self.ending("window-2")
        self.severing(after=1)
        present = self.roots_of(worker, attempt_id)
        standing = self.holding(control, worker, attempt_id)

        with self.assertRaises(ContractRefusal) as caught:
            workspaces.adopted_assignment_workspace(
                worker.given["workspace_storage"], attempt_id, control=control)
        self.assertIn("FROZEN", caught.exception.message)
        self.assertIn("adopting this attempt's workspace roots",
                      caught.exception.message)

        home = os.path.dirname(present["workspace"])
        walked = self.walked(home)
        with self.assertRaises(ContractRefusal) as ending:
            operations.abandon_attempt(attempt_id=attempt_id,
                                       reason=self.REASON, stage=stage)
        self.assertIn(standing["held"]["helper_identity"],
                      ending.exception.message)
        self.assertIn("FROZEN", ending.exception.message)
        for name, place in present.items():
            self.assertTrue(os.path.isdir(place),
                            f"the {name} root was removed behind a hold")
        self.assertEqual(self.walked(home), walked,
                         "the ending changed the adopted tree behind a hold")


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Every case DEFINED IN THIS MODULE, and only those.

    Review 2026-09-25T04-25-17Z [loader]: this named one class, so the milestone
    class appended later was silently not collected by module selection and the
    combined count could not be cited as including it. IT NOW WALKS THE MODULE,
    so a class added tomorrow is collected without anybody remembering to.

    The `__dict__` filter stays and is the point of having a loader at all: both
    classes inherit real fixtures that carry their OWN accepted cases, and
    re-running those here would inflate this module's count with other modules'
    evidence. Only methods defined in the class itself run.
    """
    suite = unittest.TestSuite()
    for owner in list(globals().values()):
        if (isinstance(owner, type) and issubclass(owner, unittest.TestCase)
                and owner.__module__ == __name__):
            for name in loader.getTestCaseNames(owner):
                if name in owner.__dict__:
                    suite.addTest(owner(name))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
