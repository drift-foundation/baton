"""W270664 F2 — workspace removal is admitted in the database and performed outside it.

THE ONE BOUNDED SELECTOR for this Work. It reuses the accepted `Workspace` fixture from
`tests.manager.test_workspaces` -- which is NOT mine to change -- by subclassing it, so the
storage, the store and the attempt scaffolding are exactly the accepted ones.

NO LIVE ENGINE, PROVIDER OR DEPLOYED STORE. Disposable stores, this fixture's own temporary
directories, and no process is created or signalled.
"""
import os
import sqlite3
import threading
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import custody, intake, workspaces
from baton_v12.worker_manager.workspaces import (discard_execution_roots,
                                                 discard_workspace)

from tests.manager.test_intake import (ATTEMPT, RETENTION, Custodian,
                                       IntakeCase)
from tests.manager.test_workspaces import Workspace


class AnOpenTransaction:
    """Record whether a transaction was open at each filesystem call the removal makes.

    THE ONLY QUESTION THIS WORK EXISTS TO ANSWER, so it is asked at the syscalls
    themselves rather than inferred from the shape of the code. Every call records the
    owner connection's `in_transaction` at the moment it happens.
    """

    def __init__(self, connection):
        self.connection = connection
        self.observed = []

    def __enter__(self):
        self.patched = []
        for name in ("rmdir", "unlink", "chmod", "scandir", "lstat", "open"):
            honest = getattr(os, name)
            self.patched.append((name, honest))

            def watching(*args, _honest=honest, **kwargs):
                self.observed.append(self.connection.in_transaction)
                return _honest(*args, **kwargs)

            setattr(os, name, watching)
        return self

    def __exit__(self, *failure):
        for name, honest in self.patched:
            setattr(os, name, honest)
        return False


