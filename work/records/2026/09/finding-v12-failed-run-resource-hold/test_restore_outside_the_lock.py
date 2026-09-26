"""W257624: an abandoned correction is restored with no lock held over I/O.

Owner reroute 270482 selects this bounded correction and the pinned selection,
exact file ownership and shape are in this dossier's FINDING and PLAN entries
dated 2026-09-26. `restore_abandoned_correction` used to call
`_validate_line_object` and then `profile.restore_checkpoint` -- a whole checkout
restoration -- inside `store.transact`, and its own comments said the write lock
was deliberately held across it. The 2026-09-26T01:04:01Z ruling withdraws that.

THE CORRECTED SHAPE, and the three things this module has to establish about it:
the intent transaction takes the exclusion by revoking the writer; the
restoration happens outside every transaction; and the completion re-proves the
exclusion and releases the line in one short database-only act.

WHAT IS REAL: a real `ControlStore` on a disposable temporary root, real
directories, a real line through `create_line`, real `grant_writer`,
`freeze_checkpoint`, `attach_review` and `record_verdict`, the real
`abandon_attempt` and `discharge_abandoned_quiescence_gate`, the real
`restore_abandoned_correction`, and a real second connection for the contention
and the unrelated-progress cases.

WHAT IS CONTROLLED AND DETERMINISTIC, named as the standing constraints require:
the checkpoint profile, the authority port and the custodian are this
repository's accepted `tests.manager.test_review_cycles` fixtures, and this
module installs a barrier inside the profile's `restore_checkpoint` so a case can
hold a restoration open at the exact moment the old shape held the write lock. No
live provider, engine, daemon, network or deployed store is reached.

ONE FIXTURE DETAIL MEASURED RATHER THAN COPIED. The accepted restore fixture
attaches its runtime by setting `execution_runtime = 'running'`, and stage 2's
reservation rule now refuses an abandonment there -- "start submission has not
returned to the manager that made it" -- which is the disclosed baseline behind
36 errors in that suite. This module therefore leaves the axis at `not-started`
and attaches only the runtime identity, which is the state
`attempts.start_submission_returned` answers True for, so the real
`abandon_attempt` commits. Nothing here works around stage 2: an attempt that
never submitted has nothing outstanding, which is that reader's own rule.

WHAT THIS DOES NOT CLAIM: no global no-I/O-under-lock coverage for any other call
site, no R3/R4/R5 evidence, and no adoption claim. The residual the corrected
shape does not close -- a second restorer whose write lands after this completion
and after a successor began writing -- is recorded in PLAN.md and is NOT asserted
away here.
"""
import os
import sqlite3
import threading
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (ControlStore, abandon_attempt,
                                      attach_review, create_line,
                                      discharge_abandoned_quiescence_gate,
                                      freeze_checkpoint, grant_writer, line_of,
                                      record_verdict, writer_of)
from baton_v12.worker_manager import review_cycles
from baton_v12.worker_manager.review_cycles import (
    RESTORE_KIND, abandoned_correction_of, restore_abandoned_correction)
from baton_v12.worker_manager.source_boundary import nominate_source
from baton_v12.worker_manager.workspaces import configure_workspace_storage

from tests.manager import input_roots
from tests.manager.disk_roots import disk_backed_under
from tests.manager.test_review_cycles import (AUTHORITY, BASE, NOW, WORK,
                                              AbandoningPort, Custodian, Port,
                                              Profile)

RETENTION = "sha256:" + "7" * 64
ABANDONED = "writer-attempt-2"
REASON = "the correction worker stopped answering and is declared abandoned"

# Every rendezvous and join in this module is bounded, so a schedule that does
# not happen fails the case instead of hanging the run. The join bound is the
# larger, so an impossible rendezvous breaks first and reports itself.
WAIT = 5
JOIN = WAIT * 3

# The operating-system calls a restoration can reach. sqlite's own I/O is in C
# and deliberately invisible here: the ruling exempts the database's own I/O, so
# a probe that saw it would be measuring the wrong thing.
OBSERVED = ("stat", "lstat", "getgroups", "getgid", "access", "scandir",
            "listdir", "chmod", "chown", "rename", "mkdir", "unlink", "rmdir")
OBSERVED_PATH = ("realpath", "islink", "isdir", "exists")


class AnOpenTransaction:
    """Record, at every observed OS call, whether a transaction was open.

    `sqlite3.Connection.in_transaction` is true from an explicit `BEGIN` until
    the matching `COMMIT` or `ROLLBACK`, and `ControlStore` opens with
    `isolation_level=None` and issues `BEGIN IMMEDIATE` itself -- so this is the
    real lock state rather than a fixture's idea of it. `ControlStore.snapshot`
    already reads the same attribute.
    """

    def __init__(self, connection):
        self.connection = connection
        self.calls = []

    @property
    def under_lock(self):
        return [name for name, held in self.calls if held]

    def _wrap(self, name, original):
        def observing(*operands, **named):
            self.calls.append((name, self.connection.in_transaction))
            return original(*operands, **named)

        return observing

    def __enter__(self):
        self._stack = []
        for owner, names in ((os, OBSERVED), (os.path, OBSERVED_PATH)):
            for name in names:
                patch = mock.patch.object(
                    owner, name, self._wrap(name, getattr(owner, name)))
                patch.start()
                self._stack.append(patch)
        return self

    def __exit__(self, *failure):
        for patch in reversed(self._stack):
            patch.stop()
        return False


