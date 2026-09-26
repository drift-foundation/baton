"""W257624: `grant_writer` admits a writer WITHOUT holding the lock over I/O.

Owner reroute 270290 selects one executable correction and this module is its
proof: remove filesystem I/O from the `grant_writer` transaction in
`worker_manager/review_cycles.py` while preserving exclusive generation-bound
writer admission, checkpoint validation and resource identity safety. The pinned
selection, the exact file ownership and the shape of the correction are in this
dossier's FINDING and PLAN entries dated 2026-09-26.

WHAT THE CORRECTION IS. `grant_writer.act` used to call `_validate_line_object`
and `workspaces._prove_line_access` INSIDE `ControlStore.transact` -- a `stat`, a
path validation and an access validation under the database write lock, plus
`check_workspace_group`'s `os.getgroups()` riding along with the second. Those
proofs now run once before the transaction is opened, in `_proved_line_object`,
which returns the recorded object triple they were taken over; the callback
compares that pin against the row in pure SQL and touches no file.

HOW THE ORDERING IS MEASURED RATHER THAN ASSERTED. `AnOpenTransaction` replaces
the operating-system calls this admission can reach and records, at every one,
whether `store._connection.in_transaction` was true. A clean result from a probe
that never fires proves nothing, so two things are required of every ordering
case: the probe must have observed real calls, and a POSITIVE CONTROL must show
the same probe catching a genuine violation. `create_line` supplies that control
-- it still proves line integrity and establishes access inside its own
transaction -- so the probe is demonstrated to detect exactly what it is used to
rule out. That `create_line` violation is out of this correction's selected scope
and is recorded as remaining rather than repaired here.

WHAT IS REAL: a real `ControlStore` on a disposable temporary root, real
directories under a disk-backed storage root, the real `create_line`,
`grant_writer`, `freeze_checkpoint`, `record_verdict` and `attach_review`, real
second connections for the contention case, and the real journal.

WHAT IS CONTROLLED AND DETERMINISTIC, named as the standing constraints require:
the checkpoint profile and the authority port are this repository's accepted
`tests.manager.test_review_cycles` fixtures, and the row edit that drives the
in-lock pin comparison is inserted by this module at an exact cut point. No live
provider, no engine, no daemon, no network and no deployed store is reached.

WHAT THIS DOES NOT CLAIM: no global I/O-under-lock coverage for any other call
site, no R3 completion, no R4 or R5 evidence, and no adoption claim. Unknown
outcome holds are untouched.
"""
import os
import sqlite3
import tempfile
import threading
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (ControlStore, attach_review,
                                      checkpoint_of, create_line,
                                      freeze_checkpoint, grant_writer, line_of,
                                      record_verdict, writer_of)
from baton_v12.worker_manager import review_cycles, workspaces
from baton_v12.worker_manager.source_boundary import nominate_source
from baton_v12.worker_manager.workspaces import configure_workspace_storage

from tests.manager import input_roots
from tests.manager.disk_roots import disk_backed_under
from tests.manager.test_review_cycles import (AUTHORITY, BASE, NOW, WORK,
                                              Port, Profile)

# The operating-system calls this admission can reach. `os.stat`, `os.lstat` and
# the three `os.path` predicates are the filesystem reads `_object` and
# `_prove_line_access` make; `os.getgroups` and `os.getgid` are the credential
# reads `check_workspace_group` makes; the four mutators are here so a case that
# accidentally reached one would see it rather than pass quietly. sqlite's own
# I/O is in C and is deliberately invisible to this probe -- the ruling exempts
# the database's own I/O, so a probe that saw it would be measuring the wrong
# thing.
OBSERVED = ("stat", "lstat", "getgroups", "getgid", "access", "scandir",
            "listdir", "chmod", "chown", "rename")
OBSERVED_PATH = ("realpath", "islink", "isdir", "exists")

# Every barrier and join in this module is bounded, so a schedule that does not
# happen fails the case instead of hanging the run. The JOIN bound is deliberately
# the larger of the two: a rendezvous that cannot happen must break FIRST, so the
# case reports "the requested schedule did not occur" rather than the generic
# "a thread is still running" that a join tripping first would give.
WAIT = 5
JOIN = WAIT * 3