class RemovalOutsideTheLock(Workspace):

    def attempt_roots(self, assignment_id="assignment-1"):
        origin = self.origin({"a.txt": b"one"})
        roots = self.workspace(assignment_id)
        self.staged(origin, roots)
        return roots

    def temporary_root(self):
        """This fixture's own scratch directory, so a case never writes outside it."""
        return self.root

    def standing(self, assignment_id="assignment-1"):
        return workspaces.standing_removal(self.store, assignment_id)

    # -- the property this Work exists for ------------------------------------

    def test_no_filesystem_call_of_a_removal_happens_inside_a_transaction(self):
        """F2 ITSELF: the deletion and its walk run with no database lock held.

        `_serialized_removal` used to perform the hold read AND the removal inside one
        `control.transact`, which takes `BEGIN IMMEDIATE` -- so mount-table reads,
        permission changes and every `unlink` blocked all unrelated manager writes, and a
        rollback could not restore what was already gone. This asserts the corrected
        shape at the syscalls: `in_transaction` is FALSE at every one of them.
        """
        roots = self.attempt_roots()
        watcher = AnOpenTransaction(self.store._connection)
        with watcher:
            self.assertTrue(discard_workspace(self.storage, "assignment-1",
                                              control=self.store))
        self.assertTrue(watcher.observed, "the removal must reach the filesystem")
        self.assertFalse(any(watcher.observed),
                         "no external call of a removal may run under a database lock")
        self.assertFalse(os.path.exists(os.path.dirname(roots["inputs"])))

    def test_unrelated_database_progress_continues_while_a_removal_is_paused(self):
        """A PAUSED DELETION NO LONGER BLOCKS THE MANAGER, which is the point of F2.

        The removal is stopped mid-tree and a SECOND connection commits an unrelated write
        while it waits. Under the old shape that write blocked behind `BEGIN IMMEDIATE`
        until the deletion finished; here it commits immediately, which is what proves the
        lock is not held across the effect.
        """
        self.attempt_roots()
        # THE SECOND CONNECTION IS OPENED IN THE THREAD THAT USES IT. Measured: opening it
        # here and using it there raised sqlite3.ProgrammingError -- a connection belongs to
        # its thread -- and the unhandled error in the worker looked exactly like "the write
        # was blocked", which is the conclusion this case exists to test. A fixture that can
        # fail silently into the answer it is looking for is worse than no fixture.
        control_path = os.path.join(self.root, "control.sqlite3")
        committed = []
        paused = threading.Event()
        released = threading.Event()
        honest = os.rmdir

        def stopping(path, *args, **kwargs):
            if not committed:
                paused.set()
                released.wait(10)
            return honest(path, *args, **kwargs)

        failures = []

        def unrelated():
            try:
                paused.wait(10)
                beside = sqlite3.connect(control_path, timeout=5)
                try:
                    beside.execute("CREATE TABLE IF NOT EXISTS unrelated_progress "
                                   "(n INTEGER)")
                    beside.execute("BEGIN IMMEDIATE")
                    beside.execute("INSERT INTO unrelated_progress VALUES (1)")
                    beside.commit()
                finally:
                    beside.close()
                committed.append(True)
            except BaseException as failure:            # reported, never swallowed
                failures.append(failure)
            finally:
                released.set()

        worker = threading.Thread(target=unrelated)
        worker.start()
        os.rmdir = stopping
        try:
            self.assertTrue(discard_workspace(self.storage, "assignment-1",
                                              control=self.store))
        finally:
            os.rmdir = honest
            released.set()
            worker.join(10)
        self.assertEqual(failures, [], f"the unrelated writer failed: {failures}")
        self.assertEqual(committed, [True],
                         "an unrelated write must commit while the deletion is paused")

    # -- the exclusion, both ways ---------------------------------------------

    def test_a_hold_recorded_before_admission_refuses_the_removal(self):
        """PRE-EFFECT EXCLUSION, not a completion-time apology.

        Review 2026-09-26T06:21:32Z: "A completion-time hold check alone is too late." A
        custody hold recorded for either root refuses the removal in the admission
        transaction, before anything is deleted and before any ownership is taken.
        """
        roots = self.attempt_roots()
        custody._record_hold(self.store, "assignment-1", "workspace",
                             "submit", "sha256:" + "1" * 64, "helper-1")
        with self.assertRaises(ContractRefusal) as caught:
            discard_workspace(self.storage, "assignment-1", control=self.store)
        # THE EXISTING TYPED REFUSAL IS PRESERVED EXACTLY. `refuse_if_held` owns this
        # message and its `policy` category; what F2 changed is only WHERE it runs --
        # outside every transaction now -- so the assertion is on the accepted refusal
        # rather than on a new one.
        self.assertEqual(caught.exception.category, "policy")
        # NOTHING WAS DELETED AND NO OWNERSHIP WAS TAKEN.
        self.assertTrue(os.path.exists(os.path.dirname(roots["inputs"])))
        self.assertEqual(self.standing(), [])

    def test_a_custody_claim_is_refused_while_a_removal_ownership_stands(self):
        """THE RECIPROCAL HALF, which the ownership record alone would not have given.

        Review 2026-09-26T06:21:32Z found that `custody._claim_episode`'s claiming callback
        reads custody overlap and nothing about a removal -- so an ownership record would
        have excluded nothing and a hold could commit while the tree came off the disk.
        The claim now reads `standing_removal` under its OWN `BEGIN IMMEDIATE`, so whichever
        act is admitted first excludes the other.
        """
        self.attempt_roots()
        interrupted = []
        honest = os.rmdir

        def dying(path, *args, **kwargs):
            interrupted.append(path)
            raise RuntimeError("the remover died mid-tree")

        os.rmdir = dying
        try:
            with self.assertRaisesRegex(RuntimeError, "died mid-tree"):
                discard_workspace(self.storage, "assignment-1", control=self.store)
        finally:
            os.rmdir = honest
        self.assertTrue(interrupted)
        # THE OWNERSHIP STANDS WITH NO COMPLETION, which is the held state.
        self.assertEqual(len(self.standing()), 1)
        with self.assertRaises(ContractRefusal) as caught:
            custody._claim_episode(self.store, "assignment-1", "workspace",
                                   "submit", "sha256:" + "2" * 64, "helper-2")
        self.assertIn("being removed under removal ownership",
                      caught.exception.message)

    def test_an_interrupted_removal_is_held_rather_than_repeated(self):
        """AN UNRESOLVED REMOVAL IS NOT RETRIED ON A GUESS.

        Owner 270664: "Interrupted or uncertain removal must remain held." A removal that
        died mid-tree left ownership with no completion, so the next removal of the same
        attempt refuses and names the ordinal rather than deleting whatever is left.
        """
        self.attempt_roots()
        honest = os.rmdir

        def dying(path, *args, **kwargs):
            raise RuntimeError("the remover died mid-tree")

        os.rmdir = dying
        try:
            with self.assertRaisesRegex(RuntimeError, "died mid-tree"):
                discard_workspace(self.storage, "assignment-1", control=self.store)
        finally:
            os.rmdir = honest
        with self.assertRaises(ContractRefusal) as caught:
            discard_workspace(self.storage, "assignment-1", control=self.store)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("recorded no completion", caught.exception.message)
        # THE CHOKEPOINT ANSWERS FIRST NOW, and it says the broader true thing: these roots
        # are not reused, adopted OR removed again until the unresolved removal is
        # reconciled. Review 2026-09-26T07:21:42Z asked for the reciprocal exclusion at the
        # point every entry already passes through, so this assertion follows it there
        # rather than pinning the admission's older wording.
        self.assertIn("not reused, adopted or removed again",
                      caught.exception.message)

    # -- exact answers, preserved --------------------------------------------

    def test_each_removal_answers_its_own_truth_and_never_a_replay(self):
        """EXACT PER-CALL ANSWERS, which the ownership must not quietly replace.

        `discard_execution_roots` answers WHICH roots this act removed, and `()` when there
        were none. The previous shape carried a nonce precisely so a second removal was not
        a replay of the first's answer; the ownership ordinal does that job now, and this
        asserts the property rather than the mechanism.
        """
        self.attempt_roots()
        first = discard_execution_roots(self.storage, "assignment-1",
                                        control=self.store)
        self.assertTrue(first, "the first act removed the roots it found")
        second = discard_execution_roots(self.storage, "assignment-1",
                                         control=self.store)
        self.assertEqual(tuple(second), (),
                         "a second act over an empty home removes nothing and says so")
        # TWO ACTS, TWO OWNERSHIPS, TWO COMPLETIONS -- and nothing standing.
        self.assertEqual(self.standing(), [])
        self.assertIsNotNone(self.store.operation_record(
            workspaces._removal_complete_id("assignment-1", 1)))
        self.assertIsNotNone(self.store.operation_record(
            workspaces._removal_complete_id("assignment-1", 2)))

    def test_a_hold_that_arrives_before_the_admission_still_refuses(self):
        """THE ADMISSION RE-READS THE HOLDS UNDER ITS OWN LOCK, and that is not decoration.

        The outer `refuse_if_held` is the early refusal for the ordinary case and it runs
        OUTSIDE every transaction, because it reaches `realpath`. That leaves an interval:
        a custody hold can commit after it answers clean and before the removal is admitted.
        The admission transaction therefore reads both roots' holds again, in pure SQL, under
        the `BEGIN IMMEDIATE` that decides -- so the hold either commits first and is seen
        here, or it waits and is refused by the reciprocal check afterwards.

        STAGED DETERMINISTICALLY by committing the hold from inside the outer check's own
        return, so the arrival provably falls in that interval rather than probably.
        """
        roots = self.attempt_roots()
        honest = workspaces.refuse_if_held
        arrived = []

        def checking(control, storage, assignment_id, what, settlement=None):
            answer = honest(control, storage, assignment_id, what, settlement)
            if not arrived:
                arrived.append(True)
                custody._record_hold(self.store, assignment_id, "result",
                                     "submit", "sha256:" + "3" * 64, "helper-3")
            return answer

        workspaces.refuse_if_held = checking
        self.addCleanup(setattr, workspaces, "refuse_if_held", honest)
        with self.assertRaises(ContractRefusal) as caught:
            discard_workspace(self.storage, "assignment-1", control=self.store)
        self.assertEqual(arrived, [True])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("carries recorded custody episode", caught.exception.message)
        # NOTHING WAS DELETED AND NO OWNERSHIP WAS TAKEN.
        self.assertTrue(os.path.exists(os.path.dirname(roots["inputs"])))
        self.assertEqual(self.standing(), [])

    def test_reuse_and_adoption_are_excluded_while_a_removal_is_unresolved(self):
        """THE RECIPROCAL EXCLUSION COVERS REUSE AND ADOPTION, not only a second removal.

        Review 2026-09-26T07:21:42Z: the exclusion belongs at the chokepoint every entry
        already calls. `refuse_if_held` is that point -- allocation, adoption and removal all
        pass through it -- so one reading of the removal ownership covers all three, and it is
        the same reading `custody._claim_episode` makes under its own lock.

        AND THIS IS WHAT COVERS THE FINAL ENTRY. What makes the last `rmdir` safe is not a
        better stat but that nothing else may create, adopt or remove at that name while the
        ownership stands: an exclusion rather than an inference.
        """
        self.attempt_roots()
        honest = os.rmdir

        def dying(path, *args, **kwargs):
            raise RuntimeError("the remover died mid-tree")

        os.rmdir = dying
        try:
            with self.assertRaisesRegex(RuntimeError, "died mid-tree"):
                discard_workspace(self.storage, "assignment-1", control=self.store)
        finally:
            os.rmdir = honest
        self.assertEqual(len(self.standing()), 1)
        # ADOPTION is refused -- the entry that reuses an existing home.
        with self.assertRaises(ContractRefusal) as adopting:
            workspaces.adopted_assignment_workspace(self.storage, "assignment-1",
                                                    control=self.store)
        self.assertIn("not reused, adopted or removed again", adopting.exception.message)
        # AND SO IS A CUSTODY CLAIM, from the other side of the same fact.
        with self.assertRaises(ContractRefusal):
            custody._claim_episode(self.store, "assignment-1", "workspace",
                                   "submit", "sha256:" + "5" * 64, "helper-5")

    def test_removal_and_adoption_exclude_each_other_in_both_orders(self):
        """MUTUAL ADMISSION, not two reads of each other's absence.

        Review 2026-09-26T07:25:48Z caught my first reciprocal attempt for what it was: a READ
        before the act. Their probe walked through it -- adoption read "no standing removal", a
        removal was admitted after that read, and adoption proceeded. A guard that answers
        before the competing act commits excludes nothing.

        SO BOTH ACTS ARE ADMITTED IN THEIR OWN SHORT `BEGIN IMMEDIATE`, and each reads the
        other's record inside its own transaction. This case runs BOTH ORDERS:

        REMOVAL FIRST -- an interrupted removal leaves its ownership standing, and adoption is
        then refused by its own admission rather than after it.

        ADOPTION FIRST -- an adoption admitted and not yet settled refuses the removal's
        admission, and the roots are untouched. The record is settled afterwards, and the
        removal then succeeds, so the exclusion is a window rather than a permanent hold.
        """
        # ADOPTION FIRST: the window excludes the removal while it stands.
        roots = self.attempt_roots("assignment-9")
        owned = workspaces._admitted_adoption(self.store, "assignment-9",
                                              "review adoption in flight")
        self.assertEqual(len(workspaces.standing_adoption(self.store, "assignment-9")), 1)
        with self.assertRaises(ContractRefusal) as blocked:
            discard_workspace(self.storage, "assignment-9", control=self.store)
        self.assertEqual((blocked.exception.category, blocked.exception.code),
                         ("refused", "precondition"))
        self.assertIn("adoption 1 of this attempt's roots was admitted",
                      blocked.exception.message)
        self.assertTrue(os.path.exists(os.path.dirname(roots["inputs"])))
        self.assertEqual(self.standing("assignment-9"), [])
        # AND IT IS A WINDOW, NOT A HOLD: settled, the removal proceeds.
        workspaces._settled_adoption(self.store, "assignment-9", owned)
        self.assertEqual(workspaces.standing_adoption(self.store, "assignment-9"), [])
        self.assertTrue(discard_workspace(self.storage, "assignment-9",
                                         control=self.store))

        # REMOVAL FIRST: an interrupted removal refuses adoption at its own admission.
        self.attempt_roots("assignment-8")
        honest = os.rmdir

        def dying(path, *args, **kwargs):
            raise RuntimeError("the remover died mid-tree")

        os.rmdir = dying
        try:
            with self.assertRaisesRegex(RuntimeError, "died mid-tree"):
                discard_workspace(self.storage, "assignment-8", control=self.store)
        finally:
            os.rmdir = honest
        self.assertEqual(len(self.standing("assignment-8")), 1)
        with self.assertRaises(ContractRefusal) as adopting:
            workspaces.adopted_assignment_workspace(self.storage, "assignment-8",
                                                    control=self.store)
        self.assertEqual((adopting.exception.category, adopting.exception.code),
                         ("refused", "precondition"))
        # NO ADOPTION WINDOW WAS LEFT STANDING by the refused act.
        self.assertEqual(workspaces.standing_adoption(self.store, "assignment-8"), [])

        # AND A SUCCESSFUL ADOPTION SETTLES ITS OWN WINDOW: measured, because a window the
        # product opened and never closed would block that attempt's removal forever, which is
        # the failure mode an exclusion turns into when it is mistaken for a hold.
        # AND A BARE ADOPTION KEEPS ITS WINDOW UNTIL THE CALLER ENDS IT -- the correction
        # review 2026-09-26T07:35:55Z required. The old shape settled in a `finally`, so the
        # window closed before the caller held the roots; now it reaches the caller, the
        # removal is refused while it stands, and `release_adopted_workspace` is what ends it.
        self.attempt_roots("assignment-7")
        adopted = workspaces.adopted_assignment_workspace(self.storage, "assignment-7",
                                                          control=self.store)
        self.assertTrue(adopted["workspace"])
        self.assertEqual(len(workspaces.standing_adoption(self.store, "assignment-7")), 1)
        with self.assertRaises(ContractRefusal) as held:
            discard_workspace(self.storage, "assignment-7", control=self.store)
        self.assertIn("adoption 1 of this attempt's roots was admitted",
                      held.exception.message)
        self.assertTrue(os.path.isdir(adopted["inputs"]),
                        "the roots the caller is holding must still be there")
        workspaces.release_adopted_workspace(adopted)
        self.assertEqual(workspaces.standing_adoption(self.store, "assignment-7"), [])
        self.assertTrue(discard_workspace(self.storage, "assignment-7",
                                         control=self.store))

        # AND THE GRANT IS THE OTHER WAY OUT, BUT ONLY IF THERE IS SOMETHING TO HAND OVER TO.
        # Review 2026-09-26T08:09:45Z: settling at every binding was still premature, because a
        # grant can be bound while the DURABLE state says nothing -- no active writer, no active
        # attachment -- and the settle then dropped the exclusion with nothing behind it. So the
        # binding releases the window exactly when `_durably_in_use` answers, and otherwise the
        # window travels on with the granted roots.
        self.attempt_roots("assignment-6")
        carried = workspaces.adopted_assignment_workspace(self.storage, "assignment-6",
                                                          control=self.store)
        self.assertEqual(len(workspaces.standing_adoption(self.store, "assignment-6")), 1)
        # NOTHING DURABLE: the window is CARRIED, and the granted roots can still end it.
        granted = workspaces._granted_roots(carried, lambda: True)
        self.assertTrue(granted["workspace"])
        self.assertEqual(len(workspaces.standing_adoption(self.store, "assignment-6")), 1)
        workspaces.release_adopted_workspace(granted)
        self.assertEqual(workspaces.standing_adoption(self.store, "assignment-6"), [])
        # DURABLE USE REPORTED: the binding is a real handover and settles the window.
        again = workspaces.adopted_assignment_workspace(self.storage, "assignment-6",
                                                        control=self.store)
        honest_use = workspaces._durably_in_use
        workspaces._durably_in_use = lambda control, attempt: (
            ("an active line writer", "writer-6") if attempt == "assignment-6"
            else honest_use(control, attempt))
        self.addCleanup(setattr, workspaces, "_durably_in_use", honest_use)
        handed = workspaces._granted_roots(again, lambda: True)
        self.assertTrue(handed["workspace"])
        self.assertEqual(workspaces.standing_adoption(self.store, "assignment-6"), [])

    def test_durable_use_refuses_a_removal_for_as_long_as_it_holds(self):
        """THE TARGET THAT MAKES THE GRANT BINDING A REAL HANDOVER.

        Review 2026-09-26T08:02:18Z: settling the adoption window at the grant binding was not a
        handover, because the removal read NOTHING that changes when a grant is bound. It now
        reads the very facts the grants themselves test -- a writer ACTIVE for the attempt or a
        review attachment ACTIVE for it -- in pure SQL inside its admission transaction.

        WHAT THIS CASE COVERS AND WHAT IT DOES NOT, stated because the difference matters. It
        covers the REMOVAL'S CONSUMPTION of that answer: while use is reported the removal is
        refused and takes no ownership, and when it stops being reported the removal proceeds.
        It does NOT cover the SQL itself -- inserting a writer row needs a real line and
        attachment to satisfy the foreign keys, which this fixture has no machinery for, and
        `_durably_in_use` is therefore replaced by a labelled answer here. The reader's own
        query is unproved and that is recorded in PROGRESS rather than implied to be covered.
        """
        self.attempt_roots("assignment-5")
        in_use = [("an active line writer", "writer-in-use")]
        honest = workspaces._durably_in_use

        def reported(control, assignment_id):
            if assignment_id == "assignment-5" and in_use:
                return in_use[0]
            return honest(control, assignment_id)

        workspaces._durably_in_use = reported
        self.addCleanup(setattr, workspaces, "_durably_in_use", honest)
        with self.assertRaises(ContractRefusal) as caught:
            discard_workspace(self.storage, "assignment-5", control=self.store)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("held by an active line writer", caught.exception.message)
        self.assertEqual(self.standing("assignment-5"), [],
                         "a refused removal takes no ownership")
        # AND WHEN USE STOPS BEING REPORTED the same removal proceeds.
        in_use.clear()
        self.assertTrue(discard_workspace(self.storage, "assignment-5",
                                         control=self.store))

    def test_a_removal_asked_inside_a_transaction_is_refused_now(self):
        """THE NESTED SHORTCUT IS GONE, and that is the enclosing entry's correction landing.

        `_serialized_removal` used to see `connection.in_transaction`, recheck the holds and
        delete right there. It existed for exactly one caller -- `intake._settle`, which removed
        from inside its own `runtime.destroy` transaction -- and that call now happens in
        `authorize_cleanup` with no lock held. So there is no legitimate caller left, and serving
        one would discard every property this correction establishes: the ownership record, the
        hold on an interrupted removal, and the rule that no database lock spans the effect.
        """
        self.attempt_roots()
        connection = self.store._connection
        connection.execute("BEGIN IMMEDIATE")
        try:
            with self.assertRaises(ContractRefusal) as caught:
                discard_workspace(self.storage, "assignment-1", control=self.store)
        finally:
            connection.execute("ROLLBACK")
        self.assertIn("from inside an open database transaction",
                      caught.exception.message)
        # NOTHING WAS DELETED AND NO OWNERSHIP WAS TAKEN.
        self.assertTrue(os.path.isdir(os.path.join(self.storage, "assignment-1")))
        self.assertEqual(self.standing(), [])

    def test_a_cleared_history_is_not_a_hold_and_a_mixed_one_refuses_only_for_the_live(self):
        """CLEARED IS HISTORY; ONLY A LIVE HOLD REFUSES.

        Review 2026-09-26T06:34:57Z caught my first reader returning EVERY recorded episode,
        so a root whose uncertainty an operator had already reconciled could never be
        removed -- a permanent false refusal, and a worse failure than the one this
        correction is about. The predicate is now `custody._standing_overlap`, the accepted
        one `_claim_episode` itself uses.

        THREE HISTORIES, ONE PREDICATE: no history removes; a history whose only episode is
        cleared removes; a MIXED history with one cleared and one live episode refuses, and
        names the live one. The mixed case is the one a single-flag reader gets wrong in
        either direction.
        """
        # no history at all
        self.attempt_roots("assignment-1")
        self.assertTrue(discard_workspace(self.storage, "assignment-1",
                                          control=self.store))

        # A SIMULATED CLEARANCE, LABELLED AS ONE. Review 2026-09-26T06:39:23Z is right that
        # this mocks the READER's validated output rather than performing an operator's
        # reconciliation: a real clearance goes through `custody.clear_custody_hold`, which
        # requires the operator's account AND the engine's own settlement, and that path has
        # no exercise anywhere in this build yet. What this case proves is exactly the
        # predicate boundary -- that a `cleared` episode is not read as standing -- and it
        # proves nothing about producing one. The real-clearance case is remaining scope and
        # is named as such in PROGRESS.
        self.attempt_roots("assignment-2")
        custody._record_hold(self.store, "assignment-2", "workspace",
                             "submit", "sha256:" + "4" * 64, "helper-4")
        self.assertIsNotNone(custody._standing_hold(self.store, "assignment-2",
                                                    "workspace"))
        cleared = [dict(one, cleared=True)
                   for one in custody.custody_holds(self.store, "assignment-2",
                                                    "workspace")]

        def reconciled(store, assignment_id, which):
            if assignment_id == "assignment-2" and which == "workspace":
                return cleared
            return []

        with mock.patch.object(custody, "custody_holds", side_effect=reconciled):
            self.assertIsNone(custody._standing_overlap(self.store, "assignment-2",
                                                        "workspace"))
            self.assertTrue(discard_workspace(self.storage, "assignment-2",
                                              control=self.store))

        # A MIXED history, same simulation and same limit: one cleared, one live
        self.attempt_roots("assignment-3")
        mixed = [dict(cleared[0], episode=0, cleared=True),
                 dict(cleared[0], episode=1, cleared=False, root="workspace")]

        def partly(store, assignment_id, which):
            if assignment_id == "assignment-3" and which == "workspace":
                return mixed
            return []

        with mock.patch.object(custody, "custody_holds", side_effect=partly):
            with self.assertRaises(ContractRefusal) as caught:
                discard_workspace(self.storage, "assignment-3", control=self.store)
        # THE OUTER CHECK ANSWERS FIRST, with its own accepted typed refusal: a live hold in
        # a mixed history is refused before the admission is reached at all. The admission's
        # own re-read of the same predicate has its own case -- the hold that arrives in the
        # interval -- so this one asserts what actually happens rather than what I expected.
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        self.assertEqual(self.standing("assignment-3"), [])

    def test_a_home_replaced_after_admission_is_not_the_object_authorized(self):
        """THE OWNERSHIP IS FOR AN OBJECT, NOT FOR A NAME.

        Review 2026-09-26T06:48:32Z. The effect now runs outside every lock, so a home
        replaced between the admission and the removal would be deleted under an authority
        granted for a different inode. `_real` already refuses a symlinked home at entry;
        this closes the interval AFTER that proof, which is the same reason
        `discard_execution_roots` opens a directory descriptor rather than trusting a name.

        STAGED DETERMINISTICALLY by swapping the home for a different real directory from
        inside the admission itself, so the replacement provably falls in the interval. The
        substitute is this fixture's own temporary directory and nothing outside it is
        touched.
        """
        self.attempt_roots()
        home = os.path.join(self.storage, "assignment-1")
        substitute = os.path.join(self.temporary_root(), "substitute-home")
        os.makedirs(substitute, exist_ok=True)
        honest = workspaces._admitted_removal
        swapped = []

        def admitting(control, assignment_id, what, pinned=None, under=None):
            owned = honest(control, assignment_id, what, pinned, under)
            if not swapped:
                swapped.append(True)
                os.rename(home, home + ".moved")
                os.rename(substitute, home)
            return owned

        workspaces._admitted_removal = admitting
        self.addCleanup(setattr, workspaces, "_admitted_removal", honest)
        with self.assertRaises(ContractRefusal) as caught:
            discard_workspace(self.storage, "assignment-1", control=self.store)
        self.assertEqual(swapped, [True])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("runtime-observation", "identity-mismatch"))
        self.assertIn("names a different one", caught.exception.message)
        # THE SUBSTITUTE SURVIVES: nothing was deleted under the wrong authority.
        self.assertTrue(os.path.exists(home))

    def test_a_descendant_replaced_mid_removal_cannot_reach_outside_material(self):
        """THE DESCENDANT ESCAPE, AT THE POINT THE NEW WALK ACTUALLY REACHES.

        Review 2026-09-26T07:07:30Z found it and 07:14:23Z prescribed the fix: the admission
        RETAINS a handle for every directory it clears, and the removal pass operates on those
        handles -- `fchmod` on the handle, `unlink`/`rmdir` by name RELATIVE to it. No name is
        resolved from the root twice, so nothing a descendant becomes afterwards can redirect
        a scan, a mode change or a deletion.

        AND THE REVIEWER'S OWN PROBE NO LONGER TRIGGERS, which I am not counting as proof.
        `review_descendant_swap_20260926.py` interposes on `_thaw(path)`; the handle walk calls
        `_thaw_handle(handle)` and never hands a path to `_thaw` for a descendant, so that
        probe's swap never fires and its first assertion fails. Review 07:14:23Z says exactly
        what to do about that -- "adapt a new schedule if a legitimate internal refactor
        retires the old interception point; never count a non-triggered probe as proof" -- so
        this case is that adapted schedule, at the new interception point, asserting the same
        property the reviewer's probe asserts: OUTSIDE MATERIAL SURVIVES.
        """
        self.attempt_roots()
        child = os.path.join(self.storage, "assignment-1", "workspace")
        outside = os.path.join(self.temporary_root(), "outside-tree")
        os.mkdir(outside)
        marker = os.path.join(outside, "keep.txt")
        with open(marker, "w") as stream:
            stream.write("outside the authorized tree")
        honest = workspaces._thaw_handle
        swapped = []

        def thawing(handle, what):
            # AT THE FIRST THAW OF THE REMOVAL PASS, the descendant's NAME is replaced by a
            # symlink to material outside the tree -- the exact schedule the reviewer's probe
            # runs, moved to the call the new walk makes.
            if not swapped:
                swapped.append(True)
                os.rename(child, outside + ".saved-workspace")
                os.symlink(outside, child)
            return honest(handle, what)

        workspaces._thaw_handle = thawing
        self.addCleanup(setattr, workspaces, "_thaw_handle", honest)
        try:
            discard_workspace(self.storage, "assignment-1", control=self.store)
        except (ContractRefusal, OSError):
            pass
        self.assertEqual(swapped, [True], "the swap must actually happen")
        self.assertTrue(os.path.isfile(marker),
                        "outside material must survive a replaced descendant")

    def test_an_absent_home_with_an_unresolved_removal_is_not_an_answer(self):
        """ABSENT IS NOT THE SAME AS RESOLVED.

        Review 2026-09-26T06:39:23Z asked for this distinction and it is a real gap, not a
        nicety: a home can be gone BECAUSE an admitted removal was part way through when it
        stopped. Answering `False` there reports the caller's desired state while the act
        that produced it is unaccounted for. So an unresolved removal refuses before the
        absence shortcut, and the ordinary absent-home answer survives untouched for a home
        with nothing outstanding -- which its own case asserts.
        """
        self.attempt_roots()
        honest = os.rmdir
        emptied = []

        def dying(path, *args, **kwargs):
            # the tree is really removed and THEN the act dies, which is exactly the state
            # this distinction is about: gone, and nobody accounted for it
            honest(path, *args, **kwargs)
            emptied.append(path)
            if len(emptied) >= 1 and path.endswith("assignment-1"):
                raise RuntimeError("the remover died after emptying the home")

        os.rmdir = dying
        try:
            with self.assertRaisesRegex(RuntimeError, "died after emptying"):
                discard_workspace(self.storage, "assignment-1", control=self.store)
        finally:
            os.rmdir = honest
        self.assertEqual(len(self.standing()), 1)
        # THE HOME IS MADE GENUINELY ABSENT, because that is the state this distinction is
        # about. Measured: with the home still partly present the ADMISSION's own refusal
        # arrives first -- also a hold, but a different sentence -- so the case removes what
        # the interrupted act left rather than asserting whichever guard happened to answer.
        import shutil

        home = os.path.join(self.storage, "assignment-1")
        if os.path.exists(home):
            shutil.rmtree(home, ignore_errors=True)
        self.assertFalse(os.path.exists(home))
        with self.assertRaises(ContractRefusal) as caught:
            discard_workspace(self.storage, "assignment-1", control=self.store)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("absence cannot be read as the state", caught.exception.message)

    def test_an_absent_home_is_still_an_answer_rather_than_a_refusal(self):
        """THE ACCEPTED ASYMMETRY IS PRESERVED: gone is the state the caller asked for."""
        self.assertFalse(discard_workspace(self.storage, "never-created",
                                          control=self.store))

    # -- the cleanup's exclusion, from admission to settlement -----------------

    def settlement(self, operation="runtime.destroy:attempt-1", signature="sig-1"):
        return {"operation": operation, "signature": signature,
                "incarnation": self.store.incarnation}

    def admitted(self, assignment_id="assignment-1", **named):
        return workspaces.admit_cleanup(self.store, assignment_id,
                                        self.settlement(**named),
                                        f"cleaning up attempt {assignment_id!r}")

    def test_an_unsettled_cleanup_refuses_allocation_reuse_and_removal(self):
        """THE WINDOW REVIEW 2026-09-26T09:15:26Z REPRODUCED, closed at the chokepoint.

        Their probe interrupted a real cleanup after both execution roots were removed
        and before `runtime.destroy` committed, allocated the attempt's roots again, and
        watched the cleanup's retry delete material created inside them. The removal's
        own ownership is not what was missing -- it had correctly completed -- so the
        cleanup now owns a record of its own that stands for the whole span between its
        eligibility and its ending, and every other entry reads it.
        """
        self.attempt_roots()
        self.admitted()
        for what, act in (
            ("allocation", lambda: workspaces.assignment_workspace(
                self.group, self.storage, "assignment-1")),
            ("adoption", lambda: workspaces.adopted_assignment_workspace(
                self.storage, "assignment-1", control=self.store)),
            ("another removal", lambda: discard_workspace(
                self.storage, "assignment-1", control=self.store)),
        ):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    act()
                self.assertIn("has recorded no settlement",
                              caught.exception.message)

    def test_the_same_operation_adopts_its_own_admission_and_another_is_refused(self):
        """RECOVERABLE RETRY, AND ONLY FOR THE ACT THAT OWNS IT.

        Review 09:15:26Z: "A standing removal must not be blindly adopted merely because
        attempt IDs match: concurrent/live ownership, changed operands, stale completion
        and interruption require attribution/fencing." So the admission carries the
        operation it will settle under, that operation's SIGNATURE, and the incarnation
        that took it -- and adoption requires the first two to be identical.
        """
        self.attempt_roots()
        first = self.admitted()
        # THE RETRY TAKES IT OVER RATHER THAN JOINING IT, and review 2026-09-26T10:07:07Z
        # is why this assertion changed. I had it returning the SAME owner, which let two
        # live executions of one act both believe they held it -- their probe paused the
        # first caller, let the second adopt and settle, and the first then deleted
        # material allocated afterwards. Same ordinal, NEW owner, and the old owner is
        # fenced out of every act performed under the admission.
        again = self.admitted()
        self.assertEqual(again["ordinal"], first["ordinal"])
        self.assertNotEqual(again["owner"], first["owner"])
        self.assertEqual(len(workspaces.standing_cleanup(self.store, "assignment-1")), 1)
        # THE DISPLACED OWNER CANNOT ACT. Its removal is refused in the admission
        # transaction that would authorize the deletion, which is the point: the fencing
        # has to stop the EFFECT, not just the bookkeeping.
        with self.assertRaises(ContractRefusal) as fenced:
            workspaces._admitted_removal(self.store, "assignment-1",
                                         "removing this attempt's execution roots",
                                         None, first)
        self.assertIn("taken over by a later act", fenced.exception.message)
        # AND THE CURRENT OWNER CAN. Same transaction, same attempt, the live authority.
        self.assertTrue(workspaces._admitted_removal(
            self.store, "assignment-1", "removing this attempt's execution roots",
            None, again))
        # A DIFFERENT OPERATION over the same attempt is another act.
        with self.assertRaises(ContractRefusal) as other:
            self.admitted(operation="runtime.destroy:somebody-else")
        self.assertIn("admitted under operation", other.exception.message)
        # THE SAME OPERATION WITH CHANGED OPERANDS is not a retry of what was admitted.
        with self.assertRaises(ContractRefusal) as changed:
            self.admitted(signature="sig-2")
        self.assertIn("DIFFERENT operands", changed.exception.message)

    def test_a_live_allocation_refuses_a_cleanup_and_a_removal_reciprocally(self):
        """THE OTHER DIRECTION, because an exclusion that only reads one way is not one.

        Review 2026-09-26T10:07:07Z required "atomic reciprocal allocation admission and
        cleanup/removal admission, durable exclusion across effects". Their probe proved the
        allocation side; this is the side facing it: while an allocation is admitted and has
        recorded no completion, a caller IS creating these roots, and what it creates would
        be newer than the authority of any act that removed it. Both admitting transactions
        read the other's record in pure SQL under `BEGIN IMMEDIATE`, so whichever commits
        first wins and the loser is told exactly what it lost to.
        """
        self.attempt_roots()
        live = workspaces._admitted_allocation(
            self.store, "assignment-1", "allocating this attempt's execution roots")
        self.assertEqual(len(workspaces.standing_allocation(self.store, "assignment-1")), 1)
        with self.assertRaises(ContractRefusal) as cleanup:
            self.admitted()
        self.assertIn("is creating them right now", cleanup.exception.message)
        with self.assertRaises(ContractRefusal) as removal:
            discard_workspace(self.storage, "assignment-1", control=self.store)
        self.assertIn("is creating them right now", removal.exception.message)
        # AND IT IS A WINDOW, NOT A WALL. The completion closes it, and both acts proceed.
        workspaces._completed_allocation(self.store, "assignment-1", live)
        self.assertEqual(workspaces.standing_allocation(self.store, "assignment-1"), [])
        self.assertTrue(self.admitted())

    def test_a_journal_that_cannot_be_asked_refuses_the_allocation(self):
        """NOT BEING ABLE TO TELL IS NOT AN ANSWER OF "NOTHING IS HELD".

        Review 2026-09-26T10:26:51Z proved the fail-open with a `PermissionError` on the
        journal's own `stat`, which `os.path.isfile` swallowed into `False`; my code read
        that as "no record can be there" and allocated straight through a standing cleanup.
        Their probe owns the unreadable case. This owns the ABSENT one, which I had argued
        was different and is not: "a pathname disappearing does not release the authority of
        handles still open on that database", so every way of being unable to ask refuses.
        """
        self.attempt_roots("assignment-2")
        group = workspaces.configured_workspace_group(self.store)
        self.assertTrue(os.path.isfile(group.store_place))
        # THE HANDLE IS SHUT AND THE FILE IS REMOVED, so the reopen has nothing to reopen.
        # Both halves are needed: with the handle live the question is simply answered.
        self.store._connection.close()
        os.unlink(group.store_place)
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.assignment_workspace(group, self.storage, "assignment-3")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        # THE CONTRACT ANSWERS BEFORE THE FILE IS EVEN LOOKED AT, and that is the corrected
        # shape: nothing reopens the database, so whether it is absent, unreadable or intact
        # no longer changes the outcome for a control that cannot be used here. The earlier
        # version of this case asserted the absence message from the reopen path; the reopen
        # is gone (reviews 10:53:09Z through 11:19:15Z) and so is that message.
        self.assertIn("cannot be used from this thread", caught.exception.message)
        # AND NOTHING WAS CREATED for the attempt it could not ask about.
        self.assertFalse(os.path.exists(os.path.join(self.storage, "assignment-3")))

    def test_a_control_that_cannot_be_used_here_is_refused_and_says_what_to_pass(self):
        """THE CLOSED AND OFF-THREAD CONTRACT, which is now a refusal rather than a reopen.

        FOUR CASES USED TO LIVE HERE and they are gone rather than adjusted, because what
        they measured no longer exists. They pinned a reopen that tried to prove the
        database it got was the journal the selected control had been opened on: first by
        comparing a `stat` of the pathname taken before the open (review 2026-09-26T10:53:09Z
        swapped the file in between), then by scanning the process for a descriptor naming
        that pathname (11:04:20Z held a witness on the original and my scan approved the
        replacement), then by attributing only descriptors created across the open
        (11:19:15Z opened an unrelated descriptor INSIDE that window and it was approved
        again). Each version accepted a replacement journal's answer for the selected one.
        A case that survived those three versions would have been pinning my prose.

        SO THE CONTRACT IS THE PROPERTY NOW: a control that cannot be used here is refused,
        the refusal names the database the caller must open for themselves, and nothing is
        answered from a journal nobody could prove.
        """
        database = self.store.database
        self.store._connection.close()
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.assignment_workspace(self.group, self.storage, "assignment-4",
                                            control=self.store)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        self.assertIn("cannot be used from this thread", caught.exception.message)
        self.assertIn(database, caught.exception.message)
        # NOTHING WAS CREATED for the attempt it could not ask about.
        self.assertFalse(os.path.exists(os.path.join(self.storage, "assignment-4")))

    def test_a_usable_control_on_this_thread_is_answered_normally(self):
        """THE OTHER HALF, so the contract is not just a way of refusing everything.

        A handle opened HERE is its own authority -- no claim about another handle's journal
        is involved -- so it answers, and the standing cleanup recorded through it is what
        refuses the allocation rather than the contract above.
        """
        from baton_v12.worker_manager.store import ControlStore

        self.attempt_roots("assignment-5")
        self.admitted("assignment-5")
        mine = ControlStore.open(os.path.join(self.root, "control.sqlite3"),
                                 incarnation="workspaces-1",
                                 clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(mine.close)
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.assignment_workspace(self.group, self.storage, "assignment-5",
                                            control=mine)
        self.assertIn("has recorded no settlement", caught.exception.message)

    def test_an_adoption_released_on_cessation_stops_blocking_the_attempt(self):
        """CESSATION RELEASES, and a caller that stops without handing over must say so.

        An adoption opens an exclusion so nothing removes or reallocates these roots while
        they are proved and used. A caller that hands them to a lifecycle grant passes that
        window on; a caller that simply STOPS has to end it, or the attempt is blocked by an
        adoption with nobody behind it. Measured here at the mechanism: while the adoption
        stands the removal is refused, and after the release it proceeds.
        """
        self.attempt_roots("assignment-8")
        roots = workspaces.adopted_assignment_workspace(
            self.storage, "assignment-8", control=self.store)
        self.assertEqual(len(workspaces.standing_adoption(self.store, "assignment-8")), 1)
        with self.assertRaises(ContractRefusal) as caught:
            discard_workspace(self.storage, "assignment-8", control=self.store)
        self.assertIn("adoption 1 of this attempt", caught.exception.message)
        workspaces.release_adopted_workspace(roots)
        self.assertEqual(workspaces.standing_adoption(self.store, "assignment-8"), [])
        self.assertTrue(discard_workspace(self.storage, "assignment-8",
                                         control=self.store))

    def test_a_failure_after_adopting_does_not_leave_the_window_standing(self):
        """FAILURE AND INTERRUPT RELEASE TOO, which is what a `finally` is for.

        The window has to end on the paths nobody plans: a refusal from a later check, an
        interrupt, an exception inside a composition. This stages the shape the real callers
        have -- adopt, then fail -- and asserts that the release in their `finally` leaves no
        standing adoption and no blocked attempt behind it.
        """
        self.attempt_roots("assignment-9")

        def using():
            roots = workspaces.adopted_assignment_workspace(
                self.storage, "assignment-9", control=self.store)
            try:
                raise RuntimeError("the caller failed after adopting")
            finally:
                workspaces.release_adopted_workspace(roots)

        with self.assertRaisesRegex(RuntimeError, "failed after adopting"):
            using()
        self.assertEqual(workspaces.standing_adoption(self.store, "assignment-9"), [])
        # AND THE ATTEMPT IS NOT BLOCKED BY WHAT THE FAILED CALLER TOOK.
        self.assertTrue(discard_workspace(self.storage, "assignment-9",
                                         control=self.store))

    def test_a_release_that_fails_leaves_the_window_for_the_retry(self):
        """AND AN INTERRUPTED RELEASE KEEPS THE WINDOW, so a retry can still end it.

        Review 2026-09-26T07:58:05Z: clearing the token first meant a failed settle left the
        window standing with nobody holding a way to end it -- an orphan by construction. So
        the token is cleared only after the settlement commits, and this is that rule as a
        case: a failed release leaves BOTH the standing adoption and the caller's handle, and
        the retry succeeds.
        """
        self.attempt_roots("assignment-10")
        roots = workspaces.adopted_assignment_workspace(
            self.storage, "assignment-10", control=self.store)
        honest = workspaces._settled_adoption
        workspaces._settled_adoption = lambda *a, **k: (_ for _ in ()).throw(
            RuntimeError("the settlement was interrupted"))
        self.addCleanup(setattr, workspaces, "_settled_adoption", honest)
        with self.assertRaisesRegex(RuntimeError, "settlement was interrupted"):
            workspaces.release_adopted_workspace(roots)
        self.assertEqual(len(workspaces.standing_adoption(self.store, "assignment-10")), 1)
        self.assertIsNotNone(getattr(roots, "_adoption", None))
        workspaces._settled_adoption = honest
        workspaces.release_adopted_workspace(roots)
        self.assertEqual(workspaces.standing_adoption(self.store, "assignment-10"), [])

    def test_the_settlement_ends_the_exclusion_and_only_for_its_owner(self):
        """AND THE EXCLUSION ENDS EXACTLY WHEN THE ENDING COMMITS.

        `settle_cleanup` writes inside the caller's open transaction -- pure database work
        -- so the record closing the window is in the same commit as the ending. Here the
        transaction is taken by hand, which is what the ending does to it.
        """
        self.attempt_roots()
        admitted = self.admitted()
        connection = self.store._connection
        connection.execute("BEGIN IMMEDIATE")
        try:
            workspaces.settle_cleanup(self.store, connection, "assignment-1",
                                      admitted, "cleaning up")
            connection.execute("COMMIT")
        except BaseException:
            connection.execute("ROLLBACK")
            raise
        self.assertEqual(workspaces.standing_cleanup(self.store, "assignment-1"), [])
        # ALLOCATION IS POSSIBLE AGAIN, which is the other half of the property: this is
        # an exclusion with an end, not a permanent block.
        self.assertTrue(workspaces.assignment_workspace(
            self.group, self.storage, "assignment-1"))
        # A SETTLEMENT FOR AN ADMISSION THIS ACT DOES NOT OWN IS REFUSED.
        second = self.admitted(operation="runtime.destroy:second")
        connection.execute("BEGIN IMMEDIATE")
        try:
            with self.assertRaises(ContractRefusal) as caught:
                workspaces.settle_cleanup(
                    self.store, connection, "assignment-1",
                    dict(second, owner="somebody-elses-owner"), "cleaning up")
        finally:
            connection.execute("ROLLBACK")
        self.assertEqual(caught.exception.code, "identity-mismatch")

    def test_the_exclusion_answers_from_a_thread_that_does_not_own_the_store(self):
        """THE QUESTION IS ASKED ON EVERY THREAD, not only the store's own.

        Allocation is accepted as safe to call concurrently -- `test_workspaces`
        allocates 24 assignments across eight threads -- and a SQLite connection belongs
        to the thread that opened it. Measured while building this: asking through the
        bound handle from another thread raises `ProgrammingError`, and a protection that
        switches off there is the "off by default" failure `refuse_if_held` names. So a
        short-lived handle on the SAME database file answers instead, and this proves it
        answers the same way.
        """
        self.attempt_roots()
        self.admitted()
        outcome = []

        def beside():
            try:
                workspaces.assignment_workspace(self.group, self.storage,
                                                "assignment-1")
                outcome.append(("allowed", None))
            except ContractRefusal as refused:
                outcome.append(("refused", refused.message))
            except BaseException as failure:            # reported, never swallowed
                outcome.append((type(failure).__name__, str(failure)))

        worker = threading.Thread(target=beside)
        worker.start()
        worker.join(10)
        self.assertEqual(len(outcome), 1, "the other thread must answer")
        self.assertEqual(outcome[0][0], "refused", outcome[0])
        # OFF-THREAD IS A REFUSAL NOW, NOT AN ANSWER FROM A REOPENED JOURNAL. The property
        # this case exists for is unchanged and is the important one: the other thread does
        # NOT allocate. What changed is why -- three attempts to prove a reopened handle was
        # the selected journal were each defeated, so the caller is told to bring a handle it
        # can use rather than being served from one nobody could attribute.
        self.assertIn("cannot be used from this thread", outcome[0][1])

    # -- the token baton, bound to the running container -----------------------

    def a_token(self, assignment_id="assignment-t", seconds=900):
        """Acquire the baton the way the removal boundary does."""
        return workspaces._admitted_removal(
            self.store, assignment_id, "removing this attempt's execution roots",
            None, None, "execution-1", seconds)

    def test_an_outstanding_token_refuses_a_competing_caller(self):
        """THE CONTRACT'S CENTRE: no second caller acquires while a baton is outstanding.

        Owner ruling OWNER-TOKEN-BATON-20260926.md: "another thread cannot acquire
        conflicting ownership until the outstanding baton is returned safely". Acquisition is
        one short transaction that decides eligibility, replay and ownership together, and the
        refusal names the generation and execution holding it rather than just saying no.
        """
        self.attempt_roots("assignment-t")
        owned = self.a_token()
        token = workspaces.token_of(self.store, "assignment-t", owned["ordinal"])
        self.assertEqual(token["generation"], owned["ordinal"])
        self.assertEqual(token["execution"], "execution-1")
        self.assertFalse(token["expired"])
        self.assertIsNone(token["container"], "no container exists at reservation")
        with self.assertRaises(ContractRefusal) as caught:
            self.a_token()
        self.assertIn("outstanding token", caught.exception.message)
        self.assertIn("execution-1", caught.exception.message)

    def test_the_container_is_bound_after_the_reservation_and_only_by_its_owner(self):
        """RESERVE BEFORE LAUNCH IS PRESERVED, which the owner named explicitly.

        "Do not assume a container ID exists at initial reservation." The baton is acquired
        first -- excluding everyone else while there is nothing yet to stop -- and the eventual
        container is bound to THAT exact generation afterwards. A stale holder cannot bind,
        because binding decides which running object an expiry will be allowed to kill.
        """
        self.attempt_roots("assignment-t")
        owned = self.a_token()
        workspaces.bind_token_container(self.store, "assignment-t", owned["ordinal"],
                                        owned, "container-abc")
        token = workspaces.token_of(self.store, "assignment-t", owned["ordinal"])
        self.assertEqual(token["container"], "container-abc")
        impostor = dict(owned, owner="somebody-elses-owner")
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.bind_token_container(self.store, "assignment-t", owned["ordinal"],
                                            impostor, "container-xyz")
        # MEASURED: the refusal arrives as `operation-collision` rather than from my own
        # owner check, because the binding is one journalled act per token and a second one
        # naming a different owner and container collides at that identity before the
        # callback runs. That is the journal enforcing the same rule one layer earlier, so
        # the assertion is on the refusal and on the binding being UNCHANGED -- the property
        # -- rather than on whichever guard got there first.
        self.assertIn(caught.exception.code, ("operation-collision", "identity-mismatch"))
        self.assertEqual(
            workspaces.token_of(self.store, "assignment-t",
                                owned["ordinal"])["container"], "container-abc")

    def test_an_expired_token_holds_the_roots_until_cessation_is_confirmed(self):
        """EXPIRY BEGINS REVOCATION AND IS NOT PERMISSION TO REPLACE.

        The owner's Docker clarification is the sequence this asserts: the token expires, the
        exact bound container is shut down, its termination is POSITIVELY CONFIRMED, and only
        then may a new generation be admitted. Between expiry and that confirmation the roots
        are held -- so an expired token refuses a replacement exactly as a live one does, with
        its own sentence.
        """
        self.attempt_roots("assignment-t")
        owned = self.a_token(seconds=1)
        workspaces.bind_token_container(self.store, "assignment-t", owned["ordinal"],
                                        owned, "container-abc")
        # THE CLOCK IS THE FIXTURE'S, not a sleep: the store's own instant source is what
        # both the journal and the expiry read, so moving it is the honest way to reach the
        # expired state deterministically.
        self.store._clock = lambda: "2026-08-24T01:00:00.000Z"
        token = workspaces.token_of(self.store, "assignment-t", owned["ordinal"])
        self.assertTrue(token["expired"])
        with self.assertRaises(ContractRefusal) as caught:
            self.a_token()
        self.assertIn("EXPIRED", caught.exception.message)
        self.assertIn("cessation is not established", caught.exception.message)
        self.assertIn("container-abc", caught.exception.message)

    def test_an_unknown_stop_or_a_surviving_helper_keeps_the_roots_held(self):
        """A STOP REQUEST IS NOT CESSATION, which is the owner's own distinction.

        The controlled boundary answers what it established. Anything short of "that exact
        container is gone and no writable helper survives" records NO cessation, so the roots
        stay held and a new generation stays refused. Both shortfalls are asked separately,
        because a surviving helper is exactly the case a container-only check would miss.
        """
        self.attempt_roots("assignment-t")
        owned = self.a_token(seconds=1)
        workspaces.bind_token_container(self.store, "assignment-t", owned["ordinal"],
                                        owned, "container-abc")
        self.store._clock = lambda: "2026-08-24T01:00:00.000Z"
        asked = []

        def unknown(container):
            asked.append(container)
            return {"stopped": False, "helpers": []}

        def surviving(container):
            asked.append(container)
            return {"stopped": True, "helpers": ["writer-1"]}

        for what, stop in (("an unknown stop", unknown),
                           ("a surviving helper", surviving)):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    workspaces.revoke_expired_token(self.store, "assignment-t",
                                                    owned["ordinal"], stop)
                self.assertEqual(caught.exception.code, "quiescence-unknown")
                self.assertIn("a stop request is not cessation", caught.exception.message)
        self.assertEqual(asked, ["container-abc", "container-abc"],
                         "the EXACT bound container is what the boundary was asked about")
        # AND THE REVOCATION IS RECORDED EVEN THOUGH CESSATION IS NOT, so no replacement can
        # slip in while an operator reconciles.
        token = workspaces.token_of(self.store, "assignment-t", owned["ordinal"])
        self.assertTrue(token["revoked"])
        self.assertFalse(token["ceased"])
        with self.assertRaises(ContractRefusal):
            self.a_token()

    def test_confirmed_cessation_permits_the_next_generation(self):
        """AND THEN, AND ONLY THEN, A NEW BATON, with the generation moving on.

        The positive answer -- that exact container gone, no writable helper surviving --
        records the cessation, and the next acquisition succeeds as generation 2. Without this
        half the contract would be a way of deadlocking an attempt rather than a way of
        recovering it.
        """
        self.attempt_roots("assignment-t")
        owned = self.a_token(seconds=1)
        workspaces.bind_token_container(self.store, "assignment-t", owned["ordinal"],
                                        owned, "container-abc")
        self.store._clock = lambda: "2026-08-24T01:00:00.000Z"
        stopped = workspaces.revoke_expired_token(
            self.store, "assignment-t", owned["ordinal"],
            lambda container: {"stopped": True, "helpers": []})
        self.assertTrue(stopped["ceased"])
        self.assertTrue(stopped["revoked"])
        second = self.a_token()
        self.assertEqual(second["ordinal"], owned["ordinal"] + 1)
        self.assertEqual(
            workspaces.token_of(self.store, "assignment-t", second["ordinal"])["generation"],
            owned["ordinal"] + 1)

    def test_the_revocation_does_no_external_work_under_a_database_lock(self):
        """F2'S OWN RULE, APPLIED TO THE NEW MACHINERY: stop and confirm outside every lock.

        The owner is explicit that "Stop/confirmation/reset I/O occurs outside DB
        transactions". The boundary records whether a transaction was open at the moment it
        was called, which is the same way this selector asks every other question.
        """
        self.attempt_roots("assignment-t")
        owned = self.a_token(seconds=1)
        workspaces.bind_token_container(self.store, "assignment-t", owned["ordinal"],
                                        owned, "container-abc")
        self.store._clock = lambda: "2026-08-24T01:00:00.000Z"
        observed = []

        def stopping(container):
            observed.append(self.store._connection.in_transaction)
            return {"stopped": True, "helpers": []}

        workspaces.revoke_expired_token(self.store, "assignment-t", owned["ordinal"],
                                        stopping)
        self.assertEqual(observed, [False],
                         "the container stop ran while a database lock was held")

    # -- the prepared store, rebound under the lock ---------------------------

    def another_configured_store(self, name="beside"):
        """A SECOND disposable deployment, configured at a different place.

        The only honest way to hold a prepared store that this database does not
        record: `WorkspaceStorage` is mintable only by
        `configured_workspace_storage`, so a stale one has to come from a
        manager that really did configure that directory. Both live inside this
        fixture's own temporary tree.
        """
        import tempfile

        from baton_v12.worker_manager.store import ControlStore

        place = os.path.join(self.root, name)
        os.makedirs(place)
        beside = ControlStore.open(
            os.path.join(self.root, f"{name}.sqlite3"),
            incarnation=f"workspaces-{name}",
            clock=lambda: "2026-09-26T00:00:00.000Z")
        self.addCleanup(beside.close)
        workspaces.configure_workspace_storage(beside, place)
        return workspaces.configured_workspace_storage(beside), place

    def test_a_prepared_store_this_database_does_not_record_is_refused(self):
        """THE OPERAND IS REBOUND, NOT BELIEVED, which is what makes hoisting the
        `lstat` out of the ending safe.

        Review 2026-09-26T08:43:12Z: "A merely passed mutable dictionary with no
        provenance binding is not completion." The physical validation now happens
        before the cleanup's transaction opens, so the reader INSIDE the
        transaction has to prove the evidence still describes this deployment --
        otherwise a place measured elsewhere, or measured before a
        reconfiguration, would be signed for as if this manager had validated it.
        A store minted by a DIFFERENT configured manager is exactly that case.
        """
        foreign, place = self.another_configured_store()
        self.assertNotEqual(place, self.storage)
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.recorded_storage_place(self.store, foreign)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("makes the prepared evidence stale", caught.exception.message)
        # AND THE AGREEING CASE STILL ANSWERS, so the refusal above is about the
        # disagreement rather than about the reader being broken.
        self.assertEqual(
            workspaces.recorded_storage_place(
                self.store, workspaces.configured_workspace_storage(self.store)),
            self.storage)

    def test_a_place_a_caller_composed_is_not_prepared_evidence(self):
        """`WorkspaceStorage`'S WHOLE RULE SURVIVES THE MOVE.

        W36540's reason for the frozen store is that a path is a value any caller
        can compose. Moving where the `lstat` happens must not turn the operand
        into a string, so the plain path -- even the RIGHT one -- is refused.
        """
        for operand in (self.storage, {"place": self.storage}, None):
            with self.subTest(operand=operand):
                with self.assertRaises(ContractRefusal) as caught:
                    workspaces.recorded_storage_place(self.store, operand)
                self.assertEqual(caught.exception.code, "schema")
                self.assertIn("frozen answer", caught.exception.message)

    def test_the_rebinding_reader_asks_the_filesystem_nothing(self):
        """THE POINT OF THE SPLIT, asked at the syscalls rather than inferred.

        `configured_workspace_storage` measures three times -- the projection, the
        committed answer, and again when the store is minted -- and the reviewer's
        trace pinned all six of the ending's locked calls to exactly that, twice.
        This asserts the corrected reader's cost directly: zero filesystem calls,
        while the accepted outside reader still makes them.
        """
        prepared = workspaces.configured_workspace_storage(self.store)
        watcher = AnOpenTransaction(self.store._connection)
        with watcher:
            self.assertEqual(
                workspaces.recorded_storage_place(self.store, prepared),
                self.storage)
        self.assertEqual(watcher.observed, [],
                         "the reader that runs under a lock asks the disk nothing")
        with watcher:
            workspaces.configured_workspace_storage(self.store)
        self.assertTrue(watcher.observed,
                        "the outside reader is unchanged and still measures")


class TheCleanupExclusionEnds(IntakeCase):
    """THE REAL CLEANUP PATH, because a mutation proved the rest of this file could not see it.

    MEASURED, NOT ANTICIPATED: deleting `settle_cleanup`'s call from `intake._settle`
    broke NOTHING -- 229 cases passed with the exclusion never being closed at all. Every
    case above either settles by hand or only cares that the window is shut, so the whole
    selector was blind to a cleanup that takes an exclusion and keeps it forever. That is
    a worse failure than the gap this Work is closing: it is a permanent one.

    The intake fixture is used exactly as `tests.manager.test_intake` and the reviewer's
    own probes use it -- disposable store, this fixture's own directories, no live engine
    or provider and no process created or signalled.
    """

    def prepared(self):
        self.retained_ready("discard-after-intake")
        self.ended()
        storage = workspaces.configured_workspace_storage(self.store).place
        workspaces.assignment_workspace(
            workspaces.configured_workspace_group(self.store), storage, ATTEMPT)
        return storage

    def test_a_settled_cleanup_leaves_no_standing_exclusion(self):
        storage = self.prepared()
        answer = intake.authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION)
        self.assertIn(answer["cleanup"], ("complete", "retained"))
        # THE WINDOW IS SHUT AND IT IS ALSO OVER. An exclusion with no end would refuse
        # this attempt's roots for the rest of the deployment's life.
        self.assertEqual(workspaces.standing_cleanup(self.store, ATTEMPT), [])
        self.assertIsNotNone(self.store.operation_record(
            workspaces._cleanup_settled_id(ATTEMPT, 1)))
        # AND THE ROOTS ARE ALLOCATABLE AGAIN, which is the observable form of that.
        self.assertTrue(workspaces.assignment_workspace(
            workspaces.configured_workspace_group(self.store), storage, ATTEMPT))


if __name__ == "__main__":
    unittest.main()