class RestoreOutsideTheLock(unittest.TestCase):
    """Real store, real directories, accepted profile/port/custodian fixtures."""

    def setUp(self):
        import tempfile

        self.temporary = tempfile.TemporaryDirectory(prefix="v12-restore-")
        self.addCleanup(self.temporary.cleanup)
        self.source = os.path.join(self.temporary.name, "source")
        os.mkdir(self.source)
        self.storage = os.path.join(disk_backed_under(self), "storage")
        os.makedirs(self.storage, exist_ok=True)
        self.control_path = os.path.join(self.temporary.name, "control.sqlite3")
        self.store = ControlStore.open(self.control_path,
                                       incarnation="manager-1",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)
        self.profile = Profile()
        self.group = input_roots.configured_group(self.store)
        configure_workspace_storage(self.store, self.storage)
        self.ports = {}

    # -- the accepted fixtures' own composition, spelled here -----------------

    def port(self, participant):
        return self.ports.setdefault(participant, Port(participant))

    def attempt(self, attempt_id, generation, participant, principal):
        """One attempt row a delivery would have written.

        The accepted `ReviewCycles.attempt` shortcut, spelled rather than
        inherited: inheriting that class would re-run its own accepted cases and
        count them as this correction's evidence.
        """
        self.store._connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, created_at, work_id, "
            "authority_uuid, assignment_participant, assignment_generation, "
            "assignment_claim_event_seq, assignment_principal, "
            "assignment_scope, assignment_role, assignment_grant, "
            "assignment_policy_generation) VALUES (?, 'adapter', "
            "'adapter-digest', 'profile-digest', ?, ?, ?, ?, ?, ?, ?, 'scope', "
            "'role', 'grant', 1)",
            (attempt_id, NOW, WORK, AUTHORITY, participant, generation,
             generation, principal))
        return attempt_id

    def completed(self, attempt_id, *, review=False):
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = "
            "'quiescent', worker_disposition = 'completed' "
            "WHERE runtime_attempt_id = ?", ("runtime-" + attempt_id,
                                             attempt_id))
        if not review:
            return
        self.store._connection.execute(
            "UPDATE attempts SET output = 'frozen', verification = 'passed' "
            "WHERE runtime_attempt_id = ?", (attempt_id,))
        self.store._connection.execute(
            "INSERT INTO outputs (runtime_attempt_id, result_id, disposition, "
            "manifest_digest, freeze_operation_id, frozen_at) VALUES (?, ?, "
            "'completed', ?, ?, ?)",
            (attempt_id, "result-" + attempt_id, "sha256:" + "1" * 64,
             "freeze-" + attempt_id, NOW))
        for name, filler in (("findings", "2"), ("logs", "3")):
            self.store._connection.execute(
                "INSERT INTO output_artifacts (runtime_attempt_id, "
                "output_name, artifact_id, media_type, bytes, content_digest, "
                "locator) VALUES (?, ?, ?, 'text/plain', 1, ?, ?)",
                (attempt_id, name, f"artifact-{name}-{attempt_id}",
                 "sha256:" + filler * 64, f"custody/{attempt_id}/{name}"))

    def granted(self, line_id, round_number, based=None):
        attempt = self.attempt(f"writer-attempt-{round_number}", round_number,
                               "baton.impl", f"writer-{round_number}")
        return grant_writer(self.store, line_id=line_id, attempt_id=attempt,
                            generation=round_number,
                            worker_id=f"worker-{round_number}",
                            profile=self.profile, based_checkpoint_id=based)

    def abandoned(self, *, discharge=True):
        """One line whose SECOND writer is really abandoned and discharged.

        Round one is composed through the real grant, freeze, attach and verdict;
        the correction writer is then granted and its attempt really abandoned
        through `abandon_attempt` with its gate really discharged. What is left is
        the state this recovery exists for: the line still `writing`, its
        correction writer still `active`, and nothing able to admit a successor.
        """
        line = create_line(self.store, source=nominate_source(self.source),
                           declared_base=BASE, profile=self.profile,
                           authority_uuid=AUTHORITY, work_id=WORK)
        first = self.granted(line["line_id"], 1)
        self.completed("writer-attempt-1")
        checkpoint = freeze_checkpoint(
            self.store, writer_id=first["writer_id"], generation=1,
            profile=self.profile, port=self.port("baton.impl"))
        reviewer = self.attempt("review-attempt-1", 1, "baton.review",
                                "reviewer-1")
        attached = attach_review(
            self.store, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id=reviewer, generation=1,
            reviewer_worker_id="review-worker-1", profile=self.profile)
        self.completed("review-attempt-1", review=True)
        record_verdict(self.store, attachment_id=attached["attachment_id"],
                       disposition="changes-requested", profile=self.profile,
                       port=self.port("baton.review"))
        writer = self.granted(line["line_id"], 2,
                              based=checkpoint["checkpoint_id"])
        # THE RUNTIME IDENTITY ONLY, with the axis left `not-started`: see the
        # module docstring. That is the state stage 2's own reader answers True
        # for, so the real abandonment commits.
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ? WHERE runtime_attempt_id = ?",
            ("runtime-" + ABANDONED, ABANDONED))
        self.custodian = Custodian()
        self.abandon_port = AbandoningPort("baton.impl",
                                           authority_uuid=AUTHORITY,
                                           work_id=WORK)
        abandon_attempt(self.store, self.abandon_port, self.custodian,
                        attempt_id=ABANDONED, reason=REASON,
                        retention_policy_digest=RETENTION)
        if discharge:
            discharge_abandoned_quiescence_gate(
                self.store, self.abandon_port, attempt_id=ABANDONED,
                retention_policy_digest=RETENTION)
        self.line_id = line["line_id"]
        self.line_path = line["path"]
        self.checkpoint = checkpoint
        self.writer_row = writer
        return writer

    def restore(self, store=None, **overrides):
        operands = {"attempt_id": ABANDONED, "generation": 2,
                    "retention_policy_digest": RETENTION,
                    "profile": self.profile}
        operands.update(overrides)
        return restore_abandoned_correction(self.store if store is None
                                            else store, **operands)

    def line_row(self):
        return line_of(self.store, self.line_id)

    def writers(self):
        """Every writer row, read from a connection this case does not own."""
        beside = sqlite3.connect(self.control_path, isolation_level=None)
        try:
            return {one[0]: one[1] for one in beside.execute(
                "SELECT writer_id, state FROM line_writers")}
        finally:
            beside.close()

    def holding(self, arrived, release, holder=None):
        """A profile whose restoration BLOCKS where the old shape held the lock.

        `arrived` is set once the restoration is inside the profile; the profile
        then waits for `release`. Every wait is bounded. This is the controlled
        boundary the owner's schedule cases need and it is the only thing about
        the restoration that is not the accepted profile's own behaviour.

        `holder` names WHICH handle to read the lock state from, because sqlite
        forbids using a connection from a thread that did not create it -- and a
        threaded case's restoration runs on its own handle. Measured, not
        assumed: reading `self.store` from the worker thread raised
        `ProgrammingError`.
        """
        honest = self.profile.restore_checkpoint
        seen = []

        def waiting(repository, evidence):
            store = self.store if holder is None else holder["store"]
            seen.append(store._connection.in_transaction)
            arrived.set()
            if not release.wait(WAIT):
                raise AssertionError("the restoration was never released")
            return honest(repository, evidence)

        self.profile.restore_checkpoint = waiting
        return seen

    def restoring_thread(self, answers, arrived, holder):
        """One restoration on ITS OWN handle, with failures carried back.

        The handle is opened inside the thread because sqlite objects belong to
        the thread that created them, and it is closed there too so cleanup
        precedes fixture teardown.
        """
        def restoring():
            # THE SAME INCARNATION AS THE FIXTURE, because this thread IS the
            # executor. Review 2026-09-26T01:49:21Z [P1]: the executor of a
            # restoration is the incarnation that committed its intent, so a
            # handle opened under another name is held rather than admitted --
            # which is the point of these cases, not an obstacle to them.
            beside = ControlStore.open(self.control_path,
                                       incarnation="manager-1",
                                       clock=lambda: NOW)
            holder["store"] = beside
            try:
                answers["restore"] = self.restore(store=beside)
            except BaseException as failure:            # noqa: BLE001
                answers["restore"] = failure
                arrived.set()
            finally:
                beside.close()

        return threading.Thread(target=restoring)

    # -- the ordering, which is what the correction is about ------------------

    def test_no_filesystem_call_happens_while_the_restore_holds_the_lock(self):
        """THE WHOLE RECOVERY, measured call by call.

        This is the property the correction exists for. A clean report from a
        probe that never fires proves nothing, so the case also requires that
        real calls were observed -- and a restoration necessarily makes them,
        because it validates an object and rewrites a checkout.
        """
        writer = self.abandoned()
        self.assertEqual(self.line_row()["state"], "writing")
        self.assertEqual(writer_of(self.store,
                                   writer["writer_id"])["state"], "active")

        with AnOpenTransaction(self.store._connection) as observing:
            answered = self.restore()

        self.assertTrue(observing.calls, "the probe observed no OS calls at all")
        self.assertEqual(observing.under_lock, [])
        # AND THE RECOVERY REALLY COMPLETED, so the empty list is the absence of
        # I/O under a lock rather than the absence of a recovery.
        self.assertEqual(answered["state"], "correction-ready")
        self.assertEqual(answered["writer_id"], writer["writer_id"])
        self.assertEqual(answered["checkpoint_id"],
                         self.checkpoint["checkpoint_id"])

    def test_the_restoration_itself_runs_outside_every_transaction(self):
        """AND THE PROFILE CALL SPECIFICALLY, asked at the moment it happens.

        The probe above cannot distinguish "no filesystem call under a lock" from
        "the profile was never asked", so the profile records the lock state
        itself. This is the exact statement the superseded comment denied: it
        said the write lock is held across the restoration.
        """
        self.abandoned()
        arrived, release = threading.Event(), threading.Event()
        release.set()
        seen = self.holding(arrived, release)
        self.restore()
        self.assertEqual(seen, [False])
        self.assertTrue(arrived.is_set())

    def test_unrelated_database_progress_continues_while_a_restore_is_paused(self):
        """THE PROPERTY THE OLD LOCK DESTROYED, and the reason for this change.

        A second real handle commits an unrelated manager act WHILE a restoration
        is open inside the profile. Under the superseded shape the write lock was
        held across the checkout, so this act would have blocked for the length of
        the restoration; here it commits immediately and the restoration then
        finishes normally.
        """
        self.abandoned()
        arrived, release = threading.Event(), threading.Event()
        holder, answers = {}, {}
        seen = self.holding(arrived, release, holder)
        thread = self.restoring_thread(answers, arrived, holder)
        thread.start()
        try:
            self.assertTrue(arrived.wait(WAIT),
                            "the restoration never reached the profile")
            # THE UNRELATED ACT, on its own handle, committed while the
            # restoration is open. A second line for another Work is chosen
            # deliberately: it shares no row with the one being restored.
            beside = ControlStore.open(self.control_path,
                                       incarnation="manager-2",
                                       clock=lambda: NOW)
            try:
                other = create_line(
                    beside, source=nominate_source(self.source),
                    declared_base=BASE, profile=self.profile,
                    authority_uuid=AUTHORITY, work_id="01234567-W71919")
                self.assertEqual(other["state"], "idle")
            finally:
                beside.close()
        finally:
            release.set()
            thread.join(timeout=JOIN)
        self.assertFalse(thread.is_alive())
        if isinstance(answers["restore"], BaseException):
            raise answers["restore"]
        self.assertEqual(answers["restore"]["state"], "correction-ready")
        self.assertEqual(seen, [False])

    # -- what the correction had to preserve ---------------------------------

    def test_the_intent_revokes_before_the_profile_is_asked(self):
        """THE EXCLUSION IS TAKEN BY THE INTENT, which is what serializes.

        The old shape revoked at completion, inside the same transaction as the
        restoration. The corrected shape revokes in the intent's own short
        transaction, so by the time the profile runs the writer is already gone
        and the line is still `writing` -- nobody holds it and nobody can be
        admitted to it.
        """
        writer = self.abandoned()
        observed = {}
        honest = self.profile.restore_checkpoint

        def watching(repository, evidence):
            observed["writer"] = writer_of(self.store,
                                           writer["writer_id"])["state"]
            observed["reason"] = self.store._connection.execute(
                "SELECT revocation_reason FROM line_writers WHERE writer_id = ?",
                (writer["writer_id"],)).fetchone()[0]
            observed["line"] = self.line_row()["state"]
            return honest(repository, evidence)

        self.profile.restore_checkpoint = watching
        self.restore()
        self.assertEqual(observed,
                         {"writer": "revoked", "reason": "abandoned",
                          "line": "writing"})

    def test_no_successor_is_admitted_while_a_restoration_is_open(self):
        """AND THE LINE IS UNGRANTABLE FOR THE WHOLE WINDOW.

        Successor admission is blocked by existing machinery rather than by
        anything this correction added: the line is left `writing` from the intent
        until the completion, and `grant_writer` admits a writer only from `idle`
        or `correction-ready`. Asked from a SECOND handle, while the restoration is
        really open inside the profile.
        """
        self.abandoned()
        self.attempt("writer-attempt-3", 3, "baton.impl", "writer-3")
        arrived, release = threading.Event(), threading.Event()
        holder, answers = {}, {}
        self.holding(arrived, release, holder)
        thread = self.restoring_thread(answers, arrived, holder)
        thread.start()
        try:
            self.assertTrue(arrived.wait(WAIT))
            beside = ControlStore.open(self.control_path,
                                       incarnation="manager-3",
                                       clock=lambda: NOW)
            try:
                with self.assertRaises(ContractRefusal) as caught:
                    grant_writer(
                        beside, line_id=self.line_id,
                        attempt_id="writer-attempt-3", generation=3,
                        worker_id="worker-3", profile=self.profile,
                        based_checkpoint_id=self.checkpoint["checkpoint_id"])
            finally:
                beside.close()
        finally:
            release.set()
            thread.join(timeout=JOIN)
        self.assertFalse(thread.is_alive())
        if isinstance(answers["restore"], BaseException):
            raise answers["restore"]
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("does not admit a writer", caught.exception.message)
        self.assertIn("writing", caught.exception.message)
        self.assertEqual(self.writers()[self.writer_row["writer_id"]], "revoked")

    def test_a_concurrent_second_caller_produces_one_recovery(self):
        """CONCURRENT CALLS, through two real handles.

        By the effectively-once contract two calls naming one (attempt,
        generation) are ONE act, so what this measures is that they produce one
        committed recovery, one revocation and one released line -- not two
        answers. The rendezvous is placed after each caller has read the line and
        before either commits its intent, which is the window where the old shape
        had no intent-level exclusion at all.
        """
        self.abandoned()
        entered = threading.Barrier(2, timeout=WAIT)
        answers = {}
        failures = []
        honest = review_cycles._abandoned_evidence

        def rendezvous(store, attempt_id, generation, policy, what):
            proved = honest(store, attempt_id, generation, policy, what)
            try:
                entered.wait()
            except threading.BrokenBarrierError:
                raise AssertionError(
                    "both callers did not reach the pre-intent rendezvous"
                ) from None
            return proved

        def caller(name):
            beside = ControlStore.open(self.control_path,
                                       incarnation=f"manager-{name}",
                                       clock=lambda: NOW)
            try:
                answers[name] = self.restore(store=beside)
            except ContractRefusal as refusal:
                answers[name] = refusal
            except BaseException as failure:            # noqa: BLE001
                failures.append(failure)
                entered.abort()
            finally:
                beside.close()

        with mock.patch.object(review_cycles, "_abandoned_evidence",
                               rendezvous):
            threads = [threading.Thread(target=caller, args=("a",)),
                       threading.Thread(target=caller, args=("b",))]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=JOIN)
                self.assertFalse(thread.is_alive())
        if failures:
            raise failures[0]

        # ONE COMMITTED RECOVERY, whatever each caller was answered.
        held = abandoned_correction_of(self.store, attempt_id=ABANDONED,
                                       generation=2)
        self.assertEqual(held["state"], "correction-ready")
        # ONE REVOCATION AND ONE RELEASE -- no second writer row and no second
        # line state change, read beside the store.
        self.assertEqual(self.writers()[self.writer_row["writer_id"]],
                         "revoked")
        self.assertEqual(len(self.writers()), 2)
        self.assertEqual(self.line_row()["state"], "correction-ready")
        # AND EVERY ANSWER IS EITHER THAT RECOVERY OR A REFUSAL -- never a
        # second, differing success document.
        for name, answer in answers.items():
            with self.subTest(caller=name):
                if isinstance(answer, ContractRefusal):
                    # AND THE REFUSAL IS THE EXECUTOR ONE, not any refusal: a
                    # case that accepted any message would pass just as happily
                    # on an unrelated precondition.
                    self.assertIn("is in flight under manager incarnation",
                                  answer.message)
                    continue
                self.assertEqual(answer, held)

    def test_a_second_restorer_is_held_and_the_successor_keeps_its_bytes(self):
        """THE SAFE COUNTERPART to the preserved reviewer reproduction.

        Review 2026-09-26T01:49:21Z [P1] reproduced real successor-byte loss on the
        previous candidate: a second handle adopted the in-flight intent, restored,
        completed and released; a successor was admitted and wrote; the first
        executor returned from its profile and overwrote those bytes; and its
        completing `transact` replayed the foreign completion, so it answered
        success. That probe is preserved unchanged and may now refuse earlier.

        THIS CASE ASSERTS THE OUTCOME instead of the fault. The same schedule is
        driven -- a second caller on another real handle, and a successor grant,
        both attempted WHILE the executor is inside its profile -- and what is
        measured is that there is exactly ONE external crossing, that both
        competing acts are refused, and that the bytes a successor writes AFTER
        the recovery completes are still there at the end.

        THE PROFILE EFFECT IS A LABELLED DETERMINISTIC FILE WRITE standing in for
        a checkout reset, exactly as the reviewer's probe models it. No engine, no
        provider and no version control is involved.
        """
        self.abandoned()
        # THE SUCCESSOR'S ATTEMPT ROW IS MADE ONCE. Measured: creating it inside
        # the profile and again afterwards raised `UNIQUE constraint failed:
        # attempts.runtime_attempt_id` -- one successor asked twice is not two.
        self.attempt("writer-attempt-3", 3, "baton.impl", "writer-3")
        marker = os.path.join(self.line_path, "successor-data.txt")
        with open(marker, "w") as writing:
            writing.write("abandoned scratch")
        crossings = []
        refusals = []
        honest = self.profile.restore_checkpoint
        other = ControlStore.open(self.control_path,
                                  incarnation="second-restorer",
                                  clock=lambda: NOW)
        self.addCleanup(other.close)

        def restoring(repository, evidence):
            crossings.append(repository)
            # A SECOND RESTORER, on another real handle, while this one is in
            # flight. It must be held before it reaches this profile at all.
            with self.assertRaises(ContractRefusal) as caught:
                self.restore(store=other)
            refusals.append(caught.exception)
            # AND A SUCCESSOR CANNOT BE ADMITTED EITHER, because the line is
            # still `writing` until this recovery releases it.
            with self.assertRaises(ContractRefusal) as denied:
                grant_writer(
                    self.store, line_id=self.line_id,
                    attempt_id="writer-attempt-3", generation=3,
                    worker_id="worker-3", profile=self.profile,
                    based_checkpoint_id=self.checkpoint["checkpoint_id"])
            refusals.append(denied.exception)
            answer = honest(repository, evidence)
            # The destructive effect, modelled on real disposable bytes.
            with open(marker, "w") as writing:
                writing.write("restored checkpoint")
            return answer

        self.profile.restore_checkpoint = restoring
        answered = self.restore()

        # EXACTLY ONE EXTERNAL CROSSING.
        self.assertEqual(len(crossings), 1)
        held, denied = refusals
        self.assertEqual((held.category, held.code), ("refused", "precondition"))
        self.assertIn("is in flight under manager incarnation", held.message)
        self.assertIn("stays held rather than being repeated", held.message)
        self.assertIn("does not admit a writer", denied.message)
        # AND THE RECOVERY COMPLETED ONCE, released by its own executor.
        self.assertEqual(answered["state"], "correction-ready")
        self.assertEqual(self.line_row()["state"], "correction-ready")
        # NOW THE SUCCESSOR IS ADMITTED AND ITS BYTES SURVIVE. Nothing is left
        # running that could come back and rewrite this checkout.
        successor = grant_writer(
            self.store, line_id=self.line_id, attempt_id="writer-attempt-3",
            generation=3, worker_id="worker-3", profile=self.profile,
            based_checkpoint_id=self.checkpoint["checkpoint_id"])
        self.assertEqual(successor["state"], "active")
        with open(marker, "w") as writing:
            writing.write("successor work must survive")
        self.assertEqual(len(crossings), 1)
        with open(marker) as reading:
            self.assertEqual(reading.read(), "successor work must survive")

    def overlapping(self, second, *, past_reads=False):
        """Drive the preserved overlap schedule and answer what it produced.

        `second` opens the competing handle, so one helper serves both the
        cross-incarnation and the same-manager cases -- the difference between
        them is only that operand, which is exactly what review
        2026-09-26T02:01:41Z changed to reproduce the defect.

        `past_reads` makes the competing caller complete its own entry proofs
        BEFORE it is refused, so the schedule covers a caller that did not learn
        about the in-flight execution by reading for it.
        """
        marker = os.path.join(self.line_path, "successor-data.txt")
        with open(marker, "w") as writing:
            writing.write("abandoned scratch")
        crossings = []
        refusals = []
        honest = self.profile.restore_checkpoint
        other = second()
        self.addCleanup(other.close)

        def restoring(repository, evidence):
            crossings.append(repository)
            if past_reads:
                # THE COMPETING CALLER'S OWN PROOFS RUN FIRST, so what stops it
                # is the execution boundary and not a read that happened to fail.
                review_cycles._abandoned_evidence(
                    other, ABANDONED, 2, RETENTION, "the competing caller")
            with self.assertRaises(ContractRefusal) as caught:
                self.restore(store=other)
            refusals.append(caught.exception)
            with self.assertRaises(ContractRefusal) as denied:
                grant_writer(
                    self.store, line_id=self.line_id,
                    attempt_id="writer-attempt-3", generation=3,
                    worker_id="worker-3", profile=self.profile,
                    based_checkpoint_id=self.checkpoint["checkpoint_id"])
            refusals.append(denied.exception)
            answer = honest(repository, evidence)
            with open(marker, "w") as writing:
                writing.write("restored checkpoint")
            return answer

        self.profile.restore_checkpoint = restoring
        answered = self.restore()
        return {"answered": answered, "crossings": crossings,
                "refusals": refusals, "marker": marker}

    def survives(self, held):
        """The successor is admitted after the recovery, and its bytes stay."""
        successor = grant_writer(
            self.store, line_id=self.line_id, attempt_id="writer-attempt-3",
            generation=3, worker_id="worker-3", profile=self.profile,
            based_checkpoint_id=self.checkpoint["checkpoint_id"])
        self.assertEqual(successor["state"], "active")
        with open(held["marker"], "w") as writing:
            writing.write("successor work must survive")
        self.assertEqual(len(held["crossings"]), 1)
        with open(held["marker"]) as reading:
            self.assertEqual(reading.read(), "successor work must survive")

    def test_two_handles_of_one_manager_cannot_overlap_restoration(self):
        """THE SAME-MANAGER OVERLAP, which the incarnation fence did not stop.

        Review 2026-09-26T02:01:41Z [P1] reproduced it by changing ONE operand:
        the competing handle's incarnation, so it matches the executor's.
        `ControlStore.open` validates a nonempty identity and neither reserves it
        nor serializes its callers, so an incarnation names a manager LIFETIME and
        not an exclusive in-flight call. Both callers reached the profile, the
        second released the line, a successor was admitted and wrote, and the
        first overwrote those bytes and answered the second's success through
        completion replay.

        WHAT HOLDS IT NOW is the in-flight registry, keyed by this recovery's own
        operation identity and scoped to the process -- the old connection-keyed
        guard with the key it should always have had. Measured here as exactly one
        external crossing and a successor whose bytes survive.
        """
        self.abandoned()
        self.attempt("writer-attempt-3", 3, "baton.impl", "writer-3")
        held = self.overlapping(
            lambda: ControlStore.open(self.control_path,
                                      incarnation=self.store.incarnation,
                                      clock=lambda: NOW))
        self.assertEqual(len(held["crossings"]), 1)
        refusal, denied = held["refusals"]
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("so this act is held rather than repeating them",
                      refusal.message)
        self.assertIn("so this act is held rather than repeating them",
                      refusal.message)
        self.assertIn("does not admit a writer", denied.message)
        self.assertEqual(held["answered"]["state"], "correction-ready")
        self.survives(held)

    def test_a_same_manager_caller_past_its_reads_is_held_too(self):
        """AND ONE THAT HAS ALREADY PROVED EVERYTHING IT READS.

        The review asked for the past-entry-reads variant of the same-manager
        schedule. The competing caller runs the real `_abandoned_evidence` proofs
        on its own handle first, so it arrives at the boundary having established
        every fact its entry checks establish -- and is still held, because none of
        those facts is evidence that the executor stopped.
        """
        self.abandoned()
        self.attempt("writer-attempt-3", 3, "baton.impl", "writer-3")
        held = self.overlapping(
            lambda: ControlStore.open(self.control_path,
                                      incarnation=self.store.incarnation,
                                      clock=lambda: NOW),
            past_reads=True)
        self.assertEqual(len(held["crossings"]), 1)
        refusal = held["refusals"][0]
        self.assertIn("so this act is held rather than repeating them",
                      refusal.message)
        self.survives(held)

    def test_a_caller_past_its_reads_is_held_when_it_loses_the_intent(self):
        """A COMPETING CALLER ALREADY PAST ITS PRELIMINARY READS.

        The review asked for this schedule specifically. Both callers complete
        their entry proofs before either commits, so the loser does not discover
        the intent by reading it -- it gets the committed document back through
        `store.transact`'s replay, already past every check that might have
        stopped it. It is held by the executor comparison, which is placed where
        both branches converge for exactly this reason.
        """
        self.abandoned()
        entered = threading.Barrier(2, timeout=WAIT)
        answers = {}
        failures = []
        crossings = []
        honest_evidence = review_cycles._abandoned_evidence
        honest_profile = self.profile.restore_checkpoint

        def rendezvous(store, attempt_id, generation, policy, what):
            proved = honest_evidence(store, attempt_id, generation, policy, what)
            try:
                entered.wait()
            except threading.BrokenBarrierError:
                raise AssertionError(
                    "both callers did not reach the pre-intent rendezvous"
                ) from None
            return proved

        def counting(repository, evidence):
            crossings.append(repository)
            return honest_profile(repository, evidence)

        self.profile.restore_checkpoint = counting

        def caller(name):
            beside = ControlStore.open(self.control_path,
                                       incarnation=f"manager-{name}",
                                       clock=lambda: NOW)
            try:
                answers[name] = self.restore(store=beside)
            except ContractRefusal as refusal:
                answers[name] = refusal
            except BaseException as failure:            # noqa: BLE001
                failures.append(failure)
                entered.abort()
            finally:
                beside.close()

        with mock.patch.object(review_cycles, "_abandoned_evidence",
                               rendezvous):
            threads = [threading.Thread(target=caller, args=("a",)),
                       threading.Thread(target=caller, args=("b",))]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=JOIN)
                self.assertFalse(thread.is_alive())
        if failures:
            raise failures[0]

        # ONE EXECUTOR CROSSED, and the loser was held rather than repeating it.
        self.assertEqual(len(crossings), 1)
        answered = [one for one in answers.values() if type(one) is dict]
        refused = [one for one in answers.values()
                   if isinstance(one, ContractRefusal)]
        self.assertEqual(len(answered), 1)
        self.assertEqual(len(refused), 1)
        self.assertIn("is in flight under manager incarnation",
                      refused[0].message)
        self.assertEqual(self.line_row()["state"], "correction-ready")

    def test_an_execution_whose_executor_is_gone_stays_held_on_reopen(self):
        """UNRESOLVED EXECUTION ON REOPEN, and the hold is the required outcome.

        The executor crashes inside its profile, so its intent stands and its
        revocation stands. A manager reopening the store comes back under a NEW
        incarnation -- which is what a restart is -- and is HELD: an intent and a
        revocation are not evidence that their executor stopped, and presuming
        death is the substitution this dossier has refused since stage 2.

        AND THE HOLD IS SAFE, not merely conservative: the line is still `writing`,
        so no successor is admitted onto a checkout nobody proved. What is NOT
        solved is a positive settling act for a dead incarnation; PLAN.md records
        supplying one as remaining scope, and this case is its reproduction.
        """
        writer = self.abandoned()
        self.attempt("writer-attempt-3", 3, "baton.impl", "writer-3")

        def crash(repository, evidence):
            raise RuntimeError("the executor died inside its restoration")

        self.profile.restore_checkpoint = crash
        with self.assertRaisesRegex(RuntimeError, "died inside"):
            self.restore()

        restarted = ControlStore.open(self.control_path,
                                      incarnation="manager-after-restart",
                                      clock=lambda: NOW)
        self.addCleanup(restarted.close)
        crossings = []
        honest = Profile.restore_checkpoint

        def counting(inner, repository, evidence):
            crossings.append(repository)
            return honest(inner, repository, evidence)

        self.profile.restore_checkpoint = counting.__get__(self.profile)
        with self.assertRaises(ContractRefusal) as caught:
            self.restore(store=restarted)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("manager-1", caught.exception.message)
        self.assertIn("manager-after-restart", caught.exception.message)
        # HELD WITHOUT TOUCHING THE CHECKOUT, and with nobody admitted.
        self.assertEqual(crossings, [])
        self.assertEqual(self.line_row()["state"], "writing")
        self.assertEqual(writer_of(self.store,
                                   writer["writer_id"])["state"], "revoked")
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=ABANDONED, generation=2))
        with self.assertRaises(ContractRefusal) as denied:
            grant_writer(restarted, line_id=self.line_id,
                         attempt_id="writer-attempt-3", generation=3,
                         worker_id="worker-3", profile=self.profile,
                         based_checkpoint_id=self.checkpoint["checkpoint_id"])
        self.assertIn("does not admit a writer", denied.exception.message)
        # AND SO IS THE ORIGINAL EXECUTOR, which is the change: ownership is now a
        # journalled EPISODE rather than a fact about a process, and the episode
        # this executor claimed has no completion behind it. Its own effects are
        # as unknown as anybody's, so it is held on the same rule.
        self.profile.restore_checkpoint = Profile.restore_checkpoint.__get__(
            self.profile)
        with self.assertRaises(ContractRefusal) as again:
            self.restore()
        self.assertIn("so this act is held rather than repeating them",
                      again.exception.message)
        self.assertEqual(crossings, [])
        self.assertEqual(self.line_row()["state"], "writing")

    def test_an_interrupted_restoration_admits_nobody_and_stays_held(self):
        """FAILURE, INTERRUPTION AND SAFE RETRY, in one schedule.

        A `RuntimeError` from the profile is not a `ContractRefusal`, so nothing
        is journalled as refused and the committed intent stands. What that leaves
        is the retryable state and NOT a release: the writer is revoked, the line
        is still `writing`, no successor can be admitted, and no completed
        recovery exists. The same call then finishes through the resumed path.
        """
        writer = self.abandoned()
        self.attempt("writer-attempt-3", 3, "baton.impl", "writer-3")
        honest = self.profile.restore_checkpoint
        calls = []

        def crash(repository, evidence):
            calls.append(repository)
            if len(calls) == 1:
                raise RuntimeError("simulated restoration crash")
            return honest(repository, evidence)

        self.profile.restore_checkpoint = crash
        with self.assertRaisesRegex(RuntimeError, "simulated"):
            self.restore()

        # THE EXCLUSION IS HELD AND NOBODY IS ADMITTED.
        self.assertEqual(writer_of(self.store,
                                   writer["writer_id"])["state"], "revoked")
        self.assertEqual(self.line_row()["state"], "writing")
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=ABANDONED, generation=2))
        with self.assertRaises(ContractRefusal) as caught:
            grant_writer(self.store, line_id=self.line_id,
                         attempt_id="writer-attempt-3", generation=3,
                         worker_id="worker-3", profile=self.profile,
                         based_checkpoint_id=self.checkpoint["checkpoint_id"])
        self.assertIn("does not admit a writer", caught.exception.message)
        # AND THE INTENT IS STILL THERE TO FINISH, which is what makes the
        # interruption retryable rather than terminal.
        self.assertIsNotNone(self.store.operation_record(
            review_cycles._restore_operation_id(
                review_cycles.RESTORE_INTENT_KIND, ABANDONED, 2)))

        # AND THE RETRY IS NOW HELD, which is the behaviour change review
        # 2026-09-26T02:11:12Z requires and this dossier's PLAN pins. A profile
        # exception is NOT evidence that every external effect ended, so the
        # claimed execution episode stays unsettled and no later caller may repeat
        # it. The previous design resumed here; that inference is withdrawn.
        with self.assertRaises(ContractRefusal) as held:
            self.restore()
        self.assertEqual((held.exception.category, held.exception.code),
                         ("refused", "precondition"))
        self.assertIn("so this act is held rather than repeating them",
                      held.exception.message)
        self.assertEqual(len(calls), 1)
        # NOTHING MOVED: no completion, the line still `writing`, nobody admitted.
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=ABANDONED, generation=2))
        self.assertEqual(self.line_row()["state"], "writing")
        with self.assertRaises(ContractRefusal) as denied:
            grant_writer(
                self.store, line_id=self.line_id,
                attempt_id="writer-attempt-3", generation=3,
                worker_id="worker-3", profile=self.profile,
                based_checkpoint_id=self.checkpoint["checkpoint_id"])
        self.assertIn("does not admit a writer", denied.exception.message)

    def test_a_completed_recovery_replays_without_touching_the_checkout(self):
        """SAFE REPLAY: an exact retry answers its record and restores nothing."""
        self.abandoned()
        first = self.restore()
        calls = []
        honest = self.profile.restore_checkpoint

        def counting(repository, evidence):
            calls.append(repository)
            return honest(repository, evidence)

        self.profile.restore_checkpoint = counting
        with AnOpenTransaction(self.store._connection) as observing:
            replay = self.restore()
        self.assertEqual(replay, first)
        self.assertEqual(calls, [])
        self.assertEqual(observing.under_lock, [])

    def test_a_completion_whose_line_moved_releases_nothing(self):
        """STALE COMPLETION, at the completing transaction's own re-proof.

        The world is moved under an adopted intent at the exact cut point: the
        line is released by somebody else while this restoration is inside the
        profile. The completion must refuse rather than release a line it no
        longer holds, and the refusal must be NON-DURABLE so the intent stays
        retryable.
        """
        self.abandoned()
        honest = self.profile.restore_checkpoint
        moved = []

        def moving(repository, evidence):
            answer = honest(repository, evidence)
            if not moved:
                moved.append(True)
                # SOMEBODY ELSE RELEASES THE LINE, which is the only way this
                # state is reachable; a supported operation cannot do it while
                # the exclusion is held, so the move is this module's and is
                # labelled as such.
                self.store._connection.execute(
                    "UPDATE review_lines SET state = 'correction-ready' "
                    "WHERE line_id = ?", (self.line_id,))
            return answer

        self.profile.restore_checkpoint = moving
        with self.assertRaises(ContractRefusal) as caught:
            self.restore()
        self.assertEqual(moved, [True])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("no longer holds the exclusion", caught.exception.message)
        # NO COMPLETED RECOVERY AND NO REFUSED ROW -- the intent stays retryable.
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=ABANDONED, generation=2))
        self.assertIsNone(self.store.operation_record(
            review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)))

    def test_a_resumption_will_not_finish_somebody_elses_revocation(self):
        """AND A REVOCATION THIS RECOVERY DID NOT MAKE IS NOT ITS EXCLUSION.

        `freeze_checkpoint` also revokes, so a resumed recovery that accepted any
        revoked writer would let a round that REACHED its checkpoint look like an
        unfinished correction. The reason is compared, and this case changes only
        that: the intent is committed, then the revocation reason is rewritten.
        """
        writer = self.abandoned()
        honest = self.profile.restore_checkpoint

        def crash(repository, evidence):
            raise RuntimeError("simulated restoration crash")

        self.profile.restore_checkpoint = crash
        with self.assertRaisesRegex(RuntimeError, "simulated"):
            self.restore()
        self.profile.restore_checkpoint = honest
        self.store._connection.execute(
            "UPDATE line_writers SET revocation_reason = 'checkpoint' "
            "WHERE writer_id = ?", (writer["writer_id"],))
        with self.assertRaises(ContractRefusal) as caught:
            self.restore()
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("this recovery's own", caught.exception.message)
        self.assertEqual(self.line_row()["state"], "writing")

    def test_a_nested_restoration_on_one_connection_is_refused(self):
        """A NESTED CALL IS JUST A SECOND EXECUTOR, and is held as one.

        The profile runs outside every transaction, so a nested call reached from
        it can no longer corrupt a savepoint -- what it would be is a second
        executor of this recovery's external act, which is worse. Review
        2026-09-26T02:01:41Z [P1] replaced the connection-keyed guard with an
        in-flight registry keyed by the recovery, and a nested call names the same
        recovery, so it is held by exactly that boundary.

        MEASURED: the refusal moved from `operation-collision` to `precondition`
        with the boundary, and the message is now the held-execution one rather
        than a statement about this connection.
        """
        self.abandoned()
        nested = []
        honest = self.profile.restore_checkpoint

        def reentering(repository, evidence):
            try:
                self.restore()
            except ContractRefusal as refusal:
                nested.append(refusal)
            return honest(repository, evidence)

        self.profile.restore_checkpoint = reentering
        answered = self.restore()
        self.assertEqual(answered["state"], "correction-ready")
        [refusal] = nested
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("so this act is held rather than repeating them",
                      refusal.message)


    def test_a_caller_stale_at_admission_observes_the_completion(self):
        """THE EPISODE GAP, SCHEDULED AGAINST THE CURRENT SEAM.

        Review 2026-09-26T02:25:54Z [P1] scheduled a caller paused between the
        eligibility transaction and a SEPARATE claim transaction: it then took a
        LATER episode because a competitor had become visible, and restored over
        an admitted successor. That seam no longer exists -- the decision and the
        claim are one transaction -- and the reviewer's probe can no longer run
        because the symbol it wrapped is gone. AN ABSENT SYMBOL IS NOT EVIDENCE,
        which that review says in terms, so this case schedules the same intent
        against the seam that does exist: a caller that is stale when it reaches
        admission.

        A competitor runs to completion BEFORE this caller's admission transaction
        opens. What the caller must then do is observe the completion and perform
        no external effect at all -- measured as zero crossings of its own and a
        successor's bytes still intact.
        """
        self.abandoned()
        self.attempt("writer-attempt-3", 3, "baton.impl", "writer-3")
        marker = os.path.join(self.line_path, "successor-data.txt")
        crossings = []
        honest = self.profile.restore_checkpoint
        competitor = ControlStore.open(self.control_path,
                                       incarnation=self.store.incarnation,
                                       clock=lambda: NOW)
        self.addCleanup(competitor.close)

        def counting(repository, evidence):
            crossings.append(repository)
            return honest(repository, evidence)

        self.profile.restore_checkpoint = counting
        # THE COMPETITOR GOES FIRST AND FINISHES, so the caller below is stale in
        # exactly the way the reviewer's schedule made it stale.
        first = self.restore(store=competitor)
        self.assertEqual(first["state"], "correction-ready")
        self.assertEqual(len(crossings), 1)
        successor = grant_writer(
            self.store, line_id=self.line_id, attempt_id="writer-attempt-3",
            generation=3, worker_id="worker-3", profile=self.profile,
            based_checkpoint_id=self.checkpoint["checkpoint_id"])
        self.assertEqual(successor["state"], "active")
        with open(marker, "w") as writing:
            writing.write("successor work must survive")

        # THE STALE CALLER OBSERVES THE COMPLETION AND CROSSES NOTHING.
        answered = self.restore()
        self.assertEqual(answered, first)
        self.assertEqual(len(crossings), 1)
        with open(marker) as reading:
            self.assertEqual(reading.read(), "successor work must survive")

    def test_another_process_cannot_restore_while_this_one_owns_the_episode(self):
        """A REAL SECOND PROCESS, which no in-process boundary could hold.

        Review 2026-09-26T02:01:41Z and 02:11:12Z both reproduced a fresh Python
        process adopting an unfinished external act. Ownership is now a journalled
        episode, so the child is held by a row rather than by anything about this
        process -- measured by the child's own exit status and by this executor's
        crossings and the successor's bytes.
        """
        import subprocess
        import sys

        self.abandoned()
        self.attempt("writer-attempt-3", 3, "baton.impl", "writer-3")
        marker = os.path.join(self.line_path, "successor-data.txt")
        crossings = []
        child = {}
        honest = self.profile.restore_checkpoint
        script = (
            "import sys\n"
            "from baton_v12.worker_manager import ControlStore\n"
            "from baton_v12.worker_manager.review_cycles import "
            "restore_abandoned_correction\n"
            "from tests.manager.test_review_cycles import Profile, NOW\n"
            "store = ControlStore.open(sys.argv[1], incarnation=sys.argv[2],\n"
            "                          clock=lambda: NOW)\n"
            "restore_abandoned_correction(store, attempt_id=sys.argv[3],\n"
            "    generation=2, retention_policy_digest=sys.argv[4],\n"
            "    profile=Profile())\n")

        def counting(repository, evidence):
            crossings.append(repository)
            if len(crossings) == 1:
                child["run"] = subprocess.run(
                    [sys.executable, "-c", script, self.control_path,
                     self.store.incarnation, ABANDONED, RETENTION],
                    capture_output=True, text=True, timeout=JOIN,
                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            return honest(repository, evidence)

        self.profile.restore_checkpoint = counting
        answered = self.restore()

        # THE CHILD WAS HELD: it exited nonzero and its refusal names the episode.
        self.assertNotEqual(child["run"].returncode, 0)
        self.assertIn("so this act is held rather than repeating them",
                      child["run"].stderr)
        # ONE CROSSING, THIS EXECUTOR'S, and the recovery completed once.
        self.assertEqual(len(crossings), 1)
        self.assertEqual(answered["state"], "correction-ready")
        # AND A SUCCESSOR'S BYTES SURVIVE.
        successor = grant_writer(
            self.store, line_id=self.line_id, attempt_id="writer-attempt-3",
            generation=3, worker_id="worker-3", profile=self.profile,
            based_checkpoint_id=self.checkpoint["checkpoint_id"])
        self.assertEqual(successor["state"], "active")
        with open(marker, "w") as writing:
            writing.write("successor work must survive")
        self.assertEqual(len(crossings), 1)
        with open(marker) as reading:
            self.assertEqual(reading.read(), "successor work must survive")


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only the cases defined in THIS module."""
    suite = unittest.TestSuite()
    for owner in list(globals().values()):
        if (isinstance(owner, type) and issubclass(owner, unittest.TestCase)
                and owner.__module__ == __name__):
            for name in loader.getTestCaseNames(owner):
                if name in owner.__dict__:
                    suite.addTest(owner(name))
    return suite


if __name__ == "__main__":
    unittest.main()