class AnOpenTransaction:
    """Record, at every observed OS call, whether a transaction was open.

    ONE OBSERVABLE AND IT IS THE PRODUCT'S OWN. `sqlite3.Connection.in_transaction`
    is true from an explicit `BEGIN` until the matching `COMMIT` or `ROLLBACK`,
    and `ControlStore` opens its connection with `isolation_level=None` and issues
    `BEGIN IMMEDIATE` itself -- so this is the real lock state rather than a
    fixture's idea of it. `ControlStore.snapshot` already reads the same attribute.
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
        for name in OBSERVED:
            patch = mock.patch.object(os, name,
                                      self._wrap(name, getattr(os, name)))
            patch.start()
            self._stack.append(patch)
        for name in OBSERVED_PATH:
            patch = mock.patch.object(
                os.path, name, self._wrap(name, getattr(os.path, name)))
            patch.start()
            self._stack.append(patch)
        return self

    def __exit__(self, *failure):
        for patch in reversed(self._stack):
            patch.stop()
        return False


class GrantWriterAdmission(unittest.TestCase):
    """Real store, real directories, accepted profile and port fixtures."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="v12-grant-writer-")
        self.addCleanup(self.temporary.cleanup)
        self.source = os.path.join(self.temporary.name, "source")
        os.mkdir(self.source)
        # THE STORAGE ROOT IS DISK-BACKED through the accepted helper, because
        # the line boundaries refuse a workspace on a memory filesystem and the
        # system temporary directory is a tmpfs on this host.
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

    # -- the accepted fixtures' own helpers, spelled here ---------------------

    def port(self, participant):
        return self.ports.setdefault(participant, Port(participant))

    def attempt(self, attempt_id, generation, participant, principal):
        """One attempt row a delivery would have written.

        The accepted `ReviewCycles.attempt` shortcut, spelled here rather than
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

    def line(self):
        return create_line(self.store, source=nominate_source(self.source),
                           declared_base=BASE, profile=self.profile,
                           authority_uuid=AUTHORITY, work_id=WORK)

    def completed(self, attempt_id):
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = "
            "'quiescent', worker_disposition = 'completed' "
            "WHERE runtime_attempt_id = ?", ("runtime-" + attempt_id,
                                             attempt_id))

    def completed_review(self, attempt_id):
        self.completed(attempt_id)
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

    def correction_ready(self):
        """One reviewed, sent-back round, so the line admits a CORRECTION writer.

        Composed entirely through the real acts: grant, freeze, attach, verdict.
        """
        line = self.line()
        writer = self.granted(line["line_id"], 1)
        self.completed("writer-attempt-1")
        checkpoint = freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, port=self.port("baton.impl"))
        attempt = self.attempt("review-attempt-1", 1, "baton.review",
                               "reviewer-1")
        attached = attach_review(
            self.store, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id=attempt, generation=1,
            reviewer_worker_id="review-worker-1", profile=self.profile)
        self.completed_review("review-attempt-1")
        record_verdict(self.store, attachment_id=attached["attachment_id"],
                       disposition="changes-requested", profile=self.profile,
                       port=self.port("baton.review"))
        self.assertEqual(line_of(self.store, line["line_id"])["state"],
                         "correction-ready")
        return line, checkpoint

    def row(self, line_id):
        return line_of(self.store, line_id)

    # -- the ordering, which is what the correction is about ------------------

    def test_the_probe_catches_a_real_violation_before_it_is_trusted(self):
        """THE POSITIVE CONTROL, and nothing below means anything without it.

        `create_line` proves line integrity and establishes access INSIDE its own
        `store.transact`, so it is a live example of the very thing this
        correction removes from `grant_writer`. The same probe is pointed at it
        first: if it reports calls under the lock here, then a clean report for
        `grant_writer` is a measurement rather than a probe that never fired.

        THIS IS NOT A COMPLAINT ABOUT `create_line` AND NOT A REPAIR OF IT. Owner
        reroute 270290 selected the `grant_writer` correction only; this site is
        recorded as a remaining violation in this dossier's FINDING.
        """
        with AnOpenTransaction(self.store._connection) as observing:
            self.line()
        self.assertTrue(observing.calls, "the probe observed no OS calls at all")
        self.assertTrue(
            observing.under_lock,
            "the probe saw no call under an open transaction, so it cannot be "
            "used to rule one out")

    def test_no_filesystem_call_happens_while_the_grant_holds_the_lock(self):
        """A FIRST WRITER'S ADMISSION, measured call by call."""
        line = self.line()
        self.attempt("writer-attempt-1", 1, "baton.impl", "writer-1")
        with AnOpenTransaction(self.store._connection) as observing:
            granted = grant_writer(
                self.store, line_id=line["line_id"],
                attempt_id="writer-attempt-1", generation=1,
                worker_id="worker-1", profile=self.profile)
        # THE PROBE FIRED: this admission really did reach the filesystem, so a
        # clean ordering is not the silence of a check that never ran.
        self.assertTrue(observing.calls)
        self.assertEqual(observing.under_lock, [])
        # AND THE TRANSACTION REALLY HAPPENED, so the empty list above is the
        # absence of I/O under a lock rather than the absence of a lock.
        self.assertEqual(granted["state"], "active")
        self.assertEqual(writer_of(self.store, granted["writer_id"])["state"],
                         "active")
        self.assertEqual(self.row(line["line_id"])["state"], "writing")

    def test_no_filesystem_call_happens_while_a_correction_holds_the_lock(self):
        """AND THE CORRECTION PATH, which also validates a checkpoint.

        The correction branch calls `profile.validate` with `current=True`, which
        the ruling names as I/O in its own right. It is already outside the
        transaction and this measures that it stays there.
        """
        line, checkpoint = self.correction_ready()
        self.attempt("writer-attempt-2", 2, "baton.impl", "writer-2")
        validations = []
        honest = self.profile.validate

        def validate(repository, evidence, *, current=False):
            validations.append(self.store._connection.in_transaction)
            return honest(repository, evidence, current=current)

        self.profile.validate = validate
        with AnOpenTransaction(self.store._connection) as observing:
            granted = grant_writer(
                self.store, line_id=line["line_id"],
                attempt_id="writer-attempt-2", generation=2,
                worker_id="worker-2", profile=self.profile,
                based_checkpoint_id=checkpoint["checkpoint_id"])
        self.assertTrue(observing.calls)
        self.assertEqual(observing.under_lock, [])
        # THE CHECKPOINT VALIDATION HAPPENED AND HELD NO LOCK.
        self.assertEqual(validations, [False])
        self.assertEqual(granted["generation"], 2)
        self.assertEqual(
            writer_of(self.store, granted["writer_id"])["based_checkpoint_id"],
            checkpoint["checkpoint_id"])

    def test_a_replayed_grant_reaches_no_access_proof_and_no_lock(self):
        """AND A GRANT THAT ALREADY COMMITTED DOES NOT RE-PROVE ITS ACCESS.

        The moved proof sits AFTER the journal replay check, so an exact retry
        answers its committed document without reaching `_prove_line_access` at
        all. The placement is deliberate: above the replay, every retry would pay
        for it.

        MEASURED, AND MY FIRST VERSION OF THIS CASE WAS WRONG. I asserted that a
        replay performs no filesystem work whatever, and it performs fourteen OS
        calls -- because `grant_writer` has ALWAYS validated the line object at
        the top of the function, before the replay check, and this correction did
        not move that call and has no mandate to. So what is true and asserted is
        narrower: every one of those calls is outside a transaction, and the
        access proof this correction relocated is not reached.
        """
        line = self.line()
        self.attempt("writer-attempt-1", 1, "baton.impl", "writer-1")
        operands = {"line_id": line["line_id"],
                    "attempt_id": "writer-attempt-1", "generation": 1,
                    "worker_id": "worker-1", "profile": self.profile}
        first = grant_writer(self.store, **operands)
        proofs = []
        honest = workspaces._prove_line_access

        def proving(place, pinned, gid):
            proofs.append(place)
            return honest(place, pinned, gid)

        with mock.patch.object(workspaces, "_prove_line_access", proving):
            with AnOpenTransaction(self.store._connection) as observing:
                replay = grant_writer(self.store, **operands)
        self.assertEqual(replay, first)
        self.assertEqual(proofs, [])
        self.assertTrue(observing.calls)
        self.assertEqual(observing.under_lock, [])

    # -- what the correction had to preserve ---------------------------------

    def contending(self, line, synchronize):
        """Two real handles racing for one line, with bounded waits.

        `synchronize` is called by each contender at the cut point a case wants
        to force; the case supplies it, so the SCHEDULE is the case's statement
        rather than whatever the interpreter happened to do. Anything that is not
        a `ContractRefusal` is captured and re-raised by the caller instead of
        dying inside a thread, and every handle is closed in its own `finally` so
        cleanup precedes fixture teardown.
        """
        outcomes = {}
        failures = []

        def contender(name, attempt, generation):
            beside = ControlStore.open(self.control_path,
                                       incarnation=f"manager-{generation + 1}",
                                       clock=lambda: NOW)
            try:
                outcomes[name] = grant_writer(
                    beside, line_id=line["line_id"], attempt_id=attempt,
                    generation=generation,
                    worker_id=f"race-worker-{generation}",
                    profile=self.profile)
            except ContractRefusal as refusal:
                outcomes[name] = refusal
            except BaseException as failure:            # noqa: BLE001
                # PROPAGATED, NOT SWALLOWED. A broken barrier or a fault inside a
                # thread would otherwise leave this case asserting about one
                # outcome and calling it a race.
                failures.append(failure)
                synchronize.abort()
            finally:
                beside.close()

        threads = [threading.Thread(target=contender, args=("a", "race-a", 1)),
                   threading.Thread(target=contender, args=("b", "race-b", 2))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=JOIN)
            self.assertFalse(thread.is_alive(),
                             "a contender did not finish within the bound")
        if failures:
            raise failures[0]
        return outcomes

    def test_one_line_admits_exactly_one_of_two_competing_writers(self):
        """EXCLUSIVE ADMISSION AT THE WINDOW THE CORRECTION ACTUALLY WIDENS.

        Review 2026-09-26T01:23:34Z [P2], and the finding was right: my first
        version waited at a barrier BEFORE `grant_writer` was called, which does
        not schedule anything. Thread timing could let the winner commit before
        the loser had even read the line, and the loser then refuses at the OUTER
        state branch -- a correct refusal, but not the one this case claimed, so
        the case was flaky and never established the post-proof interleaving.

        THE SYNCHRONIZATION IS NOW AFTER EACH REAL PROOF and before either
        transaction, through the same seam the reviewer's probe used:
        `_proved_line_object` is the last thing `grant_writer` does before
        `store.transact`, so a barrier as it returns holds both contenders in
        exactly the new window. `observed` records the lock state at each proof,
        so the case also proves both got there outside a transaction rather than
        assuming it.

        AND THE LOSING REFUSAL IS THE IN-LOCK ONE, asserted precisely. Both
        contenders are past the outer state branch by construction, so the loser
        can only be refused by the check inside the callback -- which is the
        statement being made: the exclusion did NOT move out of the lock with the
        I/O.

        THE NAME IS DELIBERATELY UNCHANGED. The reviewer's preserved probe calls
        this method by name to force its own schedules onto it, and renaming the
        corrected case would break that immutable evidence with an
        `AttributeError` rather than superseding it.
        """
        line = self.line()
        self.attempt("race-a", 1, "baton.a", "principal-a")
        self.attempt("race-b", 2, "baton.b", "principal-b")
        proved = threading.Barrier(2, timeout=WAIT)
        observed = []
        recording = threading.Lock()
        honest = review_cycles._proved_line_object

        def together(store, row):
            pin = honest(store, row)
            with recording:
                observed.append(store._connection.in_transaction)
            try:
                proved.wait()
            except threading.BrokenBarrierError:
                # THE REQUESTED SCHEDULE DID NOT HAPPEN, said precisely. A caller
                # that holds one contender back until the other has finished --
                # the reviewer's preserved delayed-entry probe does exactly that
                # -- cannot produce this window at all, and this case must say so
                # rather than report a generic stuck thread.
                raise AssertionError(
                    "both contenders did not reach the post-proof rendezvous "
                    "within the bound, so this schedule was not exercised"
                ) from None
            return pin

        with mock.patch.object(review_cycles, "_proved_line_object", together):
            outcomes = self.contending(line, proved)

        # BOTH REACHED THE CUT POINT, AND NEITHER HELD A LOCK THERE.
        self.assertEqual(observed, [False, False])
        answers = list(outcomes.values())
        self.assertEqual(len(answers), 2)
        self.assertEqual(sum(type(one) is dict for one in answers), 1)
        [refusal] = [one for one in answers
                     if isinstance(one, ContractRefusal)]
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("the line acquired another active attachment",
                      refusal.message)
        # ONE WRITER ROW EXISTS, read from a connection neither contender owned.
        beside = sqlite3.connect(self.control_path, isolation_level=None)
        try:
            self.assertEqual(
                [one[0] for one in beside.execute(
                    "SELECT state FROM line_writers")], ["active"])
        finally:
            beside.close()
        self.assertEqual(self.row(line["line_id"])["state"], "writing")

    def test_a_writer_arriving_after_the_line_is_taken_refuses_early(self):
        """THE OTHER VALID SCHEDULE, with ITS OWN correct refusal.

        The reviewer's preserved probe forces a contender to enter only after the
        first admission has finished, which is a legitimate interleaving my
        previous race could silently fall into. Kept here as its own
        deterministic case rather than as an alternative message the race would
        accept: a late arrival is refused by the OUTER state branch, before the
        relocated access proof is reached at all, and that is a different fact
        from the in-lock exclusion above.
        """
        line = self.line()
        self.attempt("race-a", 1, "baton.a", "principal-a")
        self.attempt("race-b", 2, "baton.b", "principal-b")
        first = grant_writer(self.store, line_id=line["line_id"],
                             attempt_id="race-a", generation=1,
                             worker_id="race-worker-1", profile=self.profile)
        self.assertEqual(first["state"], "active")
        proofs = []
        honest = workspaces._prove_line_access

        def proving(place, pinned, gid):
            proofs.append(place)
            return honest(place, pinned, gid)

        with mock.patch.object(workspaces, "_prove_line_access", proving):
            with AnOpenTransaction(self.store._connection) as observing:
                with self.assertRaises(ContractRefusal) as caught:
                    grant_writer(self.store, line_id=line["line_id"],
                                 attempt_id="race-b", generation=2,
                                 worker_id="race-worker-2",
                                 profile=self.profile)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertIn("does not admit a writer", caught.exception.message)
        self.assertIn("writing", caught.exception.message)
        # REFUSED BEFORE THE RELOCATED PROOF, and with no lock held at any call.
        self.assertEqual(proofs, [])
        self.assertEqual(observing.under_lock, [])
        beside = sqlite3.connect(self.control_path, isolation_level=None)
        try:
            self.assertEqual(
                [one[0] for one in beside.execute(
                    "SELECT state FROM line_writers")], ["active"])
        finally:
            beside.close()

    def test_an_assignment_at_another_generation_is_refused(self):
        """STALE GENERATION, at the admission's own assignment comparison."""
        line = self.line()
        self.attempt("writer-attempt-1", 1, "baton.impl", "writer-1")
        with self.assertRaises(ContractRefusal) as caught:
            grant_writer(self.store, line_id=line["line_id"],
                         attempt_id="writer-attempt-1", generation=2,
                         worker_id="worker-1", profile=self.profile)
        self.assertEqual(caught.exception.category, "stale-assignment")
        self.assertEqual(self.row(line["line_id"])["state"], "idle")
        # NO WRITER ROW AT ALL, read beside the store. Measured rather than
        # asserted through `writer_of`, which REFUSES an unknown writer instead
        # of answering absence -- my first version expected None from it.
        beside = sqlite3.connect(self.control_path, isolation_level=None)
        try:
            self.assertEqual(list(beside.execute(
                "SELECT state FROM line_writers")), [])
        finally:
            beside.close()

    def test_a_line_whose_object_changed_admits_nobody(self):
        """CHANGED RESOURCE, at the proof that now runs before the lock.

        The recorded pathname is made to name a DIFFERENT directory, which is
        what an operator replacing a checkout under the manager produces. The
        admission refuses and no writer row is written -- and it refuses before
        any transaction is opened, which the probe measures.
        """
        line = self.line()
        self.attempt("writer-attempt-1", 1, "baton.impl", "writer-1")
        place = line["path"]
        os.rename(place, place + "-moved")
        os.mkdir(place)
        with AnOpenTransaction(self.store._connection) as observing:
            with self.assertRaises(ContractRefusal) as caught:
                grant_writer(self.store, line_id=line["line_id"],
                             attempt_id="writer-attempt-1", generation=1,
                             worker_id="worker-1", profile=self.profile)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("runtime-observation", "identity-mismatch"))
        self.assertIn("names another object", caught.exception.message)
        self.assertEqual(observing.under_lock, [])
        beside = sqlite3.connect(self.control_path, isolation_level=None)
        try:
            self.assertEqual(list(beside.execute(
                "SELECT state FROM line_writers")), [])
        finally:
            beside.close()

    def test_a_line_whose_recorded_group_no_longer_holds_admits_nobody(self):
        """AND THE ACCESS HALF OF THE SAME PROOF, not only the object identity.

        `_prove_line_access` measures the configured group and mode `02775` and
        explicitly does not repair them. Mode is the member this case can change
        without another group on the host, so the line root is made `0700` -- the
        exact state the accepted contract calls out as denying what the grant is
        for.
        """
        line = self.line()
        self.attempt("writer-attempt-1", 1, "baton.impl", "writer-1")
        os.chmod(line["path"], 0o700)
        with AnOpenTransaction(self.store._connection) as observing:
            with self.assertRaises(ContractRefusal) as caught:
                grant_writer(self.store, line_id=line["line_id"],
                             attempt_id="writer-attempt-1", generation=1,
                             worker_id="worker-1", profile=self.profile)
        self.assertIn("admission does not repair it", caught.exception.message)
        self.assertEqual(observing.under_lock, [])
        self.assertEqual(self.row(line["line_id"])["state"], "idle")

    def test_a_correction_naming_a_checkpoint_the_line_left_is_refused(self):
        """CHANGED CHECKPOINT, at the branch that validates one."""
        line, checkpoint = self.correction_ready()
        self.attempt("writer-attempt-2", 2, "baton.impl", "writer-2")
        with self.assertRaises(ContractRefusal) as caught:
            grant_writer(self.store, line_id=line["line_id"],
                         attempt_id="writer-attempt-2", generation=2,
                         worker_id="worker-2", profile=self.profile,
                         based_checkpoint_id="checkpoint-nobody-froze")
        self.assertEqual(caught.exception.category, "stale-assignment")
        self.assertIn("must name the current checkpoint",
                      caught.exception.message)
        self.assertEqual(self.row(line["line_id"])["state"],
                         "correction-ready")

    def test_a_correction_whose_line_moved_off_its_checkpoint_is_refused(self):
        """AND THE PROFILE'S OWN CURRENT-CHECKPOINT VALIDATION, outside the lock."""
        line, checkpoint = self.correction_ready()
        self.attempt("writer-attempt-2", 2, "baton.impl", "writer-2")
        self.profile.current_revision = 99
        with AnOpenTransaction(self.store._connection) as observing:
            with self.assertRaises(ContractRefusal) as caught:
                grant_writer(
                    self.store, line_id=line["line_id"],
                    attempt_id="writer-attempt-2", generation=2,
                    worker_id="worker-2", profile=self.profile,
                    based_checkpoint_id=checkpoint["checkpoint_id"])
        self.assertIn("no longer matches", caught.exception.message)
        self.assertEqual(observing.under_lock, [])
        self.assertEqual(self.row(line["line_id"])["state"],
                         "correction-ready")

    def test_a_row_changed_after_its_proof_refuses_under_the_lock(self):
        """THE PIN IS COMPARED, and this is the case that drives the comparison.

        The recorded object triple is written once at line creation and never
        updated, so no supported operation can move it -- which means the in-lock
        comparison is a fail-closed binding against an out-of-band row edit
        rather than an ordinary transition. It is driven here by editing the row
        at the EXACT cut point: `_prove_line_access` is the last act of the proof,
        so this changes the recorded inode as that call returns, and the
        admission then holds its pin against a row that no longer agrees.

        CONTROLLED AND LABELLED: the edit is this module's, at a seam the product
        does not offer. What is measured is that the product refuses rather than
        writing a grant whose proof was about another object.
        """
        line = self.line()
        self.attempt("writer-attempt-1", 1, "baton.impl", "writer-1")
        honest = workspaces._prove_line_access
        edited = []

        def proving(place, pinned, gid):
            answer = honest(place, pinned, gid)
            if not edited:
                edited.append(True)
                self.store._connection.execute(
                    "UPDATE review_lines SET line_inode = line_inode + 1 "
                    "WHERE line_id = ?", (line["line_id"],))
            return answer

        with mock.patch.object(workspaces, "_prove_line_access", proving):
            with self.assertRaises(ContractRefusal) as caught:
                grant_writer(self.store, line_id=line["line_id"],
                             attempt_id="writer-attempt-1", generation=1,
                             worker_id="worker-1", profile=self.profile)
        self.assertEqual(edited, [True])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("runtime-observation", "identity-mismatch"))
        self.assertIn("no longer names the object this writer admission proved",
                      caught.exception.message)
        # NOTHING WAS ADMITTED and the line is untouched.
        beside = sqlite3.connect(self.control_path, isolation_level=None)
        try:
            self.assertEqual(list(beside.execute(
                "SELECT state FROM line_writers")), [])
        finally:
            beside.close()
        self.assertEqual(self.row(line["line_id"])["state"], "idle")


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only the cases defined in THIS module.

    The accepted `tests.manager.test_review_cycles` fixtures are imported for
    their profile and port; its own cases stay that suite's evidence and are not
    counted here.
    """
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
