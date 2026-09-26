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
import subprocess
import sys
import threading
import time
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (ControlStore, abandon_attempt,
                                      attach_review, create_line,
                                      discharge_abandoned_quiescence_gate,
                                      freeze_checkpoint, grant_writer, line_of,
                                      record_verdict, writer_of)
from baton_v12.worker_manager import review_cycles, workspaces
from baton_v12.worker_manager.review_cycles import (
    RESTORE_KIND, abandoned_correction_of, restore_abandoned_correction)
from baton_v12.worker_manager.store import _recorded, manager_signature
from baton_v12.checkpoint_profiles import ProfileRefusal
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


class AccountedProfile(Profile):
    """The accepted profile, plus the operand the product now always passes.

    Review 2026-09-26T04:15:08Z makes the accountable boundary mandatory, so
    `restore_abandoned_correction` always hands a runner to `restore_checkpoint`. The
    accepted `tests.manager.test_review_cycles.Profile` does not take one and is NOT mine
    to change, so this subclass -- which IS mine -- accepts it, issues exactly one
    accounted command through it, and then does what that profile has always done.

    ONE COMMAND, so a case can reason about the account without counting. The production
    profile issues several; its own cases cover that.
    """

    def restore_checkpoint(self, repository, evidence, *, runner=None):
        if runner is not None:
            # A REAL BUT HARMLESS ARGV, because this profile is used with BOTH the fixture
            # launcher and the production one, and the production launcher actually
            # executes what it is given. Measured: a non-executable placeholder raised
            # FileNotFoundError under the real launcher.
            runner(("/bin/sh", "-c", "true"))
        return Profile.restore_checkpoint(self, repository, evidence)

    def validate(self, repository, evidence, *, current=False, runner=None):
        # THE SETTLEMENT VALIDATES THROUGH ITS OWN ACCOUNTED RUNNER -- review
        # 2026-09-26T04:58:07Z [P2] refuses the "these are only reads" assumption -- so
        # this accepts the operand for the same reason `restore_checkpoint` does, and
        # issues one command through it so a case can see the settlement's own account.
        if runner is not None:
            runner(("/bin/sh", "-c", "true"))
        return Profile.validate(self, repository, evidence, current=current)


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
        self.profile = AccountedProfile()
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

    def accounted(self, ending="ended"):
        """A launcher and a cessation observer that need no real process.

        Review 2026-09-26T04:15:08Z makes the accountable boundary MANDATORY, so every
        success path here must supply one: an unaccountable restoration is now held before
        it writes anything. These two are LABELLED FIXTURES. The launcher records an intent
        and then a synthetic group for each command, in that order, exactly as the
        production launcher does; the observer answers `ending` for records it issued and
        `unknown` for anything else.

        WHAT THEY PROVE AND DO NOT. They exercise the recording order, the binding to this
        recovery and episode, and the completion's dependence on the account. They attest
        NOTHING about a real process -- `restoration_launcher` and `restoration_cessation`
        are the production boundary and have their own cases, which start real children.
        `ending` is a parameter so a case can ask for `running` or `unknown` and watch the
        completion hold.
        """
        issued = []
        minting = threading.Lock()

        def launcher(record):
            def launched(argv, *, input=None):
                record("intent", None)
                # SYNTHETIC BUT JSON-SAFE. Measured: negative ids were refused by
                # canonical JSON, which admits only non-negative integers. These are far
                # above any real process id on this host, so they cannot collide with a
                # live one, and the observer only answers for records it issued.
                # MINTED UNDER A LOCK, because concurrent restorations share this
                # fixture. Measured: `len(issued)` raced between threads and the observer
                # then failed to recognise a token it had issued, which made a legitimate
                # winner look held.
                with minting:
                    number = 900000 + len(issued) + 1
                    token = {"group": number, "leader": number,
                             "started": len(issued) + 1}
                    issued.append(token)
                record("group", token)
                return {"returncode": 0, "stdout": "", "stderr": ""}
            return launched

        def cessation(observed):
            # ANSWERS ONLY FOR TOKENS THIS FIXTURE ACTUALLY MINTED, read under the same
            # lock that mints them.
            #
            # MEASURED, AND IT WAS WRONG TWICE BEFORE THIS. First it scanned `issued`
            # without a lock and failed to recognise its own token, making a legitimate
            # winner look held. Then it recognised anything with a group at or above
            # 900000 -- "far above any real process id" -- and review 271735's
            # completion-effects probe caught that for what it is: THIS HOST ALLOCATES
            # PROCESS IDS ABOVE TWO MILLION, so the fixture answered `ended` about a REAL
            # process launched by the production launcher, which is precisely the forged
            # attestation this whole selection exists to prevent. A fixture may only speak
            # about work it performed itself, and membership is the only honest test of
            # that.
            if type(observed) is not dict:
                return "unknown"
            with minting:
                known = [dict(token) for token in issued]
            for token in known:
                if all(observed.get(name) == token[name] for name in token):
                    return ending
            return "unknown"

        return {"launcher": launcher, "cessation": cessation, "issued": issued}

    def restore(self, store=None, **overrides):
        # THE ACCOUNTED BOUNDARY IS THE DEFAULT for every case. A case about a MISSING
        # boundary passes launcher=None or cessation=None explicitly; a case about real
        # processes passes the production pair.
        if not hasattr(self, "_boundary"):
            self._boundary = self.accounted()
        operands = {"attempt_id": ABANDONED, "generation": 2,
                    "retention_policy_digest": RETENTION,
                    "profile": self.profile,
                    "launcher": self._boundary["launcher"],
                    "cessation": self._boundary["cessation"]}
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

        def waiting(repository, evidence, *, runner=None):
            store = self.store if holder is None else holder["store"]
            seen.append(store._connection.in_transaction)
            arrived.set()
            if not release.wait(WAIT):
                raise AssertionError("the restoration was never released")
            return honest(repository, evidence, runner=runner)

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

        def watching(repository, evidence, *, runner=None):
            observed["writer"] = writer_of(self.store,
                                           writer["writer_id"])["state"]
            observed["reason"] = self.store._connection.execute(
                "SELECT revocation_reason FROM line_writers WHERE writer_id = ?",
                (writer["writer_id"],)).fetchone()[0]
            observed["line"] = self.line_row()["state"]
            return honest(repository, evidence, runner=runner)

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
                    # AND THE REFUSAL IS ONE OF THIS RECOVERY'S TWO EXCLUSIONS, not any
                    # refusal: a case that accepted any message would pass just as happily
                    # on an unrelated precondition.
                    #
                    # WHICH ONE DEPENDS ON THE INTERLEAVING, measured 2026-09-26 as a real
                    # flake in this case after the executor gate became conditional on an
                    # UNSETTLED episode. A loser that arrives once an episode is claimed is
                    # refused by the executor gate; one that arrives before any episode
                    # exists falls through to the kernel exclusion, which is the stronger
                    # FOUR OUTCOMES ARE PERMITTED HERE AND EACH HAS ITS OWN DETERMINISTIC
                    # CASE, which is what makes this enumeration a contract and not a
                    # widening. Review 2026-09-26T05:47:16Z refused the alternative -- adding
                    # a message every time a thread schedule surprised me -- and it was
                    # right: which one a loser gets depends only on how far it had read
                    # before the winner committed, and every one of the four is refused
                    # BEFORE any second effect.
                    #
                    #   the executor gate ............ test_a_second_restorer_is_held...
                    #   the kernel exclusion ......... test_another_process_cannot_restore...
                    #   the line's writer attachment . test_no_successor_is_admitted...
                    #   the fresh path's writer read . test_a_loser_that_reads_the_writer...
                    #
                    # EVERY ONE IS refused/precondition, which is asserted rather than
                    # assumed, and the invariant that matters -- exactly one recovery, one
                    # effect -- is asserted above.
                    self.assertEqual((answer.category, answer.code),
                                     ("refused", "precondition"))
                    self.assertTrue(
                        any(anchor in answer.message for anchor in (
                            "is in flight under manager incarnation",
                            "is held by another manager on this line",
                            "line holds active writers",
                            "a revoked writer is what one that did leaves behind")),
                        f"unenumerated refusal: {answer.message}")
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

        def restoring(repository, evidence, *, runner=None):
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
            answer = honest(repository, evidence, runner=runner)
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

        def restoring(repository, evidence, *, runner=None):
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
            answer = honest(repository, evidence, runner=runner)
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
        # THE LOCK REFUSES FIRST NOW, which is earlier and stronger than the episode
        # check: review 2026-09-26T03:17:01Z's exclusion is taken before admission, so
        # a competing manager never reaches the episode read. Both boundaries are
        # enumerated exactly rather than accepting any refusal.
        self.assertTrue(
            any(phrase in refusal.message for phrase in (
                "restoration execution is held by another manager on this line",
                "so this act is held rather than repeating them")),
            f"the competitor was refused by neither boundary: {refusal.message}")
        # THE LOCK REFUSES FIRST NOW, which is earlier and stronger than the episode
        # check: review 2026-09-26T03:17:01Z's exclusion is taken before admission, so
        # a competing manager never reaches the episode read. Both boundaries are
        # enumerated exactly rather than accepting any refusal.
        self.assertTrue(
            any(phrase in refusal.message for phrase in (
                "restoration execution is held by another manager on this line",
                "so this act is held rather than repeating them")),
            f"the competitor was refused by neither boundary: {refusal.message}")
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
        # THE LOCK REFUSES FIRST NOW, which is earlier and stronger than the episode
        # check: review 2026-09-26T03:17:01Z's exclusion is taken before admission, so
        # a competing manager never reaches the episode read. Both boundaries are
        # enumerated exactly rather than accepting any refusal.
        self.assertTrue(
            any(phrase in refusal.message for phrase in (
                "restoration execution is held by another manager on this line",
                "so this act is held rather than repeating them")),
            f"the competitor was refused by neither boundary: {refusal.message}")
        self.survives(held)

    def test_a_competitor_cannot_even_reach_the_pre_intent_rendezvous(self):
        """SUPERSEDED SCHEDULE, restated to what is now true.

        This case used to rendezvous two callers after their `_abandoned_evidence` reads
        and before either committed an intent, and assert that the loser was held. That
        window no longer exists to schedule: the outer exclusion is taken BEFORE
        admission, so a competing caller is refused at the lock and never reaches those
        reads at all. Review 2026-09-26T03:17:01Z said the same of the reviewer's own
        atomic-admission probe, and it is true of mine.

        SO THE CASE ASSERTS WHAT IS ACTUALLY TRUE, which I had to measure rather than
        assume: the competitor DOES perform its entry reads -- `_abandoned_evidence` runs
        before the exclusion is taken -- and is then refused AT THE LOCK, before
        admission and before any intent. My first restatement claimed those reads never
        happened and the wrapper proved otherwise. So this is still the
        past-its-reads schedule; what changed is which boundary holds it, and exactly one
        restoration crosses the profile.
        """
        self.abandoned()
        reads = []
        crossings = []
        honest_evidence = review_cycles._abandoned_evidence
        honest_profile = self.profile.restore_checkpoint
        other = ControlStore.open(self.control_path,
                                  incarnation=self.store.incarnation,
                                  clock=lambda: NOW)
        self.addCleanup(other.close)

        def counting_evidence(store, attempt_id, generation, policy, what):
            reads.append(store)
            return honest_evidence(store, attempt_id, generation, policy, what)

        def restoring(repository, evidence, *, runner=None):
            crossings.append(repository)
            with self.assertRaises(ContractRefusal) as caught:
                self.restore(store=other)
            self.assertIn("restoration execution is held by another manager on this line",
                          caught.exception.message)
            return honest_profile(repository, evidence, runner=runner)

        self.profile.restore_checkpoint = restoring
        with mock.patch.object(review_cycles, "_abandoned_evidence",
                               counting_evidence):
            answered = self.restore()
        self.assertEqual(answered["state"], "correction-ready")
        # THE COMPETITOR DID READ, and was refused at the lock anyway -- which is the
        # point: being past its reads buys it nothing.
        self.assertIn(other, reads)
        # AND EXACTLY ONE RESTORATION CROSSED THE PROFILE.
        self.assertEqual(len(crossings), 1)

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

        def crash(repository, evidence, *, runner=None):
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

        def crash(repository, evidence, *, runner=None):
            calls.append(repository)
            if len(calls) == 1:
                raise RuntimeError("simulated restoration crash")
            return honest(repository, evidence, runner=runner)

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

        def counting(repository, evidence, *, runner=None):
            calls.append(repository)
            return honest(repository, evidence, runner=runner)

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

        def moving(repository, evidence, *, runner=None):
            answer = honest(repository, evidence, runner=runner)
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

        def crash(repository, evidence, *, runner=None):
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

        def reentering(repository, evidence, *, runner=None):
            try:
                self.restore()
            except ContractRefusal as refusal:
                nested.append(refusal)
            return honest(repository, evidence, runner=runner)

        self.profile.restore_checkpoint = reentering
        answered = self.restore()
        self.assertEqual(answered["state"], "correction-ready")
        [refusal] = nested
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        # THE LOCK REFUSES FIRST NOW, which is earlier and stronger than the episode
        # check: review 2026-09-26T03:17:01Z's exclusion is taken before admission, so
        # a competing manager never reaches the episode read. Both boundaries are
        # enumerated exactly rather than accepting any refusal.
        self.assertTrue(
            any(phrase in refusal.message for phrase in (
                "restoration execution is held by another manager on this line",
                "so this act is held rather than repeating them")),
            f"the competitor was refused by neither boundary: {refusal.message}")


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

        def counting(repository, evidence, *, runner=None):
            crossings.append(repository)
            return honest(repository, evidence, runner=runner)

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

        def counting(repository, evidence, *, runner=None):
            crossings.append(repository)
            if len(crossings) == 1:
                child["run"] = subprocess.run(
                    [sys.executable, "-c", script, self.control_path,
                     self.store.incarnation, ABANDONED, RETENTION],
                    capture_output=True, text=True, timeout=JOIN,
                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            return honest(repository, evidence, runner=runner)

        self.profile.restore_checkpoint = counting
        answered = self.restore()

        # THE CHILD WAS HELD: it exited nonzero and its refusal names the episode.
        self.assertNotEqual(child["run"].returncode, 0)
        # THE CHILD IS NOW HELD BY THE LOCK, an operating-system observation that a
        # separate process cannot talk its way past. Either boundary is a correct hold
        # and both are named.
        self.assertTrue(
            any(phrase in child["run"].stderr for phrase in (
                "restoration execution is held by another manager on this line",
                "so this act is held rather than repeating them")),
            f"the child was not held: {child['run'].stderr[-400:]}")
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


    # -- the settlement entry, fail-closed -----------------------------------

    def interrupted(self):
        """One claimed execution episode whose profile raised, leaving it unsettled.

        ONE ACCOUNTED COMMAND FIRST, and then the death: this is the ordinary shape of an
        interrupted execution -- work was launched and recorded, and then the manager went
        away. An executor that died before its FIRST command leaves an empty account,
        which the settlement reads differently and which has its own case.
        """
        def crash(repository, evidence, *, runner=None):
            runner(("fixture", "reset"))
            raise RuntimeError("the executor died inside its restoration")

        honest = self.profile.restore_checkpoint
        self.profile.restore_checkpoint = crash
        with self.assertRaisesRegex(RuntimeError, "died inside"):
            self.restore()
        self.profile.restore_checkpoint = honest
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        claimed = review_cycles._claimed_episodes(self.store, recovery)
        self.assertEqual(len(claimed), 1)
        _, owner = self.store.replay(
            review_cycles._execution_id(recovery, 1), claimed[0]["signature"],
            kind=review_cycles.RESTORE_EXECUTION_KIND)
        return recovery, owner["executor"]

    def settle(self, store=None, **overrides):
        # THE OBSERVER IS THE DEFAULT, exactly as for a restoration: a settlement with no
        # cessation probe is refused, and a case about THAT passes cessation=None.
        if not hasattr(self, "_boundary"):
            self._boundary = self.accounted()
        operands = {"attempt_id": ABANDONED, "generation": 2,
                    "profile": self.profile,
                    "launcher": self._boundary["launcher"],
                    "cessation": self._boundary["cessation"]}
        operands.update(overrides)
        return review_cycles.settle_restoration_execution(
            self.store if store is None else store, **operands)

    def fresh_manager(self, incarnation="manager-2"):
        """A SEPARATE ControlStore handle, opened and used as its own manager.

        Review 2026-09-26T04:43:58Z: separate handles are how the concurrent and
        fresh-manager schedules are staged; one thread-affine connection is a fixture
        limitation and not a reason to leave them unproved.
        """
        other = ControlStore.open(self.control_path, incarnation=incarnation,
                                  clock=lambda: NOW)
        self.addCleanup(other.close)
        return other

    def test_a_crashed_executor_is_settled_and_a_fresh_manager_retries(self):
        """THE WHOLE POINT OF THE SETTLEMENT, end to end, for the first time.

        Owner ruling 2026-09-26T02:57:40Z gave an interrupted execution a second exit and
        review 2026-09-26T04:43:58Z required it implemented under the pinned exclusion.
        The schedule: an executor claims episode one, launches an accounted command, and
        dies inside its profile. Its episode is claimed with no completion behind it, so
        every later caller is held -- including a FRESH manager, because the committed
        intent names the dead incarnation forever.

        THEN THE SETTLEMENT, BY A DIFFERENT MANAGER HANDLE. It acquires the restoration
        lock, which is the kernel's answer that no manager still holds this execution; it
        asks the launch account whether the children that executor's runner forked have
        ended; it validates the checkout clean at the retained checkpoint; and it journals
        what it OBSERVED -- there is no operand through which a caller can assert any of
        it, because that operand was the P1 and is gone.

        AND THEN THE RETRY SUCCEEDS ON THAT FRESH MANAGER, taking episode two through the
        ordinary admission and releasing the line to `correction-ready`. Before the
        settlement the same call on the same handle is refused; after it, it works. That
        pair is the property.
        """
        self.abandoned()
        recovery, executor = self.interrupted()
        fresh = self.fresh_manager()
        # BEFORE: a fresh manager is held, and the message names the unsettled episode.
        with self.assertRaises(ContractRefusal) as held:
            self.restore(store=fresh)
        self.assertEqual((held.exception.category, held.exception.code),
                         ("refused", "precondition"))
        self.assertIn("episode 1 of it is claimed with neither a completion nor a "
                      "settlement", held.exception.message)
        self.assertEqual(self.line_row()["state"], "writing")

        settled = self.settle(store=fresh)
        self.assertEqual(settled["episode"], 1)
        self.assertEqual(settled["executor"], executor)
        self.assertEqual(settled["ended"]["exclusion"], "acquired")
        self.assertEqual(settled["ended"]["effects"],
                         "retained-checkpoint-identity")
        self.assertEqual(settled["ended"]["coverage"], "launch-account/1")
        self.assertGreaterEqual(settled["ended"]["launches"], 1)
        # THE SETTLEMENT'S OWN VALIDATION COMMANDS ARE ACCOUNTED TOO, under their own
        # episode label -- review 2026-09-26T04:58:07Z [P2] refuses the assumption that a
        # validation's commands need no account because they only read.
        self.assertGreaterEqual(settled["ended"]["settlement_launches"], 1)
        self.assertEqual(settled["ended"]["settlement_attempt"], "settlement-1-1")
        self.assertEqual(settled["ended"]["prior_settlement_attempts"], [])
        self.assertEqual(
            review_cycles._launch_count(fresh, recovery, "settlement-1-1"),
            settled["ended"]["settlement_launches"])
        self.assertEqual(settled["checkpoint_id"],
                         self.checkpoint["checkpoint_id"])
        self.assertIsNotNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))

        # AFTER: the same fresh manager retries and this time it restores.
        answered = self.restore(store=fresh)
        self.assertEqual(answered["state"], "correction-ready")
        self.assertEqual(self.line_row()["state"], "correction-ready")
        self.assertEqual(len(review_cycles._claimed_episodes(fresh, recovery)), 2)

    def test_a_live_executor_is_not_settled_and_the_kernel_is_what_says_so(self):
        """AN EXECUTION STILL HELD BY A MANAGER IS NOT SETTLED, and no document overrides
        that.

        Review 2026-09-26T03:08:20Z [P1] obtained a settlement about an executor that was
        still on the call stack, by authoring a document about it. There is no such
        operand now, and the observation is the advisory lock itself: while any manager
        holds this line's restoration exclusion, the non-blocking acquisition fails and
        this refuses NON-DURABLY, leaving the episode claimed and the line held.

        THE HOLDER HERE IS A REAL SEPARATE HOLD ON THE REAL OBJECT, not a patched flag --
        `flock` is per open file description, so a second acquisition is refused by the
        kernel even from this process, which is what makes this schedule honest without
        needing a second interpreter.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        fresh = self.fresh_manager()
        with workspaces.hold_restoration_lock(self.storage, self.line_id,
                                              control=self.store) as holding:
            self.assertTrue(holding, "the fixture must hold the real exclusion")
            with self.assertRaises(ContractRefusal) as caught:
                self.settle(store=fresh)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("kernel's answer that its executor is alive",
                      caught.exception.message)
        # NOTHING RECORDED, so no retry can be admitted on the strength of it.
        self.assertIsNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))
        with self.assertRaises(ContractRefusal):
            self.restore(store=fresh)
        self.assertEqual(self.line_row()["state"], "writing")
        # AND ONCE THE HOLD IS GONE the same call settles: the refusal was about the
        # exclusion and nothing else.
        self.assertEqual(self.settle(store=fresh)["episode"], 1)

    def test_an_unresolved_child_is_not_settled(self):
        """A DEAD MANAGER'S LIVE CHILD HOLDS THE SETTLEMENT.

        The lock answers for MANAGERS: the kernel releases it when the process holding it
        dies. It says nothing about a child that manager's runner forked, which can
        outlive it and still write into the checkout. So the settlement asks the same
        launch account the completion is gated on, and anything other than `ended` --
        `running`, `unknown`, or an intent with no group behind it -- HOLDS.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        fresh = self.fresh_manager()
        for answer in ("running", "unknown"):
            with self.subTest(answer=answer):
                with self.assertRaises(ContractRefusal) as caught:
                    self.settle(store=fresh, cessation=lambda observed: answer)
                self.assertEqual((caught.exception.category, caught.exception.code),
                                 ("refused", "precondition"))
                self.assertIn(f"is '{answer}' rather than ended",
                              caught.exception.message)
                self.assertIsNone(fresh.operation_record(
                    review_cycles._settled_id(recovery, 1)))
        # AND A SETTLEMENT WITH NO OBSERVER AT ALL is refused before anything is read.
        with self.assertRaises(ContractRefusal) as missing:
            self.settle(store=fresh, cessation=None)
        self.assertEqual((missing.exception.category, missing.exception.code),
                         ("refused", "capability"))
        self.assertIn("without a cessation observer", missing.exception.message)
        self.assertEqual(self.line_row()["state"], "writing")

    def test_a_mid_call_death_window_holds_but_an_unlaunched_episode_settles(self):
        """THE TWO SHAPES OF AN EMPTY-LOOKING ACCOUNT, and they answer differently.

        AN INTENT WITH NO GROUP is the window between the record and the fork: a child may
        exist for it and nothing can say otherwise, so it HOLDS on both paths.

        NO RECORD AT ALL is different, and only the settlement may read it. The intent is
        committed BEFORE its child exists, so no intent means nothing was ever started --
        an executor that died between claiming its episode and its first command. With the
        kernel already saying no manager holds the execution, that is a complete account of
        nothing having happened, and holding it forever would make the ruling's second exit
        unreachable for the commonest crash there is.
        """
        self.abandoned()
        # an executor that died before its first command: no launch record at all
        def barren(repository, evidence, *, runner=None):
            raise RuntimeError("the executor died before its first command")

        honest = self.profile.restore_checkpoint
        self.profile.restore_checkpoint = barren
        with self.assertRaisesRegex(RuntimeError, "before its first command"):
            self.restore()
        self.profile.restore_checkpoint = honest
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        self.assertEqual(review_cycles._launch_count(self.store, recovery, 1), 0)
        fresh = self.fresh_manager()
        settled = self.settle(store=fresh)
        self.assertEqual(settled["ended"]["launches"], 0)

        # and now the mid-call window, on the NEXT episode: an intent with no group
        def half(repository, evidence, *, runner=None):
            review_cycles._launch_recorder(fresh, recovery, 2)("intent", None)
            raise RuntimeError("the executor died between the record and the fork")

        self.profile.restore_checkpoint = half
        with self.assertRaisesRegex(RuntimeError, "between the record and the fork"):
            self.restore(store=fresh)
        self.profile.restore_checkpoint = honest
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh)
        self.assertIn("recorded an intent with no group behind it",
                      caught.exception.message)
        self.assertEqual(self.line_row()["state"], "writing")

    def test_a_settlement_replays_without_observing_anything_again(self):
        """A SETTLED EPISODE IS SETTLED: the replay performs no external work.

        §4.2 -- an exact replay answers its committed record. What matters here is that it
        does not re-probe: re-running the observations would repeat external I/O for a
        decision already journalled, and a second observation could only disagree with a
        record it cannot change. So the second call is given an observer and a profile that
        FAIL if they are reached.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        fresh = self.fresh_manager()
        first = self.settle(store=fresh)
        touched = []

        def refuses(observed):
            touched.append("cessation")
            raise AssertionError("a replay must not observe again")

        with mock.patch.object(self.profile, "validate") as validating:
            again = self.settle(store=fresh, cessation=refuses)
            validating.assert_not_called()
        self.assertEqual(again, first)
        self.assertEqual(touched, [])

    def test_a_launch_recorded_after_the_observation_is_not_settled(self):
        """THE ACCOUNT IS REVALIDATED IN THE WRITING TRANSACTION.

        Both observations happen outside the transaction that writes the settlement --
        because the standing ruling forbids holding a database lock over external I/O --
        so the write re-reads the episode's recorded launches in pure SQL and refuses if
        they are not the ones that were observed. Without that, an account observed as
        complete could be extended between the observation and the row that rests on it.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        fresh = self.fresh_manager()
        appended = []

        def observing(observed):
            answer = self._boundary["cessation"](observed)
            if not appended:
                appended.append(True)
                # a launch recorded AFTER this observation, by the episode's own recorder
                ordinal = review_cycles._launch_count(fresh, recovery, 1) + 1
                connection = fresh._connection
                connection.execute("BEGIN IMMEDIATE")
                fresh._record(
                    review_cycles._launch_id(recovery, 1, ordinal, "intent"),
                    review_cycles.RESTORE_LAUNCH_KIND, "late-signature",
                    "committed", '{"late": true}', None)
                connection.execute("COMMIT")
            return answer

        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh, cessation=observing)
        self.assertEqual(appended, [True])
        self.assertIn("recorded a launch after its effects were observed",
                      caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))

    def test_two_managers_settle_and_retry_and_only_one_restores(self):
        """CONCURRENT RETRY, through SEPARATE ControlStore handles in their own threads.

        Review 2026-09-26T04:43:58Z is explicit that this is stageable and that a
        thread-affine connection error was my fixture's limitation rather than the
        schedule's impossibility. Each manager here opens its OWN handle inside its OWN
        thread and uses only that one, which is how a real deployment's two processes
        reach this code.

        WHAT IS MEASURED: both may settle -- one writes the record and the other replays
        the same document, which is what an effectively-once identity is for -- but only
        ONE performs a restoration, because the exclusion admits one execution at a time.
        The line ends `correction-ready` exactly once and no episode is left unsettled.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        answers, failures = [], []
        guard = threading.Lock()
        entered = threading.Barrier(2)

        def manager(name):
            store = ControlStore.open(self.control_path, incarnation=name,
                                      clock=lambda: NOW)
            try:
                entered.wait()
                try:
                    settled = review_cycles.settle_restoration_execution(
                        store, attempt_id=ABANDONED, generation=2,
                        profile=self.profile,
                        launcher=self._boundary["launcher"],
                        cessation=self._boundary["cessation"])
                except ContractRefusal as refusal:
                    with guard:
                        failures.append(("settle", name, refusal.code))
                    return
                try:
                    answer = self.restore(store=store)
                except ContractRefusal as refusal:
                    with guard:
                        failures.append(("restore", name, refusal.code))
                    return
                with guard:
                    answers.append((name, settled["episode"], answer["state"]))
            finally:
                store.close()

        if not hasattr(self, "_boundary"):
            self._boundary = self.accounted()
        racing = [threading.Thread(target=manager, args=(name,))
                  for name in ("manager-a", "manager-b")]
        for thread in racing:
            thread.start()
        for thread in racing:
            thread.join()
        self.assertEqual(len(answers) + len(failures), 2)
        # AT MOST ONE RESTORATION, and if one happened the line carries it
        restored = [answer for answer in answers if answer[2] == "correction-ready"]
        self.assertLessEqual(len(restored), 1)
        self.assertEqual(self.line_row()["state"],
                         "correction-ready" if restored else "writing")
        # AND EPISODE ONE IS SETTLED EXACTLY ONCE, whoever got there first
        self.assertIsNotNone(self.store.operation_record(
            review_cycles._settled_id(recovery, 1)))

    def test_a_settled_or_superseded_episode_releases_nothing(self):
        """THE COMPLETION REFUSES OWNERSHIP THAT HAS MOVED ON.

        Review 2026-09-26T03:08:20Z: the callback checked possession of its OWN old
        claim and nothing else, so an executor whose episode had been settled and
        replaced by a retry still satisfied it -- and an old episode must never
        release a line a retry now owns.

        CONTROLLED AND LABELLED: no supported operation can produce a settlement in
        this build, so this case writes the settlement and successor-claim rows
        directly at their derived identities while the executor is inside its
        profile. What is measured is that the product refuses to release on them; the
        rows are this module's, at a seam the product does not offer, and they attest
        nothing about a real executor.
        """
        self.abandoned()
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        planted = []
        honest = self.profile.restore_checkpoint

        def planting(repository, evidence, *, runner=None):
            answer = honest(repository, evidence, runner=runner)
            if not planted:
                planted.append(True)
                self.store._record(
                    review_cycles._settled_id(recovery, 1),
                    review_cycles.RESTORE_SETTLED_KIND, "planted-signature",
                    "committed", '{"planted": true}', None)
            return answer

        self.profile.restore_checkpoint = planting
        with self.assertRaises(ContractRefusal) as caught:
            self.restore()
        self.assertEqual(planted, [True])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("was settled as ended", caught.exception.message)
        # THE LINE IS NOT RELEASED, so no successor can be admitted onto it.
        self.assertEqual(self.line_row()["state"], "writing")
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=ABANDONED, generation=2))


    def test_the_execution_exclusion_is_a_real_lock_beside_the_line(self):
        """THE LOCK IS THE BOUNDARY, and it is an object the kernel answers for.

        Review 2026-09-26T03:17:01Z. What refuses a competing manager is now an
        exclusive advisory lock on a durable object BESIDE the line -- never inside the
        checkout, so the profile's cleanliness validation is untouched. Held across the
        whole external act, so there is no admission-before-acquire and no
        probe-and-drop gap.

        MEASURED AT THE OBJECT ITSELF rather than inferred from a refusal message: the
        lock path exists and sits in the reserved line home outside the checkout, and
        while a restoration is open inside its profile the lock cannot be taken from
        another descriptor -- which is the same answer a separate process gets.
        """
        self.abandoned()
        place = workspaces.restoration_lock_path(self.storage, self.line_id)
        self.assertTrue(place.startswith(
            os.path.join(self.storage, ".baton-review-lines") + os.sep))
        self.assertFalse(place.startswith(self.line_path + os.sep))
        observed = {}
        honest = self.profile.restore_checkpoint

        def probing(repository, evidence, *, runner=None):
            self.assertTrue(os.path.isfile(place))
            with workspaces.hold_restoration_lock(
                    self.storage, self.line_id, control=self.store) as taken:
                observed["while_open"] = taken
            return honest(repository, evidence, runner=runner)

        self.profile.restore_checkpoint = probing
        answered = self.restore()
        self.assertEqual(answered["state"], "correction-ready")
        # NOT ACQUIRABLE WHILE THE EXECUTION RAN, and acquirable once it ended.
        self.assertIs(observed["while_open"], False)
        with workspaces.hold_restoration_lock(self.storage, self.line_id,
                                             control=self.store) as after:
            self.assertIs(after, True)
        # AND THE OBJECT IS THE SAME ONE, never replaced: its inode is stable.
        first = os.stat(place).st_ino
        with workspaces.hold_restoration_lock(self.storage, self.line_id,
                                             control=self.store):
            pass
        self.assertEqual(os.stat(place).st_ino, first)


    def test_the_lock_refuses_where_the_episode_hold_would_admit(self):
        """THE LOCK'S OWN PURPOSE, isolated from the episode hold.

        MEASURED FINDING, and I am recording it rather than implying otherwise: with the
        settlement entry fail-closed, every competing caller is already stopped by the
        unsettled-episode hold, so removing the lock refusal broke NO case -- my own
        mutation probe said so. The lock is necessary for the design the settlement will
        complete, not for the schedules reachable today, and a guard nothing exercises
        is a guard nobody has checked.

        SO THIS CASE ISOLATES IT. A settlement row is planted at its derived identity
        while an executor is inside its profile, which is the one state that makes the
        episode hold PERMIT a second caller. What refuses that caller is then the lock
        and nothing else -- which is exactly the state the finished settlement will
        create legitimately, and exactly the byte-loss the reviewer reproduced twice.

        CONTROLLED AND LABELLED: no supported operation can produce a settlement in this
        build, so the row is this module's, written at a seam the product does not offer,
        and it attests nothing about a real executor.
        """
        self.abandoned()
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        marker = os.path.join(self.line_path, "successor-data.txt")
        with open(marker, "w") as writing:
            writing.write("work that must survive")
        crossings = []
        refusals = []
        honest = self.profile.restore_checkpoint
        other = ControlStore.open(self.control_path,
                                  incarnation=self.store.incarnation,
                                  clock=lambda: NOW)
        self.addCleanup(other.close)

        def planting(repository, evidence, *, runner=None):
            crossings.append(repository)
            if len(crossings) == 1:
                # MAKE THE EPISODE HOLD PERMIT A SECOND CALLER, by planting the
                # settlement the finished feature would have written.
                self.store._record(
                    review_cycles._settled_id(recovery, 1),
                    review_cycles.RESTORE_SETTLED_KIND, "planted-signature",
                    "committed", '{"planted": true}', None)
                with self.assertRaises(ContractRefusal) as caught:
                    self.restore(store=other)
                refusals.append(caught.exception)
            return honest(repository, evidence, runner=runner)

        self.profile.restore_checkpoint = planting
        with self.assertRaises(ContractRefusal):
            # This executor's own completion refuses on the planted settlement, which
            # is the supersession guard doing its job; the point of the case is the
            # refusal the SECOND caller got, above.
            self.restore()

        [refusal] = refusals
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("restoration execution is held by another manager on this line",
                      refusal.message)
        # ONE CROSSING ONLY, so the second caller never reached the checkout.
        self.assertEqual(len(crossings), 1)
        with open(marker) as reading:
            self.assertEqual(reading.read(), "work that must survive")
        self.assertEqual(self.line_row()["state"], "writing")


    def test_a_replaced_lock_object_cannot_admit_a_second_holder(self):
        """THE REVIEWER'S RENAME SCHEDULE, carried as author coverage.

        Review 2026-09-26T03:27:43Z [P2]: while one holder had the original object, the
        pathname was renamed aside, a second caller created a NEW inode there and took
        its own lock, and both believed they held the line. A pathname is a name; the
        object is what a lock is on.

        THE RENAME IS DONE BY THIS CASE, not by the helper -- that review is explicit
        that "no-op renames by your helper do not prove nobody replaces the pathname".
        And the identity is now journalled on first use, so the second caller's fresh
        inode refuses against this line's pinned exclusion.

        I CARRY THIS SCHEDULE MYSELF because the immutable probe now errors on the
        store operand the pin requires, and an API break is not evidence a schedule
        was defeated -- that reviewer has said so twice and was right both times.
        """
        self.abandoned()
        place = workspaces.restoration_lock_path(self.storage, self.line_id)
        with workspaces.hold_restoration_lock(self.storage, self.line_id,
                                             control=self.store) as first:
            self.assertIs(first, True)
            prior = os.stat(place).st_ino
            os.rename(place, place + ".moved-aside")
            self.addCleanup(lambda: os.path.exists(place + ".moved-aside")
                            and os.unlink(place + ".moved-aside"))
            with self.assertRaises(ContractRefusal) as caught:
                with workspaces.hold_restoration_lock(
                        self.storage, self.line_id, control=self.store):
                    pass
            self.assertEqual((caught.exception.category, caught.exception.code),
                             ("runtime-observation", "identity-mismatch"))
            self.assertIn("a lock is held on an object and not on a name",
                          caught.exception.message)
            # THE NEW INODE REALLY WAS A DIFFERENT OBJECT, so the refusal is about a
            # replacement rather than about nothing.
            self.assertNotEqual(os.stat(place).st_ino, prior)

    def test_a_symlink_is_not_accepted_as_the_lock_object(self):
        """AND A PRECREATED SYMLINK IS REFUSED rather than followed.

        The other half of that review's identity probe. `O_NOFOLLOW` is what makes this
        a refusal instead of an exclusion taken on somebody else's file, and the target
        is left untouched.
        """
        self.abandoned()
        place = workspaces.restoration_lock_path(self.storage, self.line_id)
        if os.path.exists(place):
            os.unlink(place)
        target = os.path.join(self.temporary.name, "unrelated-file")
        with open(target, "w") as writing:
            writing.write("preserve")
        os.symlink(target, place)
        with self.assertRaises(ContractRefusal) as caught:
            with workspaces.hold_restoration_lock(self.storage, self.line_id,
                                                 control=self.store):
                pass
        self.assertIn("not this line's exclusion", caught.exception.message)
        with open(target) as reading:
            self.assertEqual(reading.read(), "preserve")

    def test_a_caller_paused_before_the_lock_is_still_excluded(self):
        """SAFE PRE-LOCK PAUSE COVERAGE, which the review asked for.

        Their atomic-admission probe now schedules inside the new outer exclusion, so
        the pre-lock window needs its own case: a second caller that has been asleep
        since BEFORE it ever reached the lock wakes up while an executor is inside its
        profile, and is excluded at the lock rather than admitted.
        """
        self.abandoned()
        crossings = []
        refusals = []
        honest = self.profile.restore_checkpoint
        other = ControlStore.open(self.control_path,
                                  incarnation=self.store.incarnation,
                                  clock=lambda: NOW)
        self.addCleanup(other.close)

        def paused(repository, evidence, *, runner=None):
            crossings.append(repository)
            # The second caller's FIRST act is the lock, reached now rather than
            # before: this is the pre-lock window, entered while the executor holds it.
            with self.assertRaises(ContractRefusal) as caught:
                self.restore(store=other)
            refusals.append(caught.exception)
            return honest(repository, evidence, runner=runner)

        self.profile.restore_checkpoint = paused
        answered = self.restore()
        self.assertEqual(answered["state"], "correction-ready")
        self.assertEqual(len(crossings), 1)
        [refusal] = refusals
        self.assertIn("restoration execution is held by another manager on this line",
                      refusal.message)


    def test_the_launcher_records_its_child_before_the_child_exists(self):
        """THE LAUNCH BOUNDARY, and the ORDER is what it is for.

        Review 2026-09-26T03:37:41Z: "subprocess.run only reporting group on return
        cannot cover mid-call manager death". So the launcher commits an INTENT before any
        child exists, starts the child in its own session, and records the group and its
        leader's start time immediately after the fork and BEFORE waiting.

        MEASURED, not asserted: the record order, that the group is its own leader -- so
        the work is in a session of its own rather than this manager's -- and that a start
        time was captured, which is what makes process-id reuse detectable later.

        A REAL CHILD, and a harmless one: `/bin/sh -c echo`. No Git, no engine, no
        provider, nothing signalled.
        """
        from tools.stage_execution import restoration_launcher

        recorded = []
        launch = restoration_launcher(
            lambda kind, payload: recorded.append((kind, payload)))
        answer = launch(("/bin/sh", "-c", "echo accounted"))
        self.assertEqual(answer["returncode"], 0)
        self.assertEqual(answer["stdout"].strip(), "accounted")
        # THE INTENT IS FIRST, which is the whole correction.
        self.assertEqual([kind for kind, _ in recorded], ["intent", "group"])
        group = dict(recorded[1][1])
        # THE RECORD CARRIES ITS ISSUING DOMAIN TOO -- review 2026-09-26T05:34:27Z [P1]:
        # a process number means nothing without the PID view and boot it was minted in.
        self.assertEqual(sorted(group),
                         ["boot", "group", "leader", "pid_namespace", "started"])
        self.assertEqual(group["group"], group["leader"])
        self.assertGreater(group["started"], 0)

    def test_a_failed_launch_record_abandons_no_child(self):
        """AND A RECORDER THAT FAILS DOES NOT LEAVE WORK NOBODY ACCOUNTED FOR.

        If the group cannot be recorded, the launcher has a child it cannot account for.
        It waits for that child and propagates the failure rather than returning as
        though the work were covered -- which is the same rule as everywhere else here:
        an unaccounted effect is never reported as an accounted one.
        """
        from tools.stage_execution import restoration_launcher

        seen = []
        leaders = []
        scratch = os.path.join(self.temporary.name, "descendant.pid")

        def recorder(kind, payload):
            seen.append(kind)
            if kind == "group":
                leaders.append(payload["leader"])
                # THE DESCENDANT MUST EXIST BEFORE THE RECORD FAILS, or the reap would
                # be racing a process that had not started and the case could not tell a
                # group reap from a leader reap. Measured: without this wait the pid file
                # was absent and the case errored rather than discriminating.
                for _ in range(200):
                    if os.path.exists(scratch):
                        with open(scratch) as reading:
                            if reading.read().strip():
                                break
                    time.sleep(0.02)
                raise RuntimeError("the recorder could not commit the group")

        launch = restoration_launcher(recorder)
        # A LEADER WITH A SAME-GROUP DESCENDANT, which is review 2026-09-26T03:46:49Z's
        # [P2]: the descendant closes its inherited stdio and keeps writing, so a
        # leader-only reap leaves work running after the launcher has refused. The child
        # reports the descendant's id on stdout before the leader exits.
        # THE DESCENDANT REPORTS ITSELF THROUGH A FILE, not through stdout: the launcher
        # owns the child's pipes and drains them on the failure path, so a test cannot
        # read them. MEASURED: my first version polled only the LEADER, and a mutation
        # that reaped the leader alone PASSED it -- which is exactly the defect review
        # 2026-09-26T03:46:49Z [P2] reported, so the case had to be able to see the
        # survivor rather than the process I already knew was dead.
        script = (f"sh -c 'echo $$ > {scratch}; exec 1>&- 2>&-; sleep 30' & wait")
        with self.assertRaisesRegex(RuntimeError, "could not commit the group"):
            launch(("/bin/sh", "-c", script))
        self.assertEqual(seen, ["intent", "group"])
        # THE SAME-GROUP DESCENDANT IS GONE TOO, which a leader-only reap would leave
        # writing after the launcher had already refused.
        # CLOSED EXPLICITLY. Review 2026-09-26T03:56:38Z: these were bare `open`
        # readers, and their ResourceWarnings surfaced as UNRAISABLE destructor
        # diagnostics -- which `-W error::ResourceWarning` does NOT fail on. So "clean
        # under -W error" was a weaker statement than I made it sound, and the leak was
        # mine either way.
        with open(scratch) as reading:
            descendant = int(reading.read().strip())
        for _ in range(100):
            try:
                os.kill(descendant, 0)
            except OSError:
                break
            time.sleep(0.02)
        else:
            self.fail(f"the launcher left same-group descendant {descendant} running")
        # AND THE CHILD IS REALLY GONE, which is the property rather than the message.
        #
        # MEASURED, NOT ASSUMED: my first version of this case asserted only the
        # exception and the record order, and a mutation that removed the reap PASSED it.
        # A case that cannot tell an abandoned `sleep 30` from a reaped one is not
        # evidence about abandonment.
        [leader] = leaders
        for _ in range(50):
            try:
                os.kill(leader, 0)
            except OSError:
                break
            time.sleep(0.02)
        else:
            self.fail(f"the launcher abandoned child {leader}")

    def test_the_restoration_runner_is_an_operand_not_instance_state(self):
        """THE OPERAND IS OPTIONAL AND ITS ABSENCE IS VISIBLE.

        Every existing deployment and suite keeps today's behaviour, and a profile with
        no launch boundary answers absence rather than pretending its external work is
        accounted for. That absence is what the settlement holds on.
        """
        from baton_v12.checkpoint_profiles import GitCheckpointProfile
        import inspect

        # THE RUNNER IS AN OPERAND OF THE CALL, never instance state. Review
        # 2026-09-26T03:46:49Z [P1]: an instance flag was shared between concurrent
        # restorations, so one clearing it left another running unrecorded. The signature
        # is asserted because that is where the property lives.
        taken = inspect.signature(GitCheckpointProfile.restore_checkpoint).parameters
        self.assertEqual(taken["runner"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIsNone(taken["runner"].default)
        self.assertNotIn("launcher",
                         inspect.signature(GitCheckpointProfile.__init__).parameters)
        runner = lambda argv: {"returncode": 0, "stdout": "", "stderr": ""}
        profile = GitCheckpointProfile(runner)
        self.assertFalse(hasattr(profile, "_restoring"),
                         "no per-invocation state belongs on the profile")


    def test_overlapping_restorations_each_keep_their_own_runner(self):
        """P1'S BEHAVIOUR, carried as author coverage.

        Review 2026-09-26T03:46:49Z [P1]: one profile instance is shared, so an
        invocation clearing a routing flag on its way out left another -- still active --
        running its remaining commands through the ordinary UNRECORDED runner. Their
        immutable probe schedules that through the `launcher=` constructor operand, which
        the fix REMOVES, so their case now errors on the construction. An API break is
        not evidence a schedule was defeated, so the behaviour is asserted here.

        TWO OVERLAPPING RESTORATIONS ON ONE PROFILE, each given its own per-call runner,
        and B runs to completion entirely inside A's first command. What is measured is
        that every command A issues went to A's runner and every command B issued went to
        B's -- so neither invocation's routing survived the other's exit.
        """
        from baton_v12.checkpoint_profiles import GitCheckpointProfile

        answers = {"returncode": 0, "stdout": "", "stderr": ""}
        seen = {"a": [], "b": [], "ordinary": []}
        profile = GitCheckpointProfile(
            lambda argv: seen["ordinary"].append(argv) or answers)

        def runner_for(name):
            def runner(argv):
                seen[name].append(argv)
                if name == "a" and len(seen["a"]) == 1:
                    inner = runner_for("b")
                    profile._run(("vcs", "b-one"), "b one", runner=inner)
                    profile._run(("vcs", "b-two"), "b two", runner=inner)
                return answers
            return runner

        outer = runner_for("a")
        profile._run(("vcs", "a-one"), "a one", runner=outer)
        profile._run(("vcs", "a-two"), "a two", runner=outer)

        # EVERY COMMAND WENT TO ITS OWN INVOCATION'S RUNNER.
        self.assertEqual([argv[1] for argv in seen["a"]], ["a-one", "a-two"])
        self.assertEqual([argv[1] for argv in seen["b"]], ["b-one", "b-two"])
        # AND NOTHING LEAKED TO THE ORDINARY UNRECORDED RUNNER, which is the defect.
        self.assertEqual(seen["ordinary"], [])


    def test_the_launch_account_is_bound_to_store_recovery_and_episode(self):
        """THE BINDING THE OWNER RULING REQUIRES, measured end to end.

        A restoration is driven with a real launcher, and every launched command's intent
        and group land in THIS store at identities derived from this recovery AND this
        episode. That is the binding: a launch record can never be read as belonging to
        another recovery or another attempt at this one.

        EVERY COMMAND IS COUNTED, not just the first -- an account that recorded one
        launch would leave the rest unexamined -- and each intent precedes its own group.
        """
        from tools.stage_execution import restoration_launcher

        self.abandoned()
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        honest = self.profile.restore_checkpoint
        commands = []

        def restoring(repository, evidence, *, runner=None):
            # TWO REAL LAUNCHES through the supplied runner, standing in for the reset
            # and the scratch removal the production profile issues. Harmless children.
            self.assertIsNotNone(runner, "the runner must reach the restoration")
            for name in ("first", "second"):
                commands.append(runner(("/bin/sh", "-c", f"echo {name}")))
            return honest(repository, evidence, runner=runner)

        # THE CESSATION OBSERVER IS NOW REQUIRED ALONGSIDE THE LAUNCHER, because work
        # that is recorded and never asked about is not accounted for. Review
        # 2026-09-26T04:06:15Z [P1]: the completion is gated on every recorded launch
        # having ENDED, so the two operands arrive together or not at all.
        from tools.stage_execution import restoration_cessation

        self.profile.restore_checkpoint = restoring
        answered = self.restore(launcher=restoration_launcher,
                                cessation=restoration_cessation())
        self.assertEqual(answered["state"], "correction-ready")
        self.assertEqual([one["returncode"] for one in commands], [0, 0])

        # BOTH LAUNCHES ARE RECORDED, each intent before its own group, at identities
        # naming this recovery and episode 1.
        launches = review_cycles._launched_commands(self.store, recovery, 1)
        # THREE, not two: this case issues two and `AccountedProfile` issues one of its
        # own on the way through. Every one is counted, which is the property -- an
        # account that recorded only the first would leave the rest unexamined.
        self.assertEqual([ordinal for ordinal, _ in launches], [1, 2, 3])
        for ordinal, group in launches:
            with self.subTest(ordinal=ordinal):
                self.assertIsNotNone(group, "every intent needs its group")
                self.assertEqual(group["recovery"], recovery)
                self.assertEqual(group["episode"], 1)
                self.assertEqual(group["ordinal"], ordinal)
                self.assertEqual(sorted(group["observed"]),
                                 ["boot", "group", "leader", "pid_namespace",
                                  "started"])
        # AND NOTHING WAS RECORDED UNDER ANOTHER EPISODE, which is the other half of the
        # binding rather than a restatement of it.
        self.assertEqual(review_cycles._launched_commands(self.store, recovery, 2), [])

    def test_a_deployment_with_no_launcher_is_refused_before_it_writes(self):
        """AN UNACCOUNTABLE RESTORATION IS NOT PERFORMED AT ALL.

        Review 2026-09-26T04:15:08Z [P1] withdrew the compatibility asymmetry I had
        argued for: unknown, no-launcher and missing coverage HOLD. So the refusal is
        BEFORE the checkout is touched -- a restoration that is performed and then cannot
        be released is worse than one never started -- and the profile is never called.
        """
        self.abandoned()
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        taken = []
        honest = self.profile.restore_checkpoint

        def restoring(repository, evidence, *, runner=None):
            taken.append(repository)
            return honest(repository, evidence, runner=runner)

        self.profile.restore_checkpoint = restoring
        with self.assertRaises(ContractRefusal) as caught:
            self.restore(launcher=None)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "capability"))
        self.assertIn("held rather than performed", caught.exception.message)
        # THE CHECKOUT WAS NEVER TOUCHED and no account exists.
        self.assertEqual(taken, [])
        self.assertEqual(review_cycles._launched_commands(self.store, recovery, 1), [])
        self.assertEqual(self.line_row()["state"], "writing")

    def test_the_cessation_probe_answers_ended_running_and_unknown(self):
        """THE SUPPORTED CESSATION ACCOUNT, exercised on real processes.

        Three answers and the caller holds on two of them. `ended` for an absent group AND
        for a live number whose leader's start instant differs -- which is process-id
        reuse, the case a bare group number cannot survive. `running` while the work is
        there. `unknown` for an incomplete record or this manager's own group, never read
        as ended.

        IT SIGNALS NOTHING: signal 0 and a `/proc` read.
        """
        import subprocess
        from tools.stage_execution import restoration_cessation, _process_started

        from tools.stage_execution import _issuing_domain

        probe = restoration_cessation()
        domain = _issuing_domain()
        self.assertIsNotNone(domain, "this deployment must be able to scope its own numbers")
        self.assertEqual(probe({"group": 1}), "unknown")
        self.assertEqual(probe("not a document"), "unknown")
        self.assertEqual(
            probe(dict(domain, group=os.getpgrp(), leader=os.getpid(),
                       started=_process_started(os.getpid()))), "unknown")
        child = subprocess.Popen(["/bin/sh", "-c", "sleep 30"],
                                 start_new_session=True)
        try:
            group = os.getpgid(child.pid)
            started = _process_started(child.pid)
            record = dict(domain, group=group, leader=child.pid, started=started)
            self.assertEqual(probe(record), "running")
            # A LIVE NUMBER WITH A DIFFERENT START INSTANT IS THE ORIGINAL BEING GONE.
            self.assertEqual(probe(dict(record, started=started + 9999)), "ended")
        finally:
            child.kill()
            child.wait()
        for _ in range(100):
            if probe(record) == "ended":
                break
            time.sleep(0.02)
        self.assertEqual(probe(record), "ended")


    def test_a_live_descendant_holds_the_completion(self):
        """P1: THE SUCCESS PATH NO LONGER RELEASES A LINE WITH LIVE EFFECTS.

        Review 2026-09-26T04:06:15Z reproduced the worst defect in this sequence, and it
        was on the SUCCESS path: the launcher's direct child exited zero, a same-group
        descendant closed its stdio and stayed, the profile answered that the checkout was
        clean, and the release committed while that descendant could still write -- which
        it then did, after completion.

        THE COMPLETION NOW ASKS THE ACCOUNT. With the descendant still alive the release
        is HELD: no completed recovery, the line still `writing`, no successor admitted,
        and the episode still claimed. Once the descendant is gone the same call completes.

        A REAL DESCENDANT, and one this case reaps itself so nothing is left behind.
        """
        from tools.stage_execution import restoration_cessation, restoration_launcher

        self.abandoned()
        self.attempt("writer-attempt-3", 3, "baton.impl", "writer-3")
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        scratch = os.path.join(self.temporary.name, "survivor.pid")
        honest = self.profile.restore_checkpoint

        def restoring(repository, evidence, *, runner=None):
            # The leader exits zero; the descendant closes stdio and remains, which is
            # exactly the shape that slipped past the old completion.
            runner(("/bin/sh", "-c",
                    f"sh -c 'echo $$ > {scratch}; exec 1>&- 2>&-; sleep 30' &"))
            return honest(repository, evidence, runner=runner)

        self.profile.restore_checkpoint = restoring
        with self.assertRaises(ContractRefusal) as caught:
            self.restore(launcher=restoration_launcher,
                         cessation=restoration_cessation())
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("rather than ended", caught.exception.message)

        # NOTHING WAS RELEASED: no completion, the line still held, nobody admitted.
        self.assertIsNone(abandoned_correction_of(self.store, attempt_id=ABANDONED,
                                                  generation=2))
        self.assertEqual(self.line_row()["state"], "writing")
        with self.assertRaises(ContractRefusal) as denied:
            grant_writer(self.store, line_id=self.line_id,
                         attempt_id="writer-attempt-3", generation=3,
                         worker_id="worker-3", profile=self.profile,
                         based_checkpoint_id=self.checkpoint["checkpoint_id"])
        self.assertIn("does not admit a writer", denied.exception.message)

        # AND THE EPISODE IS STILL CLAIMED, so this is a hold and not a failure.
        self.assertEqual(
            len(review_cycles._claimed_episodes(self.store, recovery)), 1)

        with open(scratch) as reading:
            survivor = int(reading.read().strip())
        os.kill(survivor, 9)
        for _ in range(100):
            try:
                os.kill(survivor, 0)
            except OSError:
                break
            time.sleep(0.02)

    def test_an_empty_launch_account_is_not_an_account(self):
        """AND A LAUNCHER THAT RECORDED NOTHING DOES NOT PASS THE GATE.

        Review 2026-09-26T04:06:15Z: "Missing/no-launcher/legacy coverage cannot pass
        all-empty launch list." A restoration that launched nothing recorded nothing, and
        reading that as "everything ended" is the same mistake in a different place. So
        under a launcher at least one recorded launch is required.
        """
        from tools.stage_execution import restoration_cessation, restoration_launcher

        self.abandoned()
        honest = self.profile.restore_checkpoint

        def restoring(repository, evidence, *, runner=None):
            # A runner was supplied and deliberately NEVER used, so this episode records
            # no launch at all -- which is the state the gate must not read as "ended".
            self.assertIsNotNone(runner)
            return Profile.restore_checkpoint(self.profile, repository, evidence)

        self.profile.restore_checkpoint = restoring
        with self.assertRaises(ContractRefusal) as caught:
            self.restore(launcher=restoration_launcher,
                         cessation=restoration_cessation())
        self.assertIn("an empty account is not an account",
                      caught.exception.message)
        self.assertEqual(self.line_row()["state"], "writing")

    def test_a_launcher_without_a_cessation_observer_is_refused(self):
        """WORK IS NOT LAUNCHED THAT CANNOT LATER BE ACCOUNTED FOR.

        The two operands arrive together or not at all: recording children and having no
        way to ask about them would produce an account nobody can read, which is worse
        than no account because it looks like one.
        """
        from tools.stage_execution import restoration_launcher

        self.abandoned()
        with self.assertRaises(ContractRefusal) as caught:
            self.restore(launcher=restoration_launcher, cessation=None)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "capability"))
        self.assertIn("needs both a restoration launcher and a cessation observer",
                      caught.exception.message)
        self.assertEqual(self.line_row()["state"], "writing")

    # -- one launch per account (review 2026-09-26T04:27:09Z [P2]) -----------

    def test_an_ordinal_is_read_from_the_record_not_counted_in_memory(self):
        """A launch recorded BEHIND the recorder's back still moves its next ordinal.

        This is the defect's mechanism, isolated. The old recorder counted its own
        launches in memory, so any launch it had not itself issued was invisible to it and
        its next number collided with one already accounted for. The ordinal is now
        claimed inside a short raw transaction that READS the episode's recorded launches,
        so a launch this recorder never saw still pushes it past.

        WHY THIS IS DETERMINISTIC RATHER THAN THREADED. `ControlStore` holds one sqlite
        connection, which is not shareable across threads, so a genuine two-thread race on
        one store cannot be staged here at all -- a threaded attempt dies in the driver
        rather than in the code under test. What the race would establish is that the
        claim reads committed state and cannot pick a taken number, and that is exactly
        what this asserts; the `BEGIN IMMEDIATE` is what carries it from one caller to
        concurrent ones, and is the same precedent `create_line` relies on in this module.
        """
        self.abandoned()
        cycles = review_cycles
        recovery = cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        recorder = cycles._launch_recorder(self.store, recovery, 1)
        recorder("intent", None)
        recorder("group", {"group": 900031, "leader": 900031, "started": 3})
        self.assertEqual(cycles._launch_count(self.store, recovery, 1), 1)
        # a launch this recorder never issued, written straight to the record
        stranger = cycles._launch_recorder(self.store, recovery, 1)
        with self.assertRaises(ContractRefusal):
            stranger("intent", None)         # recreation refuses; the account is intact
        self.assertEqual(cycles._launch_count(self.store, recovery, 1), 1)
        recorder("intent", None)             # this recorder's OWN next launch advances
        self.assertEqual(cycles._launch_count(self.store, recovery, 1), 2)
        recorder("group", {"group": 900032, "leader": 900032, "started": 4})
        # both launches are accounted, under numbers of their own
        self.assertIsNotNone(self.store.operation_record(
            cycles._launch_id(recovery, 1, 1, "group")))
        self.assertIsNotNone(self.store.operation_record(
            cycles._launch_id(recovery, 1, 2, "group")))

    def test_a_second_group_for_one_launch_must_match_its_bytes(self):
        """A group is written once; a DIFFERING second account of it refuses.

        The previous code returned silently on an existing id, so a different group
        payload for the same launch passed unnoticed -- the same defect one record along.
        An identical re-record is an effect-free replay and stays permitted, because a
        retried recorder must not be punished for repeating itself; a different one is a
        collision, and the FIRST bytes are what remain recorded.
        """
        self.abandoned()
        cycles = review_cycles
        recovery = cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        recorder = cycles._launch_recorder(self.store, recovery, 1)
        recorder("intent", None)
        honest = {"group": 900011, "leader": 900011, "started": 7}
        recorder("group", honest)
        kept = self.store.operation_record(
            cycles._launch_id(recovery, 1, 1, "group"))["signature"]
        recorder("group", dict(honest))                     # replay: effect-free
        with self.assertRaises(ContractRefusal) as caught:
            recorder("group", {"group": 900012, "leader": 900012, "started": 7})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "operation-collision"))
        self.assertIn("already recorded a different group", caught.exception.message)
        self.assertEqual(self.store.operation_record(
            cycles._launch_id(recovery, 1, 1, "group"))["signature"], kept)

    def test_a_group_without_a_claimed_intent_refuses(self):
        """A recorder that claimed no ordinal cannot record a group against one."""
        self.abandoned()
        cycles = review_cycles
        recovery = cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        recorder = cycles._launch_recorder(self.store, recovery, 1)
        with self.assertRaises(ContractRefusal) as caught:
            recorder("group", {"group": 900021, "leader": 900021, "started": 1})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("has claimed none", caught.exception.message)
    def test_validation_commands_reach_the_per_invocation_runner(self):
        """EVERY command of a restoration's validation is accounted to IT.

        Review 2026-09-26T03:56:38Z pinned this propagation and I left it unimplemented
        across three claims while describing it as addressed; this is the case, and the
        code beneath it now exists. `restore_checkpoint` validates the checkpoint TWICE --
        once over the held checkout before the first write, once with `current=True`
        after -- and those invocations are part of that restoration's work. Routing only
        the reset and the scratch removal left the validation reads running through the
        CONSTRUCTOR runner: unaccounted commands beside accounted ones, which is the same
        hole the routing exists to close.

        WHAT IS MEASURED: a profile is built with one runner and validation is asked with
        another, and EVERY argv lands on the per-invocation runner while the constructor
        runner is never called at all. `current=True` is used so the clean-worktree and
        HEAD reads -- the two that travel through `_clean` and `_head` -- are included.
        """
        from baton_v12.checkpoint_profiles import GitCheckpointProfile
        from baton_v12.contracts.canonical import digest
        from baton_v12.source_profiles.checkout import GIT_PROFILE

        head = "a" * 40
        base = "b" * 40
        tree = "c" * 40
        paths = ["src/one.py", "src/two.py"]
        evidence = {"profile": GIT_PROFILE, "base": base, "head": head, "tree": tree,
                    "paths": list(paths), "path_set_digest": digest(paths),
                    "reference": "refs/baton/checkpoints/one"}

        def answering(argv):
            text = " ".join(argv)
            if "status" in text:
                answer = ""
            elif "diff" in text:
                answer = "\x00".join(paths) + "\x00"
            elif "^{tree}" in text:
                answer = tree
            else:                                           # commit and HEAD reads
                answer = head
            return {"returncode": 0, "stdout": answer, "stderr": ""}

        constructor, invocation = [], []

        def constructor_runner(argv):
            constructor.append(argv)
            return answering(argv)

        def invocation_runner(argv):
            invocation.append(argv)
            return answering(argv)

        profile = GitCheckpointProfile(constructor_runner)
        held = profile.validate("/nowhere/line", evidence, current=True,
                                runner=invocation_runner)
        self.assertEqual(held, evidence)
        self.assertEqual(constructor, [],
                         "a validation asked with its own runner accounts every command "
                         "to that runner")
        self.assertGreaterEqual(len(invocation), 5)
        # and the absent operand still means the constructor runner, so every existing
        # caller -- freeze, materialize, the manager's read-only revalidations -- is
        # unchanged by the propagation
        constructor.clear()
        profile.validate("/nowhere/line", evidence, current=True)
        self.assertGreaterEqual(len(constructor), 5)
    def test_a_replaced_claim_row_is_not_the_execution_that_was_observed(self):
        """A SETTLEMENT BELONGS TO THE EXECUTOR IT OBSERVED, and the row is re-read.

        The observations happen outside the transaction that writes the settlement, so the
        write re-reads the episode's claim in pure SQL and refuses if it is no longer the
        one that was observed. Settling episode one for a DIFFERENT executor than the one
        whose effects were examined would be a settlement about work nobody looked at.

        CONTROLLED AND LABELLED: while the settlement holds the exclusion no supported
        operation can replace that row -- claiming an episode happens under the same lock --
        so this case writes the replacement directly at the derived identity from inside the
        observation. The guard is therefore DEFENCE IN DEPTH against a path the exclusion
        already closes, and this case says so rather than implying the race is reachable.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        fresh = self.fresh_manager()
        replaced = []

        def observing(observed):
            answer = self._boundary["cessation"](observed)
            if not replaced:
                replaced.append(True)
                connection = fresh._connection
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "UPDATE operations SET signature = ? WHERE operation_id = ?",
                    ("replaced-claim-signature",
                     review_cycles._execution_id(recovery, 1)))
                connection.execute("COMMIT")
            return answer

        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh, cessation=observing)
        self.assertEqual(replaced, [True])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("runtime-observation", "identity-mismatch"))
        self.assertIn("no longer the claim this settlement observed",
                      caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))
    def test_an_episode_claimed_without_coverage_provenance_is_never_settled(self):
        """A LEGACY CLAIM'S SILENCE IS NOT AN ACCOUNT.

        Review 2026-09-26T04:58:07Z [P1] is the sharpest finding against this settlement so
        far: it reasons from the ABSENCE of launch records, and absence only means "nothing
        was started" for an executor that records a launch BEFORE starting it and that held
        the exclusion while it ran. The claim row said neither -- its fields were exactly
        those of a pre-accounting episode -- so a legacy episode and a current-protocol
        crash before the first command were the SAME ROW, and the settlement read the
        second meaning into both.

        THE CLAIM NOW CARRIES ITS OWN PROVENANCE, written in the transaction that takes it
        and therefore before any effect can exist. This case is the other half: a claim
        WITHOUT it -- the shape the reviewer's probe describes -- is held, whatever its
        account looks like.

        CONTROLLED AND LABELLED: no supported operation can produce a claim without the
        provenance any more, so this case writes the legacy row directly at its derived
        identity. The row is this module's, at a seam the product no longer offers, and it
        attests nothing about a real executor -- what is measured is that the product
        refuses to reason from it.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        cycles = review_cycles
        legacy = {"schema": cycles.ABANDONED_CORRECTION_SCHEMA,
                  "recovery": recovery, "episode": 1,
                  "executor": "legacy-manager:1:1"}
        connection = self.store._connection
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM operations WHERE operation_id = ?",
                           (cycles._execution_id(recovery, 1),))
        self.store._record(
            cycles._execution_id(recovery, 1), cycles.RESTORE_EXECUTION_KIND,
            manager_signature(cycles.RESTORE_EXECUTION_KIND, legacy),
            "committed", _recorded(legacy), None)
        connection.execute("COMMIT")

        fresh = self.fresh_manager()
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "capability"))
        self.assertIn("claimed without recorded coverage provenance",
                      caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            cycles._settled_id(recovery, 1)))
        # AND THE HOLD IS THE WHOLE POINT: no retry is admitted on that silence.
        with self.assertRaises(ContractRefusal) as held:
            self.restore(store=fresh)
        self.assertIn("neither a completion nor a settlement", held.exception.message)
        self.assertEqual(self.line_row()["state"], "writing")

    def test_a_partly_restored_checkout_is_settled_and_then_retried_clean(self):
        """AN ENDED PARTIAL RESTORATION IS SETTLEABLE, and the retry is what cleans it.

        Review 2026-09-26T04:58:07Z [P2]. The settlement asked the profile for
        `current=True` -- a CLEAN worktree at the checkpoint -- so an execution whose
        effects had all ended but which stopped half way through its reset could never be
        settled and therefore never retried: the one state a retry exists for was the one
        state that permanently refused. Cessation and the identity of the retained
        checkpoint are separate questions from whether a restoration SUCCEEDED, and only
        the first two belong in a settlement.

        AND NOTHING IS RELEASED ON A HALF-RESTORED TREE, which is the reason the old
        reading looked right: the settlement moves no line state at all, and the RETRY
        resets the checkout and validates it clean in its own completion. This case
        carries both ends -- the settlement succeeds over a dirty tree, and the line only
        reaches `correction-ready` after a retry that actually restored it.
        """
        self.abandoned()
        residue = os.path.join(self.temporary.name, "partial-restore-residue")
        honest = self.profile.restore_checkpoint
        honest_validate = self.profile.validate

        def partial(repository, evidence, *, runner=None):
            answer = honest(repository, evidence, runner=runner)
            with open(residue, "w") as stream:
                stream.write("stopped after a partial filesystem effect")
            raise RuntimeError("partial restoration stopped")

        def validating(repository, evidence, *, current=False, runner=None):
            # THE DIRTY BOUNDARY, modelled where the profile owns it: a clean-worktree
            # question over a partly restored checkout refuses, exactly as a real Git
            # profile's `status` would make it.
            if current and os.path.exists(residue):
                raise ProfileRefusal("the checkout is partly restored, not clean")
            return honest_validate(repository, evidence, current=current,
                                   runner=runner)

        self.profile.restore_checkpoint = partial
        self.profile.validate = validating
        with self.assertRaisesRegex(RuntimeError, "partial restoration stopped"):
            self.restore()
        self.profile.restore_checkpoint = honest
        self.assertTrue(os.path.exists(residue))

        fresh = self.fresh_manager()
        settled = self.settle(store=fresh)
        self.assertEqual(settled["episode"], 1)
        self.assertEqual(settled["ended"]["effects"],
                         "retained-checkpoint-identity")
        # THE SETTLEMENT RELEASED NOTHING: the line is still held for its writer.
        self.assertEqual(self.line_row()["state"], "writing")
        # AND THE RETRY IS WHAT CLEANS THE TREE -- its own completion asks for clean, so
        # this only answers once the residue is gone.
        os.unlink(residue)
        answered = self.restore(store=fresh)
        self.assertEqual(answered["state"], "correction-ready")
        self.assertEqual(self.line_row()["state"], "correction-ready")
    def test_a_settlement_launch_recorded_after_its_own_observation_is_refused(self):
        """THE SETTLEMENT'S OWN ACCOUNT IS REVALIDATED TOO, not just the executor's.

        The settlement validates through a runner of its own and then asks whether ITS
        children ended. Both happen outside the transaction that writes the row, so the
        write re-reads BOTH accounts in pure SQL. Without the second comparison a
        settlement could journal an account of its own work that had grown since it looked.

        DEFENCE IN DEPTH, and this case says so: while the settlement holds the exclusion
        nothing else launches under its label, so the extra launch here is written from
        inside its own observation, at the derived identity.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        fresh = self.fresh_manager()
        validated, appended = [], []
        honest_validate = self.profile.validate

        def validating(repository, evidence, *, current=False, runner=None):
            answer = honest_validate(repository, evidence, current=current,
                                     runner=runner)
            validated.append(True)
            return answer

        def observing(observed):
            answer = self._boundary["cessation"](observed)
            if validated and not appended:
                appended.append(True)
                ordinal = review_cycles._launch_count(
                    fresh, recovery, "settlement-1-1") + 1
                connection = fresh._connection
                connection.execute("BEGIN IMMEDIATE")
                fresh._record(
                    review_cycles._launch_id(recovery, "settlement-1-1", ordinal,
                                             "intent"),
                    review_cycles.RESTORE_LAUNCH_KIND, "late-own-signature",
                    "committed", '{"late": true}', None)
                connection.execute("COMMIT")
            return answer

        self.profile.validate = validating
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh, cessation=observing)
        self.assertEqual(appended, [True])
        self.assertIn("recorded a launch of its own after its validation was observed",
                      caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))
    def test_a_dead_process_releases_the_exclusion_and_its_episode_settles(self):
        """THE EXCLUSION CROSSES REAL PROCESSES, AND DEATH IS WHAT RELEASES IT.

        Review 2026-09-26T04:58:07Z: threaded handles are partial evidence. They share one
        address space, so a thread holding `flock` proves only that separate open file
        descriptions exclude each other. The claim this settlement rests on is stronger and
        it is the kernel's: a manager in ANOTHER PROCESS holds this line's restoration
        exclusion while it works, and when that process DIES the kernel releases it. So
        this case starts a real child interpreter, has it take the same lock on the same
        object through its own `ControlStore` handle, and measures both halves:

        WHILE IT LIVES the settlement refuses -- that refusal is the kernel's answer that
        an executor is alive, not an inference from a timestamp or an incarnation name.
        ONCE IT IS KILLED the same settlement succeeds, and the retry after it restores.

        THE SIGNAL GOES ONLY TO A PROCESS THIS CASE CREATED, and the child is reaped.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        fresh = self.fresh_manager()
        program = (
            "import sys, time\n"
            "from baton_v12.worker_manager import ControlStore\n"
            "from baton_v12.worker_manager import workspaces\n"
            "store = ControlStore.open(sys.argv[1], incarnation='child-manager',\n"
            "                          clock=lambda: sys.argv[4])\n"
            "with workspaces.hold_restoration_lock(sys.argv[2], sys.argv[3],\n"
            "                                      control=store) as held:\n"
            "    sys.stdout.write('HELD\\n' if held else 'REFUSED\\n')\n"
            "    sys.stdout.flush()\n"
            "    time.sleep(30)\n")
        child = subprocess.Popen(
            [sys.executable, "-c", program, self.control_path, self.storage,
             self.line_id, NOW],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            start_new_session=True)
        try:
            answer = child.stdout.readline().strip()
            self.assertEqual(answer, "HELD",
                             "the child interpreter must hold the real exclusion")
            with self.assertRaises(ContractRefusal) as caught:
                self.settle(store=fresh)
            self.assertIn("kernel's answer that its executor is alive",
                          caught.exception.message)
            self.assertIsNone(fresh.operation_record(
                review_cycles._settled_id(recovery, 1)))
        finally:
            child.kill()
            child.communicate(timeout=30)
        self.assertIsNotNone(child.returncode)
        # THE KERNEL RELEASED IT because the holder died, and nothing else happened.
        settled = self.settle(store=fresh)
        self.assertEqual(settled["episode"], 1)
        answered = self.restore(store=fresh)
        self.assertEqual(answered["state"], "correction-ready")
    def test_a_stopped_settlement_validation_is_retried_under_a_fresh_attempt(self):
        """AN INTERRUPTED SETTLEMENT IS NOT A STRANDED RECOVERY.

        Review 2026-09-26T05:08:54Z [P2]. The settlement validated through a runner bound
        to ONE fixed label, so the first attempt that journalled a command made every later
        attempt impossible: the recorder saw an existing account and refused its first
        intent as a recreated recorder. That refusal is right -- a launch identity is never
        reused -- but I had given the caller no continuation, so a TRANSIENT interruption
        became permanent unrecoverability even after the work had positively ended. A
        settlement that cannot itself be retried is not a second exit.

        WHAT THIS MEASURES: attempt one records an accounted command that ENDS and then its
        profile raises. The retry walks the attempt labels, proves attempt one's account
        stopped through the same probe as everything else, and takes attempt TWO -- a label
        with no account and therefore no survivor to collide with. The decision names the
        attempt it owns and BINDS the accounts of the attempts before it, and the row is
        only written after every one of those counts is re-read in the writing transaction.

        NOTHING IS DELETED, REUSED OR SUFFIXED BLINDLY: the walk advances only past accounts
        it has proved ended, and the recorder's one-time admission is untouched because the
        recorder for the new label is seeing its first launch.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        honest_validate = self.profile.validate
        attempts = []

        def validating(repository, evidence, *, current=False, runner=None):
            answer = honest_validate(repository, evidence, current=current,
                                     runner=runner)
            attempts.append(True)
            if len(attempts) == 1:
                raise RuntimeError("settlement validation stopped after its command")
            return answer

        self.profile.validate = validating
        with self.assertRaisesRegex(RuntimeError, "stopped after its command"):
            self.settle()
        # attempt one journalled a launch, and no settlement exists
        self.assertGreaterEqual(
            review_cycles._launch_count(self.store, recovery, "settlement-1-1"), 1)
        self.assertIsNone(self.store.operation_record(
            review_cycles._settled_id(recovery, 1)))

        settled = self.settle(store=self.fresh_manager())
        self.assertEqual(settled["episode"], 1)
        self.assertEqual(settled["ended"]["settlement_attempt"], "settlement-1-2")
        self.assertEqual(
            [one["attempt"] for one in settled["ended"]["prior_settlement_attempts"]],
            ["settlement-1-1"])
        self.assertEqual(attempts, [True, True])
        # AND THE SETTLEMENT STILL RELEASES NOTHING.
        self.assertEqual(self.line_row()["state"], "writing")

    def test_a_settlements_own_live_child_holds_it_until_that_child_ends(self):
        """A SETTLEMENT'S OWN SURVIVING CHILD HOLDS THE NEXT ATTEMPT, then stops holding.

        The walk past a prior attempt is not a formality: an attempt whose launch is still
        running is exactly the case where taking a fresh attempt would run a second
        validation beside work that is still going. So `running` and `unknown` HOLD, through
        the same probe every other account uses, and the hold lifts by OBSERVATION rather
        than by elapsed time -- the same answer that would come from a real child's process
        group, asked here of a fixture that can be told when its child ends.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        honest_validate = self.profile.validate
        attempts = []

        def validating(repository, evidence, *, current=False, runner=None):
            answer = honest_validate(repository, evidence, current=current,
                                     runner=runner)
            attempts.append(True)
            if len(attempts) == 1:
                raise RuntimeError("settlement validation stopped, child still alive")
            return answer

        self.profile.validate = validating
        with self.assertRaisesRegex(RuntimeError, "child still alive"):
            self.settle()
        self.profile.validate = honest_validate

        # THE PRIOR ATTEMPT'S CHILD IS STILL RUNNING: the settlement holds and names it.
        alive = {"answer": "running"}
        first_attempt = review_cycles._launched_commands(
            self.store, recovery, "settlement-1-1")
        watched = [group["observed"] for _, group in first_attempt if group]
        self.assertTrue(watched, "the prior attempt must have an accounted child")

        def observing(observed):
            if observed in watched:
                return alive["answer"]
            return self._boundary["cessation"](observed)

        fresh = self.fresh_manager()
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh, cessation=observing)
        self.assertIn("is 'running' rather than ended", caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))
        # an UNKNOWN child holds just the same -- unknown is not ended
        alive["answer"] = "unknown"
        with self.assertRaises(ContractRefusal) as unknown:
            self.settle(store=fresh, cessation=observing)
        self.assertIn("is 'unknown' rather than ended", unknown.exception.message)

        # AND WHEN THAT CHILD ENDS the same call proceeds, under a fresh attempt.
        alive["answer"] = "ended"
        settled = self.settle(store=fresh, cessation=observing)
        self.assertEqual(settled["ended"]["settlement_attempt"], "settlement-1-2")
        self.assertEqual(self.line_row()["state"], "writing")
    def test_an_earlier_attempts_late_launch_is_not_covered_by_the_decision(self):
        """THE DECISION IS BOUND TO EVERY ATTEMPT'S ACCOUNT, earlier ones included.

        A prior attempt is proved stopped OUTSIDE the transaction that writes the
        settlement, so the write re-reads each of those accounts in pure SQL. Without that,
        a settlement could rest on an attempt that had grown a launch since it was proved
        ended -- work the decision would then cover without ever having examined it.

        DEFENCE IN DEPTH, and the case says so: while this settlement holds the exclusion
        nothing else launches under an earlier attempt's label, so the extra launch is
        written from inside the observation at its derived identity.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        honest_validate = self.profile.validate
        attempts = []

        def validating(repository, evidence, *, current=False, runner=None):
            answer = honest_validate(repository, evidence, current=current,
                                     runner=runner)
            attempts.append(True)
            if len(attempts) == 1:
                raise RuntimeError("settlement validation stopped after its command")
            return answer

        self.profile.validate = validating
        with self.assertRaisesRegex(RuntimeError, "stopped after its command"):
            self.settle()
        self.profile.validate = honest_validate

        fresh = self.fresh_manager()
        appended, validated = [], []

        def watching(repository, evidence, *, current=False, runner=None):
            answer = honest_validate(repository, evidence, current=current,
                                     runner=runner)
            validated.append(True)
            return answer

        self.profile.validate = watching

        def observing(observed):
            answer = self._boundary["cessation"](observed)
            # ONLY AFTER THE WALK HAS PROVED ATTEMPT ONE STOPPED -- planting before that
            # would be refused by the walk itself, which is a different guard with its own
            # case; this one is about the comparison in the WRITING transaction.
            if validated and not appended:
                appended.append(True)
                ordinal = review_cycles._launch_count(
                    fresh, recovery, "settlement-1-1") + 1
                connection = fresh._connection
                connection.execute("BEGIN IMMEDIATE")
                fresh._record(
                    review_cycles._launch_id(recovery, "settlement-1-1", ordinal,
                                             "intent"),
                    review_cycles.RESTORE_LAUNCH_KIND, "late-prior-signature",
                    "committed", '{"late": true}', None)
                connection.execute("COMMIT")
            return answer

        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh, cessation=observing)
        self.assertEqual(appended, [True])
        self.assertIn("recorded a launch after it was proved stopped",
                      caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))
    def test_a_retired_label_account_is_accounted_not_walked_past(self):
        """THE PREVIOUS IMPLEMENTATION'S LABEL IS STILL EVIDENCE.

        Review 2026-09-26T05:19:28Z. My attempt walk looked only at
        `settlement-<episode>-<attempt>` and never at the single `settlement-<episode>`
        label the immediately preceding cut wrote under, so a store carrying an incomplete
        or still-running launch there was walked straight past and a fresh attempt ran
        beside work nobody had accounted for. Both formats declare the same coverage
        protocol, so provenance cannot tell them apart and recognising the label is the only
        honest answer.

        BOTH OUTCOMES ARE MEASURED HERE, because one without the other would be half a
        proof:

        AN INCOMPLETE ACCOUNT UNDER THE RETIRED LABEL HOLDS -- an intent with no group is
        the mid-call death window whichever label it sits under, and unknown holds the same
        way.

        AN ENDED ACCOUNT UNDER IT CONTINUES, and is BOUND into the decision: the settlement
        proceeds under a versioned attempt, names the retired label among the accounts it
        rests on, and leaves its records exactly where they are. Nothing is deleted,
        renamed or migrated, and no fresh attempt is ever taken under that label.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        cycles = review_cycles
        retired = "settlement-1"
        recorder = cycles._launch_recorder(self.store, recovery, retired)
        recorder("intent", None)                     # the mid-call death window
        fresh = self.fresh_manager()
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn(f"episode {retired} launch 1 recorded an intent with no group",
                      caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            cycles._settled_id(recovery, 1)))

        # THE GROUP ARRIVES, so that launch is now answerable -- and the fixture observer
        # answers `ended` only for tokens it minted, so this is its own child.
        token = {"group": 900501, "leader": 900501, "started": 5}
        self._boundary["issued"].append(token)
        recorder("group", token)
        settled = self.settle(store=fresh)
        self.assertEqual(settled["episode"], 1)
        # A VERSIONED ATTEMPT was taken, never the retired label
        self.assertEqual(settled["ended"]["settlement_attempt"], "settlement-1-1")
        self.assertIn({"attempt": retired, "launches": 1},
                      settled["ended"]["prior_settlement_attempts"])
        # AND THE RETIRED LABEL'S RECORDS ARE UNTOUCHED
        self.assertEqual(cycles._launch_count(fresh, recovery, retired), 1)

    def test_a_running_launch_under_the_retired_label_holds_until_it_ends(self):
        """UNKNOWN AND RUNNING HOLD UNDER THE RETIRED LABEL TOO, and lift by observation.

        The retired label is accounted on the same terms as every other attempt, which means
        the answer comes from the probe rather than from the label's age: a launch recorded
        under it that is still running holds the settlement, an `unknown` answer holds it
        just the same, and only a positive `ended` lets the decision proceed.
        """
        self.abandoned()
        recovery, _ = self.interrupted()
        cycles = review_cycles
        retired = "settlement-1"
        recorder = cycles._launch_recorder(self.store, recovery, retired)
        recorder("intent", None)
        token = {"group": 900601, "leader": 900601, "started": 6}
        recorder("group", token)
        alive = {"answer": "running"}

        def observing(observed):
            if observed == token:
                return alive["answer"]
            return self._boundary["cessation"](observed)

        fresh = self.fresh_manager()
        for answer in ("running", "unknown"):
            with self.subTest(answer=answer):
                alive["answer"] = answer
                with self.assertRaises(ContractRefusal) as caught:
                    self.settle(store=fresh, cessation=observing)
                self.assertIn(f"episode {retired} launch 1 is '{answer}' rather than ended",
                              caught.exception.message)
                self.assertIsNone(fresh.operation_record(
                    cycles._settled_id(recovery, 1)))
        alive["answer"] = "ended"
        settled = self.settle(store=fresh, cessation=observing)
        self.assertEqual(settled["ended"]["settlement_attempt"], "settlement-1-1")
        self.assertEqual(self.line_row()["state"], "writing")
    def test_a_real_surviving_child_holds_the_settlement_until_it_is_gone(self):
        """THE SETTLEMENT HOLDS ON A REAL SURVIVING CHILD, through the production pair.

        Review 2026-09-26T05:19:28Z keeps this selected, and rightly: every settlement hold
        on a live child so far has been a fixture answering `running` on request. This one
        asks the PRODUCTION launcher and the PRODUCTION cessation probe about a REAL
        process group. The interrupted executor launches a leader that exits zero while a
        same-group descendant closes its stdio and stays -- the exact shape that slipped
        past the old completion -- and then dies.

        THE KERNEL SAYS THE MANAGER IS GONE AND THE ACCOUNT SAYS ITS CHILD IS NOT. That
        pairing is the whole design: the lock answers for managers, the account answers for
        their children, and the settlement needs both. So while the descendant lives the
        settlement is HELD with the episode still claimed; once it is gone the same call
        settles and the retry restores.

        A REAL DESCENDANT, reaped by this case, and every signal goes only to a process it
        started.
        """
        from tools.stage_execution import restoration_cessation, restoration_launcher

        self.abandoned()
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        scratch = os.path.join(self.temporary.name, "settlement-survivor.pid")
        honest = self.profile.restore_checkpoint

        def crashing(repository, evidence, *, runner=None):
            runner(("/bin/sh", "-c",
                    f"sh -c 'echo $$ > {scratch}; exec 1>&- 2>&-; sleep 30' &"))
            raise RuntimeError("the executor died with a descendant still alive")

        self.profile.restore_checkpoint = crashing
        with self.assertRaisesRegex(RuntimeError, "descendant still alive"):
            self.restore(launcher=restoration_launcher,
                         cessation=restoration_cessation())
        self.profile.restore_checkpoint = honest
        for _ in range(200):
            if os.path.exists(scratch):
                break
            time.sleep(0.01)
        with open(scratch) as reading:
            survivor = int(reading.read().strip())

        # THE EXECUTOR'S MANAGER IS GONE -- its exclusion was released when its call
        # unwound -- but its child is not, and the production probe says so.
        fresh = self.fresh_manager()
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh, launcher=restoration_launcher,
                        cessation=restoration_cessation())
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("rather than ended", caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))
        self.assertEqual(
            len(review_cycles._claimed_episodes(fresh, recovery)), 1)
        self.assertEqual(self.line_row()["state"], "writing")

        # AND ONCE THE DESCENDANT IS GONE the same call settles. The wait is on the
        # PRODUCTION PROBE'S OWN ANSWER rather than on a pid check, because a killed
        # process is briefly a zombie and its group still answers alive -- which is the
        # probe being right, not slow, and is exactly the answer the settlement must wait
        # for rather than assume.
        # THE WHOLE GROUP, because `sleep 30` is a CHILD of the shell that recorded its
        # pid -- measured: killing the recorded pid alone left the sleep alive in the same
        # group and the probe went on answering `running`, correctly. Every process in it
        # was started by this case.
        launches = review_cycles._launched_commands(fresh, recovery, 1)
        watched = [group["observed"] for _, group in launches if group]
        for one in watched:
            try:
                os.killpg(one["group"], 9)
            except OSError:
                pass
        del survivor
        probe = restoration_cessation()
        for _ in range(250):
            if all(probe(one) == "ended" for one in watched):
                break
            time.sleep(0.02)
        self.assertTrue(all(probe(one) == "ended" for one in watched),
                        "the production probe must answer ended once the group is gone")
        settled = self.settle(store=fresh, launcher=restoration_launcher,
                              cessation=restoration_cessation())
        self.assertEqual(settled["episode"], 1)
        self.assertEqual(self.line_row()["state"], "writing")
        answered = self.restore(store=fresh, launcher=restoration_launcher,
                                cessation=restoration_cessation())
        self.assertEqual(answered["state"], "correction-ready")
    def test_a_stale_caller_after_a_real_settlement_keeps_the_successors_bytes(self):
        """THE WHOLE SEQUENCE, WITH A REAL SETTLEMENT AND REAL BYTES.

        Review 2026-09-26T05:27:11Z keeps this selected, and every earlier version of it
        leaned on rows this module planted. Nothing is planted here: the settlement is the
        product's own, the retry is an ordinary `restore_abandoned_correction`, the
        successor is admitted through `grant_writer`, and the bytes on disk are what the
        assertions read.

        THE SCHEDULE. An executor claims episode one, launches an accounted command that
        ENDS, and dies inside its profile -- so its exclusion is released, its episode is
        claimed, and its effects are accounted for. A fresh manager settles that episode,
        retries, and this time the restoration completes and releases the line. A successor
        is granted the line and WRITES. Then the original caller comes back.

        WHAT "COMES BACK" MEANS HERE, because review 2026-09-26T05:34:27Z asked for the
        distinction: this is a NEW request from the stale caller after its old invocation
        had already raised, not the resumption of an old in-flight callback. Python cannot
        resume a call that unwound, and no case here pretends otherwise.

        WHAT IT MUST NOT DO IS PERFORM ANOTHER EFFECT. It observes the completed recovery
        and answers it -- the SAME document the retry produced, not a second one -- and the
        successor's bytes are still on disk afterwards, byte for byte. That is the property
        review 2026-09-26T01:49:21Z [P1] reproduced the violation of, now measured on the
        far side of a real settlement rather than a planted one.
        """
        self.abandoned()
        self.attempt("writer-attempt-3", 3, "baton.impl", "writer-3")
        recovery, _ = self.interrupted()

        # A REAL SETTLEMENT AND A REAL RETRY, on a fresh manager.
        fresh = self.fresh_manager()
        settled = self.settle(store=fresh)
        self.assertEqual(settled["episode"], 1)
        completed = self.restore(store=fresh)
        self.assertEqual(completed["state"], "correction-ready")

        # A REAL SUCCESSOR, ADMITTED AND WRITING.
        granted = grant_writer(fresh, line_id=self.line_id,
                              attempt_id="writer-attempt-3", generation=3,
                              worker_id="worker-3", profile=self.profile,
                              based_checkpoint_id=self.checkpoint["checkpoint_id"])
        self.assertEqual(self.line_row()["state"], "writing")
        marker = os.path.join(self.line_path, "successor-data.txt")
        with open(marker, "w") as writing:
            writing.write("the successor's own bytes")

        # AND NOW THE STALE ORIGINAL CALLER, on its own handle, with no effect performed.
        crossed = []
        honest = self.profile.restore_checkpoint

        def counting(repository, evidence, *, runner=None):
            crossed.append(repository)
            return honest(repository, evidence, runner=runner)

        self.profile.restore_checkpoint = counting
        answered = self.restore()
        self.assertEqual(crossed, [],
                         "a stale caller observes the completion and performs no effect")
        self.assertEqual(answered, completed,
                         "it answers the recovery that happened, not a second one")
        with open(marker) as reading:
            self.assertEqual(reading.read(), "the successor's own bytes")
        # ONE COMPLETION, ONE SETTLEMENT, TWO EPISODES -- and episode TWO is "unsettled"
        # in the helper's sense, which review 2026-09-26T05:34:27Z asked me to say plainly:
        # `_unsettled_episodes` means "carries no SETTLEMENT record", and episode two
        # carries a COMPLETION instead, which is the other exit. Nothing is held open.
        self.assertEqual(len(review_cycles._claimed_episodes(fresh, recovery)), 2)
        self.assertEqual(review_cycles._unsettled_episodes(fresh, recovery), [2])
        self.assertEqual(self.line_row()["state"], "writing")
        # AND THE LINE IS THE SUCCESSOR'S NOW: three writer rows, the newest one active.
        self.assertEqual(len(self.writers()), 3)
        self.assertEqual(
            writer_of(fresh, granted["writer_id"])["state"], "active")

    def test_the_probe_holds_on_a_record_no_live_kernel_can_confirm(self):
        """NAMESPACE AND BOOT UNCERTAINTY, deterministically, without racing the kernel.

        Review 2026-09-26T05:27:11Z asks for these as cases rather than as a stress run, and
        they are identity questions, not timing ones. A recorded group number means nothing
        on its own: the same number exists in another PID namespace, and after a reboot
        every number is somebody else's. The probe's three answers are what carry that, and
        the two that HOLD are the ones a settlement must never read as ended.

        A RECORD THIS KERNEL CANNOT CONFIRM IS `unknown`, never `ended`: an incomplete
        record, a non-document, a record naming this manager's OWN group -- which is what a
        record from another namespace looks like when its number happens to land here -- and
        a record whose fields are not integers at all.

        A LIVE NUMBER WITH A DIFFERENT START INSTANT IS `ended`, because that is the same
        number belonging to something else -- id reuse within a boot, or the whole table
        reassigned after one. A record whose start instant matches is `running`.

        AND THE SETTLEMENT INHERITS EXACTLY THOSE ANSWERS: a record it cannot confirm holds
        it, which this asserts through the product rather than only through the probe.
        """
        from tools.stage_execution import restoration_cessation, _process_started

        probe = restoration_cessation()
        own = {"group": os.getpgrp(), "leader": os.getpid(),
               "started": _process_started(os.getpid())}
        for record, expected in (
                ({"group": 1}, "unknown"),                       # incomplete
                ("not a document", "unknown"),
                ({"group": 1, "leader": 1, "started": "x"}, "unknown"),
                ({"group": True, "leader": 1, "started": 1}, "unknown"),
                (own, "unknown"),                                # this manager's own group
                (dict(own, started=own["started"] + 4242), "unknown")):
            with self.subTest(record=record):
                self.assertEqual(probe(record), expected)

        # AND THROUGH THE PRODUCT: an episode whose recorded group is one this kernel
        # cannot speak about is HELD by the settlement, not settled. The launch is recorded
        # with THIS manager's own group -- which is what a record carried in from another
        # namespace looks like when its number lands here -- and the production probe is
        # asked about it.
        self.abandoned()
        recording = []

        def launcher(record):
            def launched(argv, *, input=None):
                record("intent", None)
                record("group", dict(own))
                recording.append(argv)
                return {"returncode": 0, "stdout": "", "stderr": ""}
            return launched

        def crash(repository, evidence, *, runner=None):
            runner(("fixture", "reset"))
            raise RuntimeError("the executor died inside its restoration")

        honest = self.profile.restore_checkpoint
        self.profile.restore_checkpoint = crash
        with self.assertRaisesRegex(RuntimeError, "died inside"):
            self.restore(launcher=launcher, cessation=probe)
        self.profile.restore_checkpoint = honest
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        self.assertEqual(recording, [("fixture", "reset")])
        fresh = self.fresh_manager()
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh, launcher=launcher, cessation=probe)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("is 'unknown' rather than ended", caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))
        self.assertEqual(self.line_row()["state"], "writing")
    def test_a_launch_number_is_only_read_inside_the_domain_that_minted_it(self):
        """THE GENUINE COMPARISON PATHS, not a collision with this manager's own group.

        Review 2026-09-26T05:34:27Z [P1] is right that my earlier "namespace and boot" case
        established neither: an own-group coincidence and a malformed record only exercise
        the shape checks. The real claim is that `killpg` answering ESRCH means "no such
        group IN THIS PID VIEW", which is not absence in the view that MINTED the number --
        a live original can be invisible from another namespace -- and that start ticks are
        measured from a boot, so across a restart they describe a different
        machine-lifetime.

        SO THE RECORD NOW CARRIES WHERE IT WAS MINTED and the observer compares before it
        probes. Each case below changes EXACTLY ONE of those two fields away from this
        deployment's own and asserts `unknown` even though the number itself is absent here
        -- absence in the wrong domain is not cessation. A legacy record with no scope at
        all answers `unknown` for the same reason, and only a record whose scope matches is
        probed at all.

        NO KERNEL IS MUTATED AND NO PROCESS IS CREATED: `killpg` is where the answer comes
        from, so that is the one call patched, exactly as the reviewer's own probe does it.
        """
        from tools.stage_execution import _issuing_domain, restoration_cessation

        probe = restoration_cessation()
        domain = _issuing_domain()
        self.assertIsNotNone(domain)
        number = os.getpgrp() + 1000000
        absent = {"group": number, "leader": number, "started": 17}

        with mock.patch("os.killpg", side_effect=ProcessLookupError):
            # ONLY the matching domain is read as ended.
            self.assertEqual(probe(dict(absent, **domain)), "ended")
            # ANOTHER PID VIEW: the number may name a live group there.
            self.assertEqual(
                probe(dict(absent, pid_namespace="4:999999999",
                           boot=domain["boot"])), "unknown")
            # ANOTHER BOOT: the start ticks describe a different machine-lifetime.
            self.assertEqual(
                probe(dict(absent, pid_namespace=domain["pid_namespace"],
                           boot="00000000-0000-0000-0000-000000000000")), "unknown")
            # BOTH WRONG, and a LEGACY record with neither -- the exact shape the previous
            # launcher emitted, which is what made this a defect rather than a gap.
            self.assertEqual(probe(dict(absent, pid_namespace="4:999999999",
                                        boot="00000000-0000-0000-0000-000000000000")),
                             "unknown")
            self.assertEqual(probe(dict(absent)), "unknown")
            # AND A SCOPE OF THE WRONG TYPE is not a scope.
            self.assertEqual(probe(dict(absent, pid_namespace=None,
                                        boot=domain["boot"])), "unknown")
            # AND AN OBSERVER THAT CANNOT READ ITS OWN DOMAIN compares nothing, so a
            # perfectly formed record is still unknown: a comparison that cannot be made
            # is never a pass.
            with mock.patch("tools.stage_execution._issuing_domain",
                            return_value=None):
                self.assertEqual(probe(dict(absent, **domain)), "unknown")

        # THE PRODUCT INHERITS IT: an episode whose launch was recorded without a domain --
        # a legacy account -- holds the settlement rather than settling on absence.
        self.abandoned()
        recorded = []

        def launcher(record):
            def launched(argv, *, input=None):
                record("intent", None)
                # THE PREVIOUS LAUNCHER'S EXACT SHAPE, deliberately: group, leader and
                # start ticks with no issuing domain.
                record("group", {"group": number, "leader": number, "started": 17})
                recorded.append(argv)
                return {"returncode": 0, "stdout": "", "stderr": ""}
            return launched

        honest = self.profile.restore_checkpoint

        def crash(repository, evidence, *, runner=None):
            runner(("fixture", "reset"))
            raise RuntimeError("the executor died inside its restoration")

        self.profile.restore_checkpoint = crash
        with self.assertRaisesRegex(RuntimeError, "died inside"):
            self.restore(launcher=launcher, cessation=probe)
        self.profile.restore_checkpoint = honest
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        self.assertEqual(recorded, [("fixture", "reset")])
        fresh = self.fresh_manager()
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh, launcher=launcher, cessation=probe)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("is 'unknown' rather than ended", caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))
        self.assertEqual(self.line_row()["state"], "writing")

    def test_a_launch_that_cannot_scope_its_numbers_is_not_performed(self):
        """AN UNSCOPED LAUNCH IS REFUSED BEFORE THE FORK, not recorded and held forever.

        A record without its issuing domain can never be read as ended, so starting a child
        under one would guarantee a permanent hold. The production launcher therefore reads
        the domain BEFORE it records anything and refuses if it cannot -- the same rule the
        rest of this boundary follows, applied to the one place that mints the numbers.
        """
        from tools.stage_execution import restoration_launcher

        recorded = []
        with mock.patch("tools.stage_execution._issuing_domain", return_value=None):
            launched = restoration_launcher(lambda part, payload:
                                            recorded.append(part))
            with self.assertRaisesRegex(RuntimeError, "cannot be accounted for"):
                launched(("/bin/sh", "-c", "true"))
        self.assertEqual(recorded, [],
                         "nothing is recorded for a launch that never happened")
    def test_a_real_manager_dies_leaving_a_child_and_a_fresh_manager_finishes_it(self):
        """THE COMBINED SCENARIO, in one run, with real processes on both sides.

        Review 2026-09-26T05:41:32Z: my two real-process cases were partial evidence, not
        this. One had a child interpreter holding the exclusion and dying with no child of
        its own; the other had an orphan descendant outliving a manager whose call merely
        unwound by exception. Neither is the thing the recovery exists for, which is ONE run
        where an actual manager process performs an accounted restoration, DIES while its
        child survives, and another manager finishes the job.

        SO THIS RUNS A REAL MANAGER IN A REAL INTERPRETER. It opens its own `ControlStore`,
        performs `restore_abandoned_correction` with the PRODUCTION launcher and probe, and
        inside its profile it starts a same-group descendant that closes its stdio and stays
        -- then calls `os._exit`, so the process is GONE mid-restoration with its launch
        recorded, its episode claimed and its exclusion released by the kernel rather than
        by any code.

        AND THEN THE FOUR THINGS THAT MATTER, in order:

          1. A fresh manager CANNOT settle while the descendant lives. The kernel says no
             manager holds the execution; the account says its child is still there; the
             settlement holds and the episode stays claimed.
          2. THE ATTRIBUTION SURVIVES THE DEATH: the claim still names the dead manager's
             own executor token, so what is being settled is identifiable as ITS execution
             and not as anybody else's.
          3. ONCE THE DESCENDANT IS GONE the probe says so positively and the settlement
             succeeds, naming that same dead executor.
          4. THE FRESH MANAGER THEN RETRIES and the restoration completes, releasing the
             line to `correction-ready`.

        EVERY PROCESS SIGNALLED HERE WAS STARTED HERE, and both the manager and the group
        are reaped.
        """
        from tools.stage_execution import (restoration_cessation,
                                           restoration_launcher)

        self.abandoned()
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        scratch = os.path.join(self.temporary.name, "orphan.pid")
        program = (
            "import os, sys\n"
            "from baton_v12.worker_manager import ControlStore\n"
            "from baton_v12.worker_manager.review_cycles import "
            "restore_abandoned_correction\n"
            "from tools.stage_execution import restoration_launcher, "
            "restoration_cessation\n"
            "import test_restore_outside_the_lock as author\n"
            "control, storage, scratch, now = sys.argv[1:5]\n"
            "store = ControlStore.open(control, incarnation='dying-manager',\n"
            "                          clock=lambda: now)\n"
            "profile = author.AccountedProfile()\n"
            "def restoring(repository, evidence, *, runner=None):\n"
            "    runner(('/bin/sh', '-c',\n"
            "            \"sh -c 'echo $$ > \" + scratch + \"; exec 1>&- 2>&-; \"\n"
            "            \"sleep 30' &\"))\n"
            "    sys.stdout.write('LAUNCHED\\n')\n"
            "    sys.stdout.flush()\n"
            "    os._exit(9)\n"
            "profile.restore_checkpoint = restoring\n"
            "restore_abandoned_correction(\n"
            "    store, attempt_id=author.ABANDONED, generation=2,\n"
            "    retention_policy_digest=author.RETENTION, profile=profile,\n"
            "    launcher=restoration_launcher,\n"
            "    cessation=restoration_cessation())\n")
        manager = subprocess.Popen(
            [sys.executable, "-c", program, self.control_path, self.storage,
             scratch, NOW],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            start_new_session=True)
        launched = manager.stdout.readline().strip()
        out, err = manager.communicate(timeout=60)
        self.assertEqual(launched, "LAUNCHED",
                         f"the real manager must reach its launch: {err[-800:]}")
        self.assertEqual(manager.returncode, 9,
                         "the manager must have died rather than returned")
        for _ in range(500):
            if os.path.exists(scratch):
                break
            time.sleep(0.01)
        with open(scratch) as reading:
            orphan = int(reading.read().strip())

        # 1. THE EPISODE IS CLAIMED AND THE DESCENDANT IS ALIVE, so nobody settles.
        fresh = self.fresh_manager()
        claimed = review_cycles._claimed_episodes(fresh, recovery)
        self.assertEqual(len(claimed), 1)
        probe = restoration_cessation()
        launches = review_cycles._launched_commands(fresh, recovery, 1)
        watched = [group["observed"] for _, group in launches if group]
        self.assertTrue(watched, "the dead manager's launch must be recorded")
        self.assertIn("running", [probe(one) for one in watched])
        with self.assertRaises(ContractRefusal) as caught:
            self.settle(store=fresh, launcher=restoration_launcher,
                        cessation=probe)
        self.assertIn("rather than ended", caught.exception.message)
        self.assertIsNone(fresh.operation_record(
            review_cycles._settled_id(recovery, 1)))
        self.assertEqual(self.line_row()["state"], "writing")

        # 2. THE ATTRIBUTION SURVIVED: the claim names the dead manager's token.
        _, owner = fresh.replay(
            review_cycles._execution_id(recovery, 1), claimed[0]["signature"],
            kind=review_cycles.RESTORE_EXECUTION_KIND)
        self.assertTrue(owner["executor"].startswith("dying-manager:"),
                        f"unexpected executor {owner['executor']}")

        # 3. THE DESCENDANT GOES and the probe says so, positively.
        for one in watched:
            try:
                os.killpg(one["group"], 9)
            except OSError:
                pass
        del orphan
        for _ in range(500):
            if all(probe(one) == "ended" for one in watched):
                break
            time.sleep(0.02)
        self.assertTrue(all(probe(one) == "ended" for one in watched))
        settled = self.settle(store=fresh, launcher=restoration_launcher,
                              cessation=probe)
        self.assertEqual(settled["episode"], 1)
        self.assertEqual(settled["executor"], owner["executor"])
        self.assertEqual(self.line_row()["state"], "writing")

        # 4. AND THE FRESH MANAGER FINISHES THE WORK.
        answered = self.restore(store=fresh, launcher=restoration_launcher,
                                cessation=restoration_cessation())
        self.assertEqual(answered["state"], "correction-ready")
        self.assertEqual(self.line_row()["state"], "correction-ready")
        self.assertEqual(len(review_cycles._claimed_episodes(fresh, recovery)), 2)
    def test_a_loser_that_reads_the_writer_after_the_winner_revoked_it_is_precise(self):
        """THE FOURTH EXCLUSION OUTCOME, staged DETERMINISTICALLY instead of asserted loosely.

        Review 2026-09-26T05:47:16Z caught caller `b` in the concurrent case taking a refusal
        I had not enumerated -- the fresh path's own writer reader -- and refused the obvious
        patch: widening the accepted messages again is not a proof of anything. The timing it
        named is precise, so it is staged precisely here.

        THE SCHEDULE. The fresh branch decides there is no recovery intent, reads its
        evidence, and only THEN reads the writer. So a caller can pass the intent decision
        before a competitor commits and still read the writer after that competitor's intent
        REVOKED it -- and a revoked writer is exactly what the fresh path must refuse,
        because it is what a correction that reached its checkpoint leaves behind. The reader
        cannot tell those apart, and it is right not to guess.

        STAGED WITHOUT THREADS by interposing on the writer read itself: the competitor's
        whole restoration runs inside the loser's first `writer_for_attempt` call, so the
        revocation provably precedes the read rather than probably preceding it.

        AND THE GUARANTEES ARE ASSERTED, not just the message: exactly ONE external effect,
        one completed recovery, the winner's document answered on replay, and the successor's
        line state untouched by the loser.
        """
        self.abandoned()
        crossings = []
        honest = self.profile.restore_checkpoint
        winner = self.fresh_manager("winning-manager")
        answered = []

        def counting(repository, evidence, *, runner=None):
            crossings.append(repository)
            return honest(repository, evidence, runner=runner)

        self.profile.restore_checkpoint = counting
        real_reader = review_cycles.writer_for_attempt

        entered = []

        def reading(store, *, attempt_id, generation):
            # THE FLAG IS SET BEFORE THE NESTED CALL, not after. Measured: appending the
            # ANSWER as the guard re-entered this wrapper from the competitor's own read and
            # recursed until the interpreter gave up -- a fixture bug, and a reminder that a
            # guard has to be taken before the work it guards.
            if not entered:
                entered.append(True)
                # THE COMPETITOR COMMITS ITS INTENT -- which revokes the writer -- and
                # completes, all before this caller's read returns.
                answered.append(self.restore(store=winner))
            return real_reader(store, attempt_id=attempt_id, generation=generation)

        with mock.patch.object(review_cycles, "writer_for_attempt",
                               side_effect=reading):
            with self.assertRaises(ContractRefusal) as caught:
                self.restore()

        self.assertEqual(len(answered), 1)
        self.assertEqual(answered[0]["state"], "correction-ready")
        # THE PRECISE REFUSAL: the fresh path's writer reader, naming the state it found.
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("writer is 'revoked'", caught.exception.message)
        self.assertIn("a revoked writer is what one that did leaves behind",
                      caught.exception.message)
        # ONE EFFECT, ONE RECOVERY, AND THE LOSER CHANGED NOTHING.
        self.assertEqual(len(crossings), 1)
        self.assertEqual(self.line_row()["state"], "correction-ready")
        recovery = review_cycles._restore_operation_id(RESTORE_KIND, ABANDONED, 2)
        self.assertEqual(len(review_cycles._claimed_episodes(self.store, recovery)), 1)
        # AND A REPLAY ON THE LOSER'S OWN HANDLE ANSWERS THE WINNER'S DOCUMENT, performing
        # no second effect.
        replayed = self.restore()
        self.assertEqual(replayed, answered[0])
        self.assertEqual(len(crossings), 1)

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
