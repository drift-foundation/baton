import contextlib
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.worker_manager import (ControlStore, attach_review,
                                      audit_checkpoint, checkpoint_of,
                                      create_line,
                                      freeze_checkpoint, grant_writer,
                                      integration_checkpoint, line_of,
                                      line_status, record_progress,
                                      record_verdict, review_boundary,
                                      review_for_attempt, review_of,
                                      verdict_of, writer_boundary,
                                      writer_for_attempt, writer_of)
from baton_v12.worker_manager import review_cycles
from baton_v12.worker_manager.review_cycles import (ATTACH_KIND, GRANT_KIND,
                                                     RESTORE_KIND,
                                                     abandoned_correction_of,
                                                     restore_abandoned_correction,
                                                     settle_restoration_execution)
from baton_v12.worker_manager.source_boundary import (adopt_source_boundary,
                                                       boundary_mounts,
                                                       compose_runtime_storage_boundary,
                                                       compose_source_boundary,
                                                       nominate_source,
                                                       workspace_capacity)
from baton_v12.worker_manager.workspaces import (assignment_workspace,
                                                 configure_workspace_storage,
                                                 discard_execution_roots,
                                                 discard_workspace)
from . import input_roots
from .disk_roots import disk_backed_under


NOW = "2026-09-05T12:00:00.000Z"
AUTHORITY = "0123456789abcdef0123456789abcdef"
WORK = "01234567-W71918"
BASE = "a" * 40
# W275774: the policy an attempt's delivery is made under, which every real
# attempt row carries and a runtime is labelled with. Distinct from the
# RETENTION digest below, which is the abandonment's own policy operand.
DELIVERY_POLICY = "sha256:" + "5" * 64
# W275774: the command the restoration's launch account is taken over.
#
# W257624 made `restore_abandoned_correction` refuse without BOTH a launcher and
# a cessation observer, because external work that is not recorded before it
# exists can never be accounted for -- and these cases predate that pair. The
# pair they are now given is THE DEPLOYMENT'S OWN, from `tools.stage_execution`:
# the launcher commits each command's intent before its child exists and its
# group immediately after the fork, and the observer answers through the kernel.
# So the account is a real one and the ending is proved rather than asserted.
#
# WHAT THE FIXTURE SUPPLIES IS THE COMMAND, AND IT IS A NO-OP. The profile below
# writes no checkout, so there is no reset and no clean to route; this stands
# exactly where the real profile's two write commands are, for the one purpose of
# making the launch account genuine instead of composed. No case asserts anything
# about it, and nothing here claims the fixture restored a repository.
RESTORATION_COMMAND = ["/bin/true"]


class Port:
    def __init__(self, participant):
        self.participant = participant
        self.calls = []

    def cancel(self, expect, operation_id, reason, work_id, authority_uuid):
        answer = {"operation_id": operation_id, "participant": self.participant,
                  "generation": expect["generation"], "status": "fenced"}
        self.calls.append((dict(expect), operation_id, reason, work_id,
                           authority_uuid))
        return answer


class Profile:
    name = "test-profile"

    def __init__(self):
        self.held = {}
        self.freeze_calls = []
        self.materialize_calls = 0
        self.current_revision = None
        self.restore_calls = []
        self.restore_runs = []
        self.validate_runs = []

    def materialize(self, source, repository, declared_base):
        self.materialize_calls += 1
        if not os.path.exists(repository):
            os.mkdir(repository)
        return {"profile": self.name, "base": declared_base,
                "head": declared_base}

    def freeze(self, repository, *, line_id, revision, declared_base):
        self.freeze_calls.append((repository, revision))
        head = f"{revision:040x}"
        paths = [f"round-{revision}.txt"]
        evidence = {"profile": self.name, "base": declared_base,
                    "head": head, "tree": f"{revision + 100:040x}",
                    "paths": paths, "path_set_digest": digest(paths),
                    "reference": f"checkpoint/{line_id}/{revision}"}
        self.held[revision] = evidence
        self.current_revision = revision
        return dict(evidence)

    def validate(self, repository, evidence, *, current=False, runner=None):
        """W275774: and the ROUTED COMMAND, because a settlement's reads are work
        too.

        `settle_restoration_execution` validates the retained checkpoint through a
        runner of its own, under its own episode label, precisely so that the
        commands its validation runs are accounted for beside the executor's --
        "they are only reads" being the assumption that was wrong before. So this
        stand-in takes the operand and routes the no-op where those commands are;
        every other caller of `validate` passes none and is unaffected.
        """
        if runner is not None:
            self.validate_runs.append(runner(RESTORATION_COMMAND))
        revision = int(evidence["head"], 16)
        if self.held.get(revision) != evidence:
            raise ContractRefusal("policy", "profile-uncertified",
                                  "checkpoint evidence is not retained")
        if current and self.current_revision != revision:
            raise ContractRefusal("policy", "profile-uncertified",
                                  "the line no longer matches this checkpoint")
        return dict(evidence)

    # W128692: the capability the abandoned-correction restore requires.
    # ADDITIVE, and it models exactly what the real profile does: the
    # checkpoint is verified before any write, the ONE nominated checkout is
    # put back on it, and the same evidence is answered only after a
    # `current=True` validation succeeds. `restore_refusal` is how a case asks
    # for a failed restoration without reaching a real filesystem.
    restore_refusal = None

    def restore_checkpoint(self, repository, evidence, *, runner=None):
        """W275774: and the ROUTED COMMAND, in the real profile's own order.

        The production profile takes `runner` per invocation and routes exactly
        the two commands that write the checkout through it, AFTER the
        before-any-write validation. So the runner is invoked here and not
        earlier: a restoration that refuses at that validation has started no
        external work, and recording a launch for it would account for a child
        that never existed.
        """
        self.restore_calls.append((repository, dict(evidence)))
        self.validate(repository, evidence)
        if self.restore_refusal is not None:
            raise self.restore_refusal
        if runner is not None:
            self.restore_runs.append(runner(RESTORATION_COMMAND))
        self.current_revision = int(evidence["head"], 16)
        return self.validate(repository, evidence, current=True)


class ReviewCycles(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.source = os.path.join(self.temporary.name, "source")
        self.storage = os.path.join(disk_backed_under(self), "storage")
        os.mkdir(self.source)
        os.mkdir(self.storage)
        self.control_path = os.path.join(self.temporary.name, "control.sqlite3")
        self.store = ControlStore.open(
            self.control_path,
            incarnation="manager-1", clock=lambda: NOW)
        self.profile = Profile()
        self.group = input_roots.configured_group(self.store)
        configure_workspace_storage(self.store, self.storage)
        self.ports = {}

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    def attempt(self, attempt_id, generation, participant, principal):
        # W275774: AND THE POLICY ITS DELIVERY WAS MADE UNDER. `_runtime_labels`
        # refuses an attempt whose `policy_digest` is null -- a runtime is
        # labelled with that policy and reconciliation has no other way to learn
        # it -- so a row without one cannot reach a real start at all. Every real
        # delivery records it; this fixture's row-level composition simply never
        # did, because nothing here used to start anything.
        self.store._connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, policy_digest, created_at, work_id, "
            "authority_uuid, assignment_participant, assignment_generation, "
            "assignment_claim_event_seq, assignment_principal, assignment_scope, "
            "assignment_role, assignment_grant, assignment_policy_generation) "
            "VALUES (?, 'adapter', 'adapter-digest', 'profile-digest', ?, ?, ?, ?, "
            "?, ?, ?, ?, 'scope', 'role', 'grant', 1)",
            (attempt_id, DELIVERY_POLICY, NOW, WORK, AUTHORITY, participant,
             generation, generation, principal))
        return attempt_id

    def line(self):
        source = nominate_source(self.source)
        return create_line(self.store, source=source,
                           declared_base=BASE, profile=self.profile,
                           authority_uuid=AUTHORITY, work_id=WORK)

    def port(self, participant):
        return self.ports.setdefault(participant, Port(participant))

    def complete(self, attempt_id, *, review=False, findings=True, logs=True):
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = 'quiescent', "
            "worker_disposition = 'completed' WHERE runtime_attempt_id = ?",
            ("runtime-" + attempt_id, attempt_id))
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
        for name, present in (("findings", findings), ("logs", logs)):
            if present:
                self.store._connection.execute(
                    "INSERT INTO output_artifacts (runtime_attempt_id, output_name, "
                    "artifact_id, media_type, bytes, content_digest, locator) "
                    "VALUES (?, ?, ?, 'text/plain', 1, ?, ?)",
                    (attempt_id, name, f"artifact-{name}-{attempt_id}",
                     "sha256:" + ("2" if name == "findings" else "3") * 64,
                     f"custody/{attempt_id}/{name}"))

    def freeze(self, writer, generation):
        attempt_id = f"writer-attempt-{generation}"
        self.complete(attempt_id)
        return freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=generation,
            profile=self.profile, port=self.port("baton.impl"))

    def verdict(self, review, round_number, disposition):
        self.complete(f"review-attempt-{round_number}", review=True)
        return record_verdict(
            self.store, attachment_id=review["attachment_id"],
            disposition=disposition, profile=self.profile,
            port=self.port("baton.review"))

    def writer(self, line_id, round_number, based=None):
        attempt = self.attempt(f"writer-attempt-{round_number}", round_number,
                               "baton.impl", f"writer-{round_number}")
        return grant_writer(self.store, line_id=line_id, attempt_id=attempt,
                            generation=round_number,
                            worker_id=f"worker-{round_number}",
                            profile=self.profile,
                            based_checkpoint_id=based)

    def review(self, checkpoint_id, round_number):
        attempt = self.attempt(f"review-attempt-{round_number}", round_number,
                               "baton.review", f"reviewer-{round_number}")
        return attach_review(
            self.store, checkpoint_id=checkpoint_id, attempt_id=attempt,
            generation=round_number,
            reviewer_worker_id=f"review-worker-{round_number}",
            profile=self.profile)

    def test_line_and_each_operation_replay_exactly(self):
        line = self.line()
        self.assertEqual(self.line(), line)
        self.assertEqual(line_status(
            self.store, line["line_id"],
            lambda path: {"bytes": 0, "entries": 0})["storage"],
            {"bytes": 0, "entries": 0})
        writer = self.writer(line["line_id"], 1)
        replay = grant_writer(
            self.store, line_id=line["line_id"],
            attempt_id="writer-attempt-1", generation=1,
            worker_id="worker-1", profile=self.profile)
        self.assertEqual(replay, writer)
        self.assertEqual(
            record_progress(self.store, writer_id=writer["writer_id"],
                            generation=1, sequence=1,
                            document={"status": "working"}),
            record_progress(self.store, writer_id=writer["writer_id"],
                            generation=1, sequence=1,
                            document={"status": "working"}))
        checkpoint = self.freeze(writer, 1)
        self.assertEqual(checkpoint, freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, port=self.port("baton.impl")))
        review = self.review(checkpoint["checkpoint_id"], 1)
        self.assertEqual(review, attach_review(
            self.store, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id="review-attempt-1", generation=1,
            reviewer_worker_id="review-worker-1", profile=self.profile))
        verdict = self.verdict(review, 1, "accepted")
        self.assertEqual(verdict, record_verdict(
            self.store, attachment_id=review["attachment_id"],
            disposition="accepted", profile=self.profile,
            port=self.port("baton.review")))
        eligible = integration_checkpoint(self.store, line["line_id"])
        self.assertEqual(eligible["checkpoint_id"], checkpoint["checkpoint_id"])

    def test_ten_corrections_reuse_line_and_retain_old_checkpoints(self):
        line = self.line()
        place = line["path"]
        identity = os.stat(place).st_ino
        prior = None
        checkpoints = []
        operations = []
        with mock.patch("os.statvfs", side_effect=AssertionError(
                "review lines have no predictive capacity probe")):
            for round_number in range(1, 11):
                writer = self.writer(line["line_id"], round_number, prior)
                progress = record_progress(
                    self.store, writer_id=writer["writer_id"],
                    generation=round_number, sequence=1,
                    document={"round": round_number})
                checkpoint = self.freeze(writer, round_number)
                checkpoints.append(checkpoint["checkpoint_id"])
                review = self.review(checkpoint["checkpoint_id"], round_number)
                disposition = ("accepted" if round_number == 10
                               else "changes-requested")
                verdict = self.verdict(review, round_number, disposition)
                operations.append((round_number, writer, progress, checkpoint,
                                   review, disposition, verdict))
                prior = checkpoint["checkpoint_id"]
        current = line_of(self.store, line["line_id"])
        self.assertEqual((current["revision"], current["state"]), (10, "accepted"))
        self.assertEqual(os.stat(place).st_ino, identity)
        self.assertEqual(self.line(), line)
        self.assertEqual(self.profile.materialize_calls, 1)
        for (round_number, writer, progress, checkpoint, review, disposition,
             verdict) in operations:
            self.assertEqual(record_progress(
                self.store, writer_id=writer["writer_id"],
                generation=round_number, sequence=1,
                document={"round": round_number}), progress)
            self.assertEqual(freeze_checkpoint(
                self.store, writer_id=writer["writer_id"],
                generation=round_number, profile=self.profile,
                port=self.port("baton.impl")), checkpoint)
            self.assertEqual(attach_review(
                self.store, checkpoint_id=checkpoint["checkpoint_id"],
                attempt_id=f"review-attempt-{round_number}",
                generation=round_number,
                reviewer_worker_id=f"review-worker-{round_number}",
                profile=self.profile), review)
            self.assertEqual(record_verdict(
                self.store, attachment_id=review["attachment_id"],
                disposition=disposition, profile=self.profile,
                port=self.port("baton.review")), verdict)
        for checkpoint_id in checkpoints:
            self.assertEqual(audit_checkpoint(self.store, checkpoint_id,
                                              self.profile)["profile"],
                             self.profile.name)
        self.assertEqual(self.store._connection.execute(
            "SELECT count(*) FROM line_checkpoints").fetchone()[0], 10)

    def test_writer_is_revoked_before_profile_runs_and_crash_resumes(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        original = self.profile.freeze
        calls = 0

        def crash(repository, **arguments):
            nonlocal calls
            calls += 1
            state = self.store._connection.execute(
                "SELECT state FROM line_writers WHERE writer_id = ?",
                (writer["writer_id"],)).fetchone()[0]
            self.assertEqual(state, "revoked")
            if calls == 1:
                raise RuntimeError("simulated profile crash")
            return original(repository, **arguments)

        self.profile.freeze = crash
        self.complete("writer-attempt-1")
        with self.assertRaisesRegex(RuntimeError, "simulated"):
            freeze_checkpoint(self.store, writer_id=writer["writer_id"],
                              generation=1, profile=self.profile,
                              port=self.port("baton.impl"))
        self.assertEqual(line_of(self.store, line["line_id"])["state"],
                         "freezing")
        checkpoint = freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, port=self.port("baton.impl"))
        self.assertEqual(checkpoint["revision"], 1)

    def test_line_materialization_crash_resumes_only_the_recorded_operands(self):
        original = self.profile.materialize

        def crash(source, repository, declared_base):
            original(source, repository, declared_base)
            raise RuntimeError("simulated materialization crash")

        self.profile.materialize = crash
        with self.assertRaisesRegex(RuntimeError, "materialization"):
            self.line()
        row = self.store._connection.execute(
            "SELECT state FROM review_lines").fetchone()
        self.assertEqual(row[0], "materializing")
        other = os.path.join(self.temporary.name, "other-source")
        os.mkdir(other)
        with self.assertRaises(ContractRefusal) as caught:
            create_line(
                self.store,
                source=nominate_source(other), declared_base=BASE,
                profile=self.profile, authority_uuid=AUTHORITY, work_id=WORK)
        self.assertEqual(caught.exception.code, "operation-collision")
        self.profile.materialize = original
        self.assertEqual(self.line()["state"], "idle")

    def test_review_independence_and_exact_verdict_collision(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        checkpoint = self.freeze(writer, 1)
        collisions = (
            ("same-worker-review", "baton.other", "other-principal",
             "worker-1", "worker"),
            ("same-participant-review", "baton.impl", "other-principal",
             "different-worker", "participant"),
            ("same-principal-review", "baton.other", "writer-1",
             "different-worker", "principal"),
        )
        for generation, collision in enumerate(collisions, 2):
            attempt, participant, principal, worker_id, label = collision
            self.attempt(attempt, generation, participant, principal)
            with self.subTest(identity=label), self.assertRaisesRegex(
                    ContractRefusal, label):
                attach_review(
                    self.store, checkpoint_id=checkpoint["checkpoint_id"],
                    attempt_id=attempt, generation=generation,
                    reviewer_worker_id=worker_id, profile=self.profile)
        review = self.review(checkpoint["checkpoint_id"], 1)
        self.verdict(review, 1, "accepted")
        with self.assertRaises(ContractRefusal) as caught:
            record_verdict(self.store, attachment_id=review["attachment_id"],
                           disposition="rejected", profile=self.profile,
                           port=self.port("baton.review"))
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_checkpoint_redundant_columns_must_match_sealed_evidence(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        checkpoint = self.freeze(writer, 1)
        self.store._connection.execute(
            "UPDATE line_checkpoints SET checkpoint_digest = ? "
            "WHERE checkpoint_id = ?",
            ("sha256:" + "0" * 64, checkpoint["checkpoint_id"]))
        with self.assertRaises(ContractRefusal) as caught:
            audit_checkpoint(self.store, checkpoint["checkpoint_id"],
                             self.profile)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "digest"))

    def test_verdict_refuses_an_attachment_retargeted_to_another_line(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        checkpoint = self.freeze(writer, 1)
        review = self.review(checkpoint["checkpoint_id"], 1)
        other = create_line(
            self.store, source=nominate_source(self.source),
            declared_base=BASE, profile=self.profile,
            authority_uuid="fedcba9876543210fedcba9876543210", work_id=WORK)
        self.store._connection.execute(
            "UPDATE review_attachments SET line_id = ? WHERE attachment_id = ?",
            (other["line_id"], review["attachment_id"]))
        with self.assertRaises(ContractRefusal) as caught:
            record_verdict(self.store, attachment_id=review["attachment_id"],
                           disposition="accepted", profile=self.profile,
                           port=self.port("baton.review"))
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))

    def test_integration_requires_the_exact_accepted_verdict_row(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        checkpoint = self.freeze(writer, 1)
        review = self.review(checkpoint["checkpoint_id"], 1)
        verdict = self.verdict(review, 1, "accepted")
        self.assertEqual(integration_checkpoint(
            self.store, line["line_id"])["verdict_id"], verdict["verdict_id"])
        self.store._connection.execute(
            "UPDATE checkpoint_verdicts SET disposition = 'rejected' "
            "WHERE verdict_id = ?", (verdict["verdict_id"],))
        with self.assertRaises(ContractRefusal) as caught:
            integration_checkpoint(self.store, line["line_id"])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "digest"))

    def test_verdict_requires_quiescent_frozen_verified_findings_and_logs(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        checkpoint = self.freeze(writer, 1)
        review = self.review(checkpoint["checkpoint_id"], 1)
        port = self.port("baton.review")
        with self.assertRaisesRegex(ContractRefusal, "positively quiescent"):
            record_verdict(
                self.store, attachment_id=review["attachment_id"],
                disposition="accepted", profile=self.profile, port=port)
        self.assertEqual(port.calls, [])
        self.complete("review-attempt-1", review=True, logs=False)
        with self.assertRaisesRegex(ContractRefusal, "findings and logs"):
            record_verdict(
                self.store, attachment_id=review["attachment_id"],
                disposition="accepted", profile=self.profile, port=port)
        self.assertEqual(port.calls, [])
        self.store._connection.execute(
            "INSERT INTO output_artifacts (runtime_attempt_id, output_name, "
            "artifact_id, media_type, bytes, content_digest, locator) VALUES "
            "('review-attempt-1', 'logs', 'artifact-logs-review-attempt-1', "
            "'text/plain', 1, ?, 'custody/review-attempt-1/logs')",
            ("sha256:" + "3" * 64,))
        # W110772, owner ruling M111752: THE REVIEWER'S OWN VERIFICATION AXIS
        # IS NO LONGER A PREREQUISITE, and this expectation is replaced rather
        # than dropped. For this milestone the implementer runs the ordinary
        # required tests and an independent reviewer assesses the checkpoint;
        # there is no producer that could write `passed` into a REVIEW
        # attempt's axis, so requiring one made every honest review
        # unsettleable. The quiescence, disposition, findings and logs
        # refusals above are untouched, and so is every no-side-effect
        # assertion.
        #
        # NO AXIS IS FORGED AND NONE IS RESET, which is the half worth
        # driving: the verdict is recorded with the axis left exactly as each
        # value below found it.
        # Each axis is exercised through a fresh verdict in the separate case
        # below; writing and reading it before one final verdict proved nothing.
        self.store._connection.execute(
            "UPDATE attempts SET verification = 'none' "
            "WHERE runtime_attempt_id = 'review-attempt-1'")
        record_verdict(
            self.store, attachment_id=review["attachment_id"],
            disposition="accepted", profile=self.profile, port=port)
        self.assertEqual(len(port.calls), 1)
        self.assertIsNotNone(integration_checkpoint(self.store, line["line_id"]))
        # AND THE AXIS THE REVIEW ATTEMPT CARRIES IS STILL `none`.
        self.assertEqual(self.store._connection.execute(
            "SELECT verification FROM attempts WHERE "
            "runtime_attempt_id = 'review-attempt-1'").fetchone()[0], "none")

    def test_each_reviewer_axis_records_a_fresh_verdict_without_changing_the_axis(self):
        for axis in ("none", "failed", "unable"):
            with self.subTest(verification=axis):
                fresh = ReviewCycles()
                fresh.setUp()
                try:
                    line = fresh.line()
                    checkpoint = fresh.freeze(fresh.writer(line["line_id"], 1), 1)
                    review = fresh.review(checkpoint["checkpoint_id"], 1)
                    fresh.complete("review-attempt-1", review=True)
                    fresh.store._connection.execute(
                        "UPDATE attempts SET verification = ? WHERE runtime_attempt_id = 'review-attempt-1'", (axis,))
                    port = fresh.port("baton.review")
                    self.assertEqual(port.calls, [])
                    verdict = record_verdict(fresh.store, attachment_id=review["attachment_id"],
                        disposition="accepted", profile=fresh.profile, port=port)
                    self.assertEqual(fresh.store._connection.execute(
                        "SELECT verification FROM attempts WHERE runtime_attempt_id = 'review-attempt-1'").fetchone()[0], axis)
                    self.assertEqual(len(port.calls), 1)
                    self.assertEqual(fresh.store._connection.execute(
                        "SELECT count(*) FROM checkpoint_verdicts").fetchone()[0], 1)
                    self.assertEqual(integration_checkpoint(fresh.store, line["line_id"])["verdict_id"], verdict["verdict_id"])
                finally:
                    fresh.tearDown()
                    fresh.doCleanups()

    def test_live_child_and_stale_progress_refuse_without_mutation(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = 'runtime-writer-attempt-1', "
            "execution_runtime = 'running', worker_disposition = 'completed' "
            "WHERE runtime_attempt_id = 'writer-attempt-1'")
        with self.assertRaises(ContractRefusal):
            freeze_checkpoint(self.store, writer_id=writer["writer_id"],
                              generation=1, profile=self.profile,
                              port=self.port("baton.impl"))
        self.assertEqual(line_of(self.store, line["line_id"])["state"], "writing")
        with self.assertRaises(ContractRefusal) as caught:
            record_progress(self.store, writer_id=writer["writer_id"],
                            generation=2, sequence=1, document={"status": "late"})
        self.assertEqual(caught.exception.category, "stale-assignment")

    def test_writer_and_review_mount_the_line_without_copying_or_sharing_output(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        writer_roots = assignment_workspace(
            self.group, self.storage, "writer-attempt-1")
        with self.assertRaisesRegex(ContractRefusal, "live grant"):
            compose_runtime_storage_boundary(
                nominate_source(self.source), writer_roots)
        with mock.patch("os.statvfs", side_effect=AssertionError(
                "runtime-provided line storage is not predictively measured")):
            writable = writer_boundary(
                self.store, writer_id=writer["writer_id"], generation=1)
            with self.assertRaisesRegex(ContractRefusal, "revocable live grant"):
                compose_source_boundary(
                    nominate_source(self.source), writable["roots"],
                    workspace_capacity(100 * 1024 * 1024))
            adopted = adopt_source_boundary(
                writable["boundary"], writable["roots"], pinned=(
                    (writable["boundary"].device,
                     writable["boundary"].inode),
                    (writable["boundary"].workspace_device,
                     writable["boundary"].workspace_inode)))
        self.assertEqual(boundary_mounts(writable["boundary"]), (
            (self.source, "/input/source", False),
            (line["path"], "/output", True)))
        self.assertEqual(writable["roots"]["inputs"], writer_roots["inputs"])
        self.assertNotEqual(writable["roots"]["workspace"],
                            writer_roots["workspace"])
        self.assertEqual(boundary_mounts(adopted),
                         boundary_mounts(writable["boundary"]))
        checkpoint = self.freeze(writer, 1)
        with self.assertRaisesRegex(ContractRefusal, "revoked"):
            boundary_mounts(writable["boundary"])
        with self.assertRaisesRegex(ContractRefusal, "revoked"):
            adopt_source_boundary(writable["boundary"], writable["roots"])
        discard_execution_roots(self.storage, "writer-attempt-1", control=self.store)
        self.assertTrue(os.path.isdir(line["path"]))

        review = self.review(checkpoint["checkpoint_id"], 1)
        review_roots = assignment_workspace(
            self.group, self.storage, "review-attempt-1")
        with mock.patch("os.statvfs", side_effect=AssertionError(
                "runtime-provided line storage is not predictively measured")):
            readonly = review_boundary(
                self.store, attachment_id=review["attachment_id"],
                profile=self.profile)
        self.assertEqual(boundary_mounts(readonly["boundary"]), (
            (line["path"], "/input/source", False),
            (review_roots["workspace"], "/output", True)))
        self.assertNotEqual(readonly["boundary"].source.place,
                            readonly["boundary"].workspace)
        self.verdict(review, 1, "accepted")
        with self.assertRaisesRegex(ContractRefusal, "revoked"):
            boundary_mounts(readonly["boundary"])
        discard_execution_roots(self.storage, "review-attempt-1", control=self.store)
        self.assertTrue(os.path.isdir(line["path"]))

    def test_review_mount_revalidates_the_current_checkpoint(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        checkpoint = self.freeze(writer, 1)
        review = self.review(checkpoint["checkpoint_id"], 1)
        assignment_workspace(self.group, self.storage, "review-attempt-1")
        self.profile.current_revision = 99
        with self.assertRaisesRegex(ContractRefusal, "no longer matches"):
            review_boundary(
                self.store, attachment_id=review["attachment_id"],
                profile=self.profile)

    def test_restart_preserves_review_to_correction_and_rejected_is_ineligible(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        record_progress(self.store, writer_id=writer["writer_id"],
                        generation=1, sequence=1, document={"status": "ready"})
        checkpoint = self.freeze(writer, 1)
        self.store.close()
        self.store = ControlStore.open(
            self.control_path, incarnation="manager-after-freeze",
            clock=lambda: NOW)
        review = self.review(checkpoint["checkpoint_id"], 1)
        self.verdict(review, 1, "changes-requested")
        self.assertIsNone(integration_checkpoint(self.store, line["line_id"]))
        self.store.close()
        self.store = ControlStore.open(
            self.control_path, incarnation="manager-after-verdict",
            clock=lambda: NOW)
        correction = self.writer(line["line_id"], 2,
                                 checkpoint["checkpoint_id"])
        corrected = self.freeze(correction, 2)
        second_review = self.review(corrected["checkpoint_id"], 2)
        self.verdict(second_review, 2, "rejected")
        self.assertIsNone(integration_checkpoint(self.store, line["line_id"]))
        self.assertEqual(line_of(self.store, line["line_id"])["state"],
                         "rejected")
        self.assertEqual(audit_checkpoint(
            self.store, checkpoint["checkpoint_id"], self.profile)["head"],
            checkpoint["evidence"]["head"])

    def test_correction_refuses_if_the_line_no_longer_matches_its_checkpoint(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        checkpoint = self.freeze(writer, 1)
        review = self.review(checkpoint["checkpoint_id"], 1)
        self.verdict(review, 1, "changes-requested")
        self.attempt("writer-attempt-2", 2, "baton.impl", "writer-2")
        self.profile.current_revision = 99
        with self.assertRaisesRegex(ContractRefusal, "no longer matches"):
            grant_writer(
                self.store, line_id=line["line_id"],
                attempt_id="writer-attempt-2", generation=2,
                worker_id="worker-2", profile=self.profile,
                based_checkpoint_id=checkpoint["checkpoint_id"])
        self.assertEqual(line_of(self.store, line["line_id"])["state"],
                         "correction-ready")

    def test_authority_and_work_identity_isolate_line_custody(self):
        first = self.line()
        source = nominate_source(self.source)
        second = create_line(
            self.store, source=source,
            declared_base=BASE, profile=self.profile,
            authority_uuid="fedcba9876543210fedcba9876543210", work_id=WORK)
        third = create_line(
            self.store, source=source,
            declared_base=BASE, profile=self.profile,
            authority_uuid=AUTHORITY, work_id="01234567-W71919")
        self.assertEqual(len({first["line_id"], second["line_id"],
                              third["line_id"]}), 3)
        self.assertEqual(len({first["path"], second["path"], third["path"]}), 3)

    def test_line_custody_is_derived_only_from_configured_storage(self):
        nested_storage = os.path.join(self.source, "storage")
        os.mkdir(nested_storage)
        with self.assertRaises(TypeError):
            create_line(
                self.store, storage=nested_storage,
                source=nominate_source(self.source), declared_base=BASE,
                profile=self.profile, authority_uuid=AUTHORITY, work_id=WORK)
        self.assertFalse(os.path.exists(os.path.join(
            nested_storage, ".baton-review-lines")))
        line = self.line()
        self.assertTrue(line["path"].startswith(
            os.path.join(self.storage, ".baton-review-lines") + os.sep))

    def test_writer_race_has_one_winner_and_reserved_line_survives_cleanup(self):
        line = self.line()
        self.attempt("race-a", 1, "baton.a", "principal-a")
        self.attempt("race-b", 2, "baton.b", "principal-b")
        outcomes = []
        barrier = threading.Barrier(2)

        def contender(attempt, generation):
            beside = ControlStore.open(
                self.control_path, incarnation=f"manager-{generation + 1}",
                clock=lambda: NOW)
            try:
                barrier.wait()
                outcomes.append(grant_writer(
                    beside, line_id=line["line_id"], attempt_id=attempt,
                    generation=generation,
                    worker_id=f"race-worker-{generation}",
                    profile=self.profile))
            except ContractRefusal as refusal:
                outcomes.append(refusal)
            finally:
                beside.close()

        threads = [threading.Thread(target=contender, args=("race-a", 1)),
                   threading.Thread(target=contender, args=("race-b", 2))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sum(type(answer) is dict for answer in outcomes), 1)
        self.assertEqual(sum(type(answer) is ContractRefusal
                             for answer in outcomes), 1)
        for identity in (".baton-review-lines", ".baton-review-lines/child",
                         "other/../.baton-review-lines"):
            with self.subTest(identity=identity), self.assertRaises(ContractRefusal):
                discard_workspace(self.storage, identity, control=self.store)
        self.assertTrue(os.path.isdir(line["path"]))


if __name__ == "__main__":
    unittest.main()


class TypedReadersAnswerRowsTheirOwnACTSExplain(unittest.TestCase):
    """W103076: `review_of` and `verdict_of`, and why they cross-bind.

    A composite outside this module has an attachment or a verdict IDENTITY and
    must not take the attempt, line or disposition beside it as separately
    chosen operands -- that is how one reviewer's output gets frozen and
    another's verdict recorded. These readers are the owner's answer, and each
    one proves the materialized row against the committed act that wrote it,
    so a row this manager cannot explain is refused rather than projected.
    """

    # THE FIXTURE IS BORROWED BY NAME RATHER THAN BY INHERITANCE. Subclassing
    # `ReviewCycles` would make unittest collect and re-run all seventeen of
    # its cases under this name too -- a silent duplication that inflates every
    # count in this suite without failing anything.
    setUp = ReviewCycles.setUp
    tearDown = ReviewCycles.tearDown
    attempt = ReviewCycles.attempt
    line = ReviewCycles.line
    port = ReviewCycles.port
    complete = ReviewCycles.complete
    freeze = ReviewCycles.freeze
    verdict = ReviewCycles.verdict
    writer = ReviewCycles.writer
    review = ReviewCycles.review

    def round(self, number, disposition, based=None):
        line = self.line()
        writer = self.writer(line["line_id"], number, based=based)
        checkpoint = self.freeze(writer, number)
        review = self.review(checkpoint["checkpoint_id"], number)
        verdict = self.verdict(review, number, disposition)
        return line, checkpoint, review, verdict

    def test_an_attachment_answers_its_own_runtime_attempt(self):
        line, checkpoint, review, _ = self.round(1, "accepted")
        answered = review_of(self.store, review["attachment_id"])
        self.assertEqual(answered["runtime_attempt_id"], "review-attempt-1")
        self.assertEqual(answered["checkpoint_id"],
                         checkpoint["checkpoint_id"])

    def test_an_attachment_nobody_attached_is_refused(self):
        self.round(1, "accepted")
        with self.assertRaises(ContractRefusal) as caught:
            review_of(self.store, "review-nobody-attached")
        self.assertEqual(caught.exception.category, "refused")

    def test_an_attachment_row_no_committed_act_explains_is_refused(self):
        """The cross-binding, driven: the row is real and the act is gone."""
        line, checkpoint, review, _ = self.round(1, "accepted")
        self.store._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            ("review-line.attach-review:" + review["attachment_id"],))
        with self.assertRaises(ContractRefusal) as caught:
            review_of(self.store, review["attachment_id"])
        self.assertIn("no committed", str(caught.exception))

    def test_a_verdict_answers_every_binding_it_was_recorded_with(self):
        line, checkpoint, review, verdict = self.round(1, "changes-requested")
        answered = verdict_of(self.store, verdict["verdict_id"])
        self.assertEqual(answered["disposition"], "changes-requested")
        self.assertEqual(answered["line_id"], line["line_id"])
        self.assertEqual(answered["checkpoint_id"],
                         checkpoint["checkpoint_id"])
        self.assertEqual(answered["attachment_id"], review["attachment_id"])
        self.assertEqual(answered["work_id"], WORK)
        self.assertEqual(answered["authority_uuid"], AUTHORITY)

    def test_a_verdict_nobody_recorded_is_refused(self):
        self.round(1, "accepted")
        with self.assertRaises(ContractRefusal) as caught:
            verdict_of(self.store, "verdict-nobody-recorded")
        self.assertEqual(caught.exception.category, "refused")

    def test_a_verdict_row_that_disagrees_with_its_act_is_refused(self):
        """Two accounts of one decision have no tie-break, so neither wins."""
        _, _, _, verdict = self.round(1, "accepted")
        self.store._connection.execute(
            "UPDATE checkpoint_verdicts SET disposition = 'rejected' "
            "WHERE verdict_id = ?", (verdict["verdict_id"],))
        with self.assertRaises(ContractRefusal) as caught:
            verdict_of(self.store, verdict["verdict_id"])
        self.assertIn("disagree about disposition", str(caught.exception))

    def test_an_attachment_whose_attempt_was_rewritten_is_refused(self):
        """The third review's exact reproduction.

        `runtime_attempt_id` is foreign-key valid for the writer's attempt too,
        so a rewritten row stayed loadable and the reader answered it -- and a
        composite that trusts the answer stops and freezes another lane's
        runtime.
        """
        _, _, review, _ = self.round(1, "accepted")
        self.store._connection.execute(
            "UPDATE review_attachments SET runtime_attempt_id = "
            "'writer-attempt-1' WHERE attachment_id = ?",
            (review["attachment_id"],))
        with self.assertRaises(ContractRefusal) as caught:
            review_of(self.store, review["attachment_id"])
        self.assertIn("runtime_attempt_id", str(caught.exception))

    def test_every_immutable_attachment_member_is_bound_to_its_act(self):
        _, _, review, _ = self.round(1, "accepted")
        for column, value in (("assignment_generation", 9),
                              ("reviewer_worker_id", "review-worker-9"),
                              ("reviewer_participant", "baton.somebody"),
                              ("reviewer_principal", "reviewer-9")):
            with self.subTest(column=column):
                held = self.store._connection.execute(
                    f"SELECT {column} AS held FROM review_attachments "
                    f"WHERE attachment_id = ?",
                    (review["attachment_id"],)).fetchone()["held"]
                self.store._connection.execute(
                    f"UPDATE review_attachments SET {column} = ? "
                    f"WHERE attachment_id = ?",
                    (value, review["attachment_id"]))
                with self.assertRaises(ContractRefusal) as caught:
                    review_of(self.store, review["attachment_id"])
                self.assertIn(column, str(caught.exception))
                self.store._connection.execute(
                    f"UPDATE review_attachments SET {column} = ? "
                    f"WHERE attachment_id = ?",
                    (held, review["attachment_id"]))

    def test_a_verdict_whose_retained_digest_was_rewritten_is_refused(self):
        """The third review's other reproduction: another well-formed SHA-256
        was accepted, so a correction could be scheduled on a verdict whose
        retained evidence contradicted its act."""
        _, _, _, verdict = self.round(1, "accepted")
        self.store._connection.execute(
            "UPDATE checkpoint_verdicts SET review_result_digest = ? "
            "WHERE verdict_id = ?",
            ("sha256:" + "e" * 64, verdict["verdict_id"]))
        with self.assertRaises(ContractRefusal) as caught:
            verdict_of(self.store, verdict["verdict_id"])
        self.assertEqual(caught.exception.code, "digest")

    def test_a_verdict_whose_retained_fence_digest_was_rewritten_is_refused(self):
        _, _, _, verdict = self.round(1, "accepted")
        self.store._connection.execute(
            "UPDATE checkpoint_verdicts SET review_fence_digest = ? "
            "WHERE verdict_id = ?",
            ("sha256:" + "e" * 64, verdict["verdict_id"]))
        with self.assertRaises(ContractRefusal) as caught:
            verdict_of(self.store, verdict["verdict_id"])
        self.assertEqual(caught.exception.code, "digest")

    def test_every_immutable_verdict_member_is_bound_to_its_act(self):
        _, _, _, verdict = self.round(1, "accepted")
        for column, value in (
                ("review_assignment_generation", 9),
                ("reviewer_worker_id", "review-worker-9"),
                ("reviewer_participant", "baton.somebody"),
                ("reviewer_principal", "reviewer-9"),
                ("base_object", "b" * 40), ("head_object", "c" * 40),
                ("tree_object", "d" * 40),
                ("path_set_digest", "sha256:" + "f" * 64)):
            with self.subTest(column=column):
                held = self.store._connection.execute(
                    f"SELECT {column} AS held FROM checkpoint_verdicts "
                    f"WHERE verdict_id = ?",
                    (verdict["verdict_id"],)).fetchone()["held"]
                self.store._connection.execute(
                    f"UPDATE checkpoint_verdicts SET {column} = ? "
                    f"WHERE verdict_id = ?", (value, verdict["verdict_id"]))
                with self.assertRaises(ContractRefusal) as caught:
                    verdict_of(self.store, verdict["verdict_id"])
                self.assertIn(column, str(caught.exception))
                self.store._connection.execute(
                    f"UPDATE checkpoint_verdicts SET {column} = ? "
                    f"WHERE verdict_id = ?", (held, verdict["verdict_id"]))

    def test_a_verdict_whose_act_is_gone_is_refused(self):
        _, _, review, verdict = self.round(1, "accepted")
        self.store._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            ("review-line.verdict:" + review["attachment_id"],))
        with self.assertRaises(ContractRefusal) as caught:
            verdict_of(self.store, verdict["verdict_id"])
        self.assertIn("no committed", str(caught.exception))


class StableLineLifecycle(unittest.TestCase):
    """Initial-access checkpoint; reuse fixture builders, not inherited cases."""

    setUp = ReviewCycles.setUp
    tearDown = ReviewCycles.tearDown
    attempt = ReviewCycles.attempt
    line = ReviewCycles.line
    port = ReviewCycles.port
    complete = ReviewCycles.complete
    writer = ReviewCycles.writer
    freeze = ReviewCycles.freeze
    review = ReviewCycles.review
    verdict = ReviewCycles.verdict

    def mounted_writer(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        assignment_workspace(self.group, self.storage, "writer-attempt-1")
        delivered = writer_boundary(self.store, writer_id=writer["writer_id"], generation=1)
        return line, writer, delivered

    def labels(self):
        from baton_v12.worker_manager.attempts import assignment_of
        return assignment_of(self.store, "writer-attempt-1")

    def test_establishing_access_is_serialized_before_idle_and_never_repeated(self):
        """W194457's property, under W301404's mechanism.

        The property is unchanged and is still the point: the permission act happens
        while the line is still `materializing` -- so nothing can be granted a writer
        over a tree whose access has not been established -- and exactly once.

        WHAT CHANGED IS WHERE IT RUNS. It used to run INSIDE the creation transaction,
        and that is the DESIGN DB-1 violation W301404 corrects: the consumer's reached
        probe measured 46 `lstat` and one `fchmod` with `in_transaction=True`. So this
        case now asserts the opposite of what it asserted before -- NO transaction is
        open while the filesystem is touched -- and keeps every other assertion it
        made. Serialization does not come from the lock; it comes from the line being
        exclusively `materializing` until the conditional completion publishes it.
        """
        from baton_v12.worker_manager import workspaces
        original = workspaces.establish_line_access
        calls = []

        def establish(place, pinned, identity):
            self.assertFalse(self.store._connection.in_transaction,
                             "DB-1: the permission act holds a database transaction")
            self.assertEqual(self.store._connection.execute("SELECT state FROM review_lines").fetchone()[0],
                             "materializing")
            calls.append(place)
            return original(place, pinned, identity)

        with mock.patch.object(workspaces, "establish_line_access", side_effect=establish):
            line, writer, delivered = self.mounted_writer()
            self.assertEqual(workspaces._prove_execution_workspace(
                delivered["roots"], self.group.gid, self.labels()), line["path"])
            self.assertEqual(self.line(), line)
            grant_writer(self.store, line_id=line["line_id"], attempt_id="writer-attempt-1",
                         generation=1, worker_id="worker-1", profile=self.profile)
            checkpoint = self.freeze(writer, 1)
            review = self.review(checkpoint["checkpoint_id"], 1)
            assignment_workspace(self.group, self.storage, "review-attempt-1")
            readonly = review_boundary(self.store, attachment_id=review["attachment_id"], profile=self.profile)
            self.assertFalse(readonly["roots"]._line)
            self.verdict(review, 1, "changes-requested")
            self.writer(line["line_id"], 2, checkpoint["checkpoint_id"])
        self.assertEqual(calls, [line["path"]])
        self.assertEqual(os.stat(line["path"]).st_mode & 0o7777, 0o2775)

    def test_a_COMPETING_creator_is_refused_while_this_one_holds_the_line(self):
        """W301404 reviews 02-32-53Z then 02-43-58Z, and the second corrected the first fix.

        The hole was real: a competitor admitted mid-preparation settled the line, took a
        writer, and the first creator still permissioned the tree. My first answer put an
        atomic re-read immediately before the permission act, and the reviewer's boundary
        probe then switched at the actual `fchmod` -- after that read had committed -- and
        the stale act ran anyway. AN ADJACENT READ IS NOT A CRITICAL SECTION, and no read
        is close enough, because the effect is a syscall rather than a transaction.

        SO THE COMPETITOR IS REFUSED WHILE THE FIRST PREPARATION IS LIVE, which the review
        confirms is safe rather than a lost requirement: the historical probe admitted one
        to EXPOSE the defect, which is not the same as requiring it be admitted.

        THE FOUR FACTS: the competitor refuses while the holder is inside its own
        preparation, the holder still completes, the line is published exactly once, and
        the live-work entry below the root is untouched. Recovery after a death is a
        different schedule and is `test_line_materialization_crash_resumes_only_the_
        recorded_operands` plus the interruption case below.
        """
        from baton_v12.worker_manager import workspaces
        prove = workspaces.prove_line_integrity
        entered, refused, established = False, [], []

        def interleave(*args, **kwargs):
            """A competitor, driven at the same interval both reviewer probes use."""
            nonlocal entered
            if not entered:
                entered = True
                try:
                    self.line()
                except ContractRefusal as declined:
                    refused.append(declined.message)
            return prove(*args, **kwargs)

        original = workspaces.establish_line_access

        def counted(*args, **kwargs):
            established.append(args[0])
            return original(*args, **kwargs)

        with mock.patch.object(workspaces, "prove_line_integrity", side_effect=interleave), \
                mock.patch.object(workspaces, "establish_line_access", side_effect=counted):
            held = self.line()

        self.assertTrue(entered, "the competing schedule never ran")
        self.assertEqual(len(refused), 1, refused)
        self.assertIn("in flight in this manager", refused[0])
        self.assertEqual(held["state"], "idle")
        # PUBLISHED ONCE: one permission act, one row, one recorded creation.
        self.assertEqual(established, [held["path"]])
        self.assertEqual(review_cycles.line_of(self.store, held["line_id"])["state"], "idle")
        writer = self.writer(held["line_id"], 1)
        child = os.path.join(held["path"], "live-worker-file")
        with open(child, "w") as stream:
            stream.write("owned by live work")
        os.chmod(child, 0o600)
        self.assertEqual(os.stat(child).st_mode & 0o7777, 0o600)
        del writer

    def test_a_SECOND_HANDLE_on_the_same_store_cannot_bypass_the_exclusion(self):
        """W301404 review 2026-09-29T02-49-10Z: the key is the DATABASE, not the handle.

        My first exclusion was keyed on `id(store)`, and the reviewer opened a second
        `ControlStore` on the same file in the same process and walked straight past it --
        two handles, one resource, no exclusion at all. The key is now the canonical path of
        the database the handle was opened on, which every handle on that store agrees about.
        """
        from baton_v12.worker_manager import workspaces

        # THE ORIGINAL IS BOUND BEFORE THE PATCH, or the hook calls itself.
        prove = workspaces.prove_line_integrity
        original = self.store
        refused = []

        def interleave(*args, **kwargs):
            if not refused:
                with ControlStore.open(self.control_path,
                                       incarnation="second-handle",
                                       clock=lambda: NOW) as second:
                    self.store = second
                    try:
                        self.line()
                    except ContractRefusal as declined:
                        refused.append(declined.message)
                    finally:
                        self.store = original
            return prove(*args, **kwargs)

        with mock.patch.object(workspaces, "prove_line_integrity",
                               side_effect=interleave):
            held = self.line()

        self.assertEqual(len(refused), 1, refused)
        self.assertIn("in flight in this manager", refused[0])
        self.assertEqual(held["state"], "idle")
        self.assertEqual(self.profile.materialize_calls, 1)

    def test_an_INDEPENDENT_line_is_not_blocked_by_another_preparation(self):
        """The control for the exclusion, and the failure mode it must not have.

        An exclusion keyed too coarsely would serialize every line in the deployment, which
        is a worse defect than the one it fixes: a preparation of ANOTHER Authority and Work
        touches different roots and has nothing to wait for. So while one line is held, a
        different one completes -- and the held one still completes afterwards.
        """
        from baton_v12.worker_manager import workspaces

        prove = workspaces.prove_line_integrity
        other_work = "01234567-W71919"
        finished = {}

        def interleave(*args, **kwargs):
            # THE FLAG IS SET BEFORE THE CALL, because this hook is on the act the nested
            # creation performs too: setting it afterwards recursed and refused the
            # independent line against ITSELF, which measured my own probe rather than
            # the product.
            if "started" not in finished:
                finished["started"] = True
                finished["other"] = create_line(
                    self.store, source=nominate_source(self.source),
                    declared_base=BASE, profile=self.profile,
                    authority_uuid=AUTHORITY, work_id=other_work)
            return prove(*args, **kwargs)

        with mock.patch.object(workspaces, "prove_line_integrity",
                               side_effect=interleave):
            held = self.line()

        self.assertEqual(finished["other"]["state"], "idle")
        self.assertEqual(held["state"], "idle")
        self.assertNotEqual(finished["other"]["line_id"], held["line_id"])
        self.assertNotEqual(finished["other"]["path"], held["path"])

    def test_a_WITHDRAWN_publication_leaves_a_recoverable_materializing_line(self):
        """W301404: what the durable state IS when the root is replaced at the instant of
        the completion commit, which is the one instant no check outside a transaction can
        observe.

        The mismatch is detected exactly where it always was -- the post-commit object
        validation -- and the publication it just made is WITHDRAWN rather than left
        standing: `materializing`, with no object recorded, which no consumer treats as a
        line. Restoring the object lets the recorded creation replay, so the state is
        recoverable rather than terminal, and the withdrawal is conditional so it can never
        pull back a line a writer has advanced.
        """
        original = self.store.transact
        changed = {}

        def interleave(operation, kind, signature, act):
            if kind == "review-line.create" and "path" not in changed:
                path = self.store._connection.execute(
                    "SELECT line_path FROM review_lines").fetchone()[0]
                changed["path"] = path
                os.rename(path, path + "-original")
                os.mkdir(path, 0o700)
            return original(operation, kind, signature, act)

        with mock.patch.object(self.store, "transact", side_effect=interleave):
            with self.assertRaises(ContractRefusal):
                self.line()

        row = self.store._connection.execute(
            "SELECT state, line_device, line_inode FROM review_lines").fetchone()
        self.assertEqual(row["state"], "materializing")
        # AND NO OBJECT IS RECORDED, which the SCHEMA requires rather than this test
        # preferring it: the table's CHECK constraint is `state = 'materializing' AND
        # line_device IS NULL AND line_inode IS NULL`. Keeping the pair raised an
        # `IntegrityError`, so a withdrawn row carries no measurement and the recovery
        # re-applies the RECORDED creation's own members instead.
        self.assertIsNone(row["line_device"])
        self.assertIsNone(row["line_inode"])
        # THE REPLACEMENT WAS NEVER PROVISIONED, and the original is still intact.
        self.assertEqual(os.stat(changed["path"]).st_mode & 0o7777, 0o700)
        os.rmdir(changed["path"])
        os.rename(changed["path"] + "-original", changed["path"])

        recovered = self.line()

        self.assertEqual(recovered["state"], "idle")
        self.assertEqual(recovered["path"], changed["path"])

    def test_an_INTERRUPTION_after_the_access_act_leaves_a_recoverable_line(self):
        """W301404: the window this correction creates, and what it leaves behind.

        Moving the proof and the permission pass out of `store.transact` puts them BEFORE
        the completion commit, so a process that dies between them and the flip leaves the
        access effect on disk with the line still unpublished. That is the honest state and
        the one this case pins:

          * the line stays `materializing`, so nothing reads it as usable;
          * the permission effect IS present -- it is not pretended away;
          * a re-entry completes, because both acts are idempotent over an unchanged tree,
            and the published line validates.

        The previous shape had the same exposure with the lock held -- `transact` could fail
        after the permission pass just as easily -- so what changes here is that the effect
        is no longer rolled back by a database that never owned it.
        """
        from baton_v12.worker_manager import workspaces
        original = workspaces.establish_line_access
        interrupted = []

        def establish_then_die(place, pinned, identity):
            answer = original(place, pinned, identity)
            interrupted.append(place)
            raise RuntimeError("simulated interruption after the access act")

        with mock.patch.object(workspaces, "establish_line_access",
                               side_effect=establish_then_die):
            with self.assertRaisesRegex(RuntimeError, "after the access act"):
                self.line()
        place = interrupted[0]
        self.assertEqual(self.store._connection.execute(
            "SELECT state FROM review_lines").fetchone()[0], "materializing")
        # THE EFFECT SURVIVED THE INTERRUPTION, asserted rather than assumed.
        self.assertEqual(os.stat(place).st_mode & 0o7777, 0o2775)

        recovered = self.line()

        self.assertEqual(recovered["state"], "idle")
        self.assertEqual(recovered["path"], place)
        self.assertEqual(os.stat(place).st_mode & 0o7777, 0o2775)

    def test_late_creator_cannot_reprovision_an_admitted_line(self):
        """W301404 review 2026-09-29T02-49-10Z moved WHEN this schedule is answered.

        The property has not changed: a line is provisioned ONCE and a live worker's own
        file is never touched by a later creator. What changed is that the later creator is
        refused BEFORE it materializes anything, because the exclusive preparation is taken
        ahead of the first external effect -- the reviewer measured two `materialize` calls
        where the property is one, and a refusal that arrives after an effect has not
        excluded it.

        So the competitor here is driven at the same interval as before and now REFUSES,
        the holder completes, and the two facts this case has always been about are
        asserted over the holder's own line.
        """
        from baton_v12.worker_manager import workspaces
        materialize = self.profile.materialize
        inside = False
        refused = []

        def interleave(source, path, base):
            nonlocal inside
            result = materialize(source, path, base)
            if not inside:
                inside = True
                try:
                    self.line()
                except ContractRefusal as declined:
                    refused.append(declined.message)
                child = os.path.join(path, "live-worker-file")
                with open(child, "w") as stream:
                    stream.write("owned by live work")
                os.chmod(child, 0o600)
            return result

        with mock.patch.object(self.profile, "materialize", side_effect=interleave):
            with mock.patch.object(workspaces, "establish_line_access",
                                   wraps=workspaces.establish_line_access) as establish:
                held = self.line()
                self.assertEqual(establish.call_count, 1)

        self.assertTrue(inside, "the late-creator schedule never ran")
        self.assertEqual(len(refused), 1, refused)
        self.assertIn("in flight in this manager", refused[0])
        self.assertEqual(held["state"], "idle")
        # ONE MATERIALIZATION, which is the count the refusal now protects.
        self.assertEqual(self.profile.materialize_calls, 1)
        # AND THE LIVE WORKER'S OWNER-ONLY FILE IS UNTOUCHED -- which used to be
        # true because the second provisioning never ran, and is true now
        # because no permission act ever reaches an entry below the root.
        self.assertEqual(os.stat(os.path.join(held["path"], "live-worker-file")).st_mode & 0o7777, 0o600)

    def test_creating_a_line_PROVES_its_integrity_before_granting_access(self):
        """A reversal probe found this gap: removing the integrity proof from
        `create_line` changed nothing any check could see, because the
        remaining cases only look at modes. A hardlinked file is a property
        ONLY that walk refuses, so it is what asks the question."""
        materialize = self.profile.materialize

        def with_a_hardlink(source, path, base):
            result = materialize(source, path, base)
            original = os.path.join(path, "original")
            with open(original, "w") as stream:
                stream.write("payload")
            os.link(original, os.path.join(path, "hardlinked"))
            return result

        with mock.patch.object(self.profile, "materialize",
                               side_effect=with_a_hardlink):
            with self.assertRaisesRegex(ContractRefusal, "hardlinked"):
                self.line()
        self.assertEqual(
            self.store._connection.execute(
                "SELECT state FROM review_lines").fetchone()[0], "materializing")

    def test_a_failure_while_establishing_keeps_materializing_and_retry_finishes(self):
        """The honest failure semantics the ruling requires kept: the line stays
        `materializing`, no writer is granted, and a retry finishes. What
        changed is the message -- there is no per-entry partial state to warn
        about any more, and the errno is named instead.

        W194457, owner decision 2026-09-17: the errno is named BY NAME now, and
        a permission failure also points at the engine's id mapping, because
        the arrangement is trusted rather than probed and an actual access
        failure is the whole diagnostic an operator gets."""
        from baton_v12.worker_manager import workspaces
        with mock.patch.object(workspaces.os, "fchmod",
                               side_effect=PermissionError(1, "injected")):
            with self.assertRaisesRegex(ContractRefusal, "EPERM") as raised:
                self.line()
        self.assertIn("Operation not permitted", str(raised.exception))
        self.assertIn("id mapping", str(raised.exception))
        self.assertEqual(self.store._connection.execute("SELECT state FROM review_lines").fetchone()[0],
                         "materializing")
        self.assertEqual(self.store._connection.execute("SELECT count(*) FROM line_writers").fetchone()[0], 0)
        self.assertEqual(self.line()["state"], "idle")

    def test_admission_does_not_repair_preexisting_root(self):
        line = self.line()
        os.chmod(line["path"], 0o700)
        with self.assertRaises(ContractRefusal):
            self.writer(line["line_id"], 1)
        self.assertEqual(os.stat(line["path"]).st_mode & 0o7777, 0o700)
        self.assertEqual(line_of(self.store, line["line_id"])["state"], "idle")

    def test_assignment_generation_is_rechecked_in_grant_transaction(self):
        line = self.line()
        original = self.store.transact

        def interleave(operation, kind, signature, act):
            if kind == "review-line.grant-writer":
                self.store._connection.execute(
                    "UPDATE attempts SET assignment_generation = 2 WHERE runtime_attempt_id = 'writer-attempt-1'")
            return original(operation, kind, signature, act)

        with mock.patch.object(self.store, "transact", side_effect=interleave):
            with self.assertRaises(ContractRefusal):
                self.writer(line["line_id"], 1)
        self.assertEqual(line_of(self.store, line["line_id"])["state"], "idle")
        self.assertEqual(self.store._connection.execute("SELECT count(*) FROM line_writers").fetchone()[0], 0)

    def test_durable_launch_binding_refuses_crosswired_roots_and_labels(self):
        from types import MappingProxyType
        from baton_v12.worker_manager import workspaces
        line, writer, delivered = self.mounted_writer()
        roots = delivered["roots"]
        self.assertTrue(roots._line)
        original = dict(roots)
        other = os.path.join(self.storage, "other-line")
        os.mkdir(other)
        os.chmod(other, 0o2775)
        os.chown(other, -1, self.group.gid)
        object.__setattr__(roots, "_members", MappingProxyType({**original, "workspace": other}))
        with self.assertRaisesRegex(ContractRefusal, "actual launch roots"):
            workspaces._prove_execution_workspace(roots, self.group.gid, self.labels())
        object.__setattr__(roots, "_members", MappingProxyType(original))
        for member, value in (("runtime_attempt_id", "another-attempt"),
                              ("generation", 2), ("principal", "another-principal")):
            with self.subTest(member=member), self.assertRaises(ContractRefusal):
                workspaces._prove_execution_workspace(roots, self.group.gid, {**self.labels(), member: value})
        self.freeze(writer, 1)
        with self.assertRaises(ContractRefusal):
            workspaces._prove_execution_workspace(roots, self.group.gid, self.labels())

    def test_replaced_line_refuses_launch(self):
        from baton_v12.worker_manager import workspaces
        line, _, delivered = self.mounted_writer()
        os.rename(line["path"], line["path"] + "-original")
        os.mkdir(line["path"], 0o2775)
        os.chmod(line["path"], 0o2775)
        with self.assertRaises(ContractRefusal):
            workspaces._prove_execution_workspace(delivered["roots"], self.group.gid, self.labels())


    def test_root_replacement_before_initial_publication_never_provisions_replacement(self):
        original = self.store.transact
        changed = {}

        def interleave(operation, kind, signature, act):
            if kind == "review-line.create":
                path = self.store._connection.execute("SELECT line_path FROM review_lines").fetchone()[0]
                changed["path"] = path
                os.rename(path, path + "-original")
                os.mkdir(path, 0o700)
            return original(operation, kind, signature, act)

        with mock.patch.object(self.store, "transact", side_effect=interleave):
            with self.assertRaises(ContractRefusal):
                self.line()
        self.assertEqual(os.stat(changed["path"]).st_mode & 0o7777, 0o700)
        self.assertEqual(self.store._connection.execute("SELECT state FROM review_lines").fetchone()[0],
                         "materializing")

    def test_changed_current_checkpoint_cannot_admit_a_stale_correction(self):
        line = self.line()
        first = self.freeze(self.writer(line["line_id"], 1), 1)
        self.verdict(self.review(first["checkpoint_id"], 1), 1, "changes-requested")
        second = self.freeze(self.writer(line["line_id"], 2, first["checkpoint_id"]), 2)
        self.verdict(self.review(second["checkpoint_id"], 2), 2, "changes-requested")
        original = self.profile.validate

        def interleave(repository, evidence, *, current=False):
            result = original(repository, evidence, current=current)
            self.store._connection.execute("UPDATE review_lines SET current_checkpoint_id = ?",
                                           (first["checkpoint_id"],))
            return result

        with mock.patch.object(self.profile, "validate", side_effect=interleave):
            with self.assertRaises(ContractRefusal):
                self.writer(line["line_id"], 3, second["checkpoint_id"])
        self.assertEqual(self.store._connection.execute(
            "SELECT count(*) FROM line_writers WHERE state = 'active'").fetchone()[0], 0)

    def test_current_assignment_principal_must_still_match_the_granted_writer(self):
        from baton_v12.worker_manager import workspaces
        _, _, delivered = self.mounted_writer()
        self.store._connection.execute(
            "UPDATE attempts SET assignment_principal = 'replacement' WHERE runtime_attempt_id = 'writer-attempt-1'")
        with self.assertRaises(ContractRefusal):
            workspaces._prove_execution_workspace(delivered["roots"], self.group.gid, self.labels())

    def test_launch_group_must_equal_durable_configuration(self):
        from baton_v12.worker_manager import workspaces
        _, _, delivered = self.mounted_writer()
        with self.assertRaises(ContractRefusal):
            workspaces._prove_execution_workspace(delivered["roots"], self.group.gid + 1, self.labels())


class TheConsumptionSubjectIsResolvedFromDurableState(ReviewCycles):
    """W105982: WHICH line an attempt may be consumed from.

    The defect this closes is a subject defect, not a permission one: ordinary
    custody addressed `<storage>/<attempt>/workspace` while a writer attempt
    was mounted at the line checkout, so a receipt was accurate about
    directories that had nothing to do with the tree the manager read.
    """

    def granted(self):
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        return line, writer

    def subject(self, attempt_id="writer-attempt-1", generation=1):
        from baton_v12.worker_manager.review_cycles import consumption_subject
        return consumption_subject(self.store, attempt_id=attempt_id,
                                   generation=generation)

    def test_the_subject_is_the_mounted_line_and_its_custody_sibling(self):
        line, writer = self.granted()
        held = self.subject()
        self.assertEqual(held["line_id"], line["line_id"])
        self.assertEqual(held["writer_id"], writer["writer_id"])
        self.assertEqual(held["line_path"], line_of(
            self.store, line["line_id"])["line_path"])
        # THE SIBLING IS OUTSIDE THE WRITER'S OWN MOUNT, which is the property
        # a retained result depends on: bytes the worker can still reach are
        # not retained.
        self.assertEqual(
            held["custody_path"],
            os.path.join(os.path.dirname(held["line_path"]), "custody",
                         "writer-attempt-1"))
        self.assertFalse(held["custody_path"].startswith(
            held["line_path"].rstrip("/") + "/"))
        # AND THE ORDINARY ATTEMPT ROOT IS NOT IT.
        self.assertNotEqual(held["line_path"],
                            os.path.join(self.storage, "writer-attempt-1",
                                         "workspace"))

    def test_the_recorded_object_pin_travels_with_the_subject(self):
        line, _ = self.granted()
        held = self.subject()
        found = os.stat(held["line_path"], follow_symlinks=False)
        self.assertEqual(held["pinned"], (found.st_dev, found.st_ino))

    def test_a_stale_generation_resolves_no_subject(self):
        self.granted()
        with self.assertRaises(ContractRefusal):
            self.subject(generation=2)

    def test_an_attempt_with_no_live_writer_resolves_no_subject(self):
        line, writer = self.granted()
        self.store._connection.execute(
            "UPDATE line_writers SET state = 'revoked', revoked_at = ?, "
            "revocation_reason = 'checkpoint' WHERE writer_id = ?",
            (NOW, writer["writer_id"]))
        with self.assertRaises(ContractRefusal) as caught:
            self.subject()
        self.assertIn("active line writers", caught.exception.message)

    def test_another_attempts_line_is_never_answered_for_this_one(self):
        self.granted()
        with self.assertRaises(ContractRefusal):
            self.subject(attempt_id="writer-attempt-2")

    def test_a_line_that_is_not_writing_refuses_consumption(self):
        line, _ = self.granted()
        self.store._connection.execute(
            "UPDATE review_lines SET state = 'reviewing' WHERE line_id = ?",
            (line["line_id"],))
        with self.assertRaises(ContractRefusal) as caught:
            self.subject()
        self.assertIn("may be consumed", caught.exception.message)

    def test_the_schema_is_what_makes_the_writer_exclusive(self):
        """The resolver does not re-count active writers, so this pins the
        rule it relies on instead of leaving the dependency implicit."""
        import sqlite3
        line, _ = self.granted()
        self.attempt("writer-attempt-9", 1, "baton.impl", "writer-9")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store._connection.execute(
                "INSERT INTO line_writers (writer_id, line_id, "
                "runtime_attempt_id, assignment_generation, worker_id, "
                "participant, principal, based_checkpoint_id, state, "
                "granted_at) VALUES ('writer-9', ?, 'writer-attempt-9', 1, "
                "'worker-9', 'baton.impl', 'writer-9', NULL, 'active', ?)",
                (line["line_id"], NOW))

    def test_a_replaced_line_object_refuses_before_anything_reads_it(self):
        line, _ = self.granted()
        self.store._connection.execute(
            "UPDATE review_lines SET line_inode = line_inode + 1 "
            "WHERE line_id = ?", (line["line_id"],))
        with self.assertRaises(ContractRefusal):
            self.subject()

    def test_the_subject_is_stable_for_one_unchanged_grant(self):
        self.granted()
        self.assertEqual(self.subject(), self.subject())

    def test_a_changed_assignment_principal_no_longer_authorizes_the_line(self):
        """Authority, Work and generation can all agree while the attempt's
        assignment names somebody else; the accepted launch boundary already
        requires both grant identities, so consumption does too."""
        self.granted()
        for column in ("assignment_principal", "assignment_participant"):
            with self.subTest(column=column):
                self.assertIsNotNone(self.subject())
                self.store._connection.execute(
                    f"UPDATE attempts SET {column} = 'replacement' "
                    "WHERE runtime_attempt_id = 'writer-attempt-1'")
                with self.assertRaises(ContractRefusal) as caught:
                    self.subject()
                self.assertIn("different participants or principals",
                              caught.exception.message)
                self.store._connection.execute(
                    f"UPDATE attempts SET {column} = ? "
                    "WHERE runtime_attempt_id = 'writer-attempt-1'",
                    ("baton.impl" if column == "assignment_participant"
                     else "writer-1",))

    def test_a_line_replaced_during_the_fence_never_reaches_the_profile(self):
        """The early adapter gate runs before sealing, retention, publication
        and an EXTERNAL Authority fence, so re-resolving after that walk cannot
        protect a read this far downstream.

        `freeze_checkpoint` is where the profile is finally handed the path, so
        the recorded object is proved again immediately before it — after the
        checkpoint has legitimately revoked the writer, which is why the
        question asked there is about the LINE and not about a live grant.
        """
        line, writer = self.granted()
        self.complete("writer-attempt-1")
        port = self.port("baton.impl")
        cancel = port.cancel

        def replace_during_the_fence(*operands, **named):
            answer = cancel(*operands, **named)
            os.rename(line["path"], line["path"] + "-original")
            os.mkdir(line["path"])
            return answer

        with mock.patch.object(port, "cancel",
                               side_effect=replace_during_the_fence):
            with self.assertRaises(ContractRefusal):
                freeze_checkpoint(self.store, writer_id=writer["writer_id"],
                                  generation=1, profile=self.profile,
                                  port=port)
        # THE PROFILE WAS NEVER CALLED, which is the whole point: a checkpoint
        # frozen over the replacement would be evidence about somebody else's
        # tree.
        self.assertEqual(self.profile.freeze_calls, [])

    def test_an_unchanged_line_still_freezes_and_still_replays(self):
        line, writer = self.granted()
        self.complete("writer-attempt-1")
        port = self.port("baton.impl")
        first = freeze_checkpoint(self.store, writer_id=writer["writer_id"],
                                  generation=1, profile=self.profile,
                                  port=port)
        self.assertEqual(len(self.profile.freeze_calls), 1)
        # AND THE FROZEN REPLAY PATH IS UNTOUCHED by the added proof.
        self.assertEqual(freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, port=port), first)


class HistoryIsReachableFromTheAttemptThatMadeIt(unittest.TestCase):
    """W124331: `writer_for_attempt` and `review_for_attempt`.

    WHAT WAS NOT ASKABLE. Every other historical reader here takes a writer or
    attachment IDENTITY, and both identities are derived privately inside the
    acts that mint them. A deployment resuming its own ended attempt holds the
    attempt and its generation and nothing else, so it could reach its writer
    only by copying that derivation or by reading the line's CURRENT checkpoint
    -- a second copy of an identity only this module may change, or a pointer
    that every later round moves. These two readers answer from the pair that
    does not move, and the cases below drive that difference rather than
    restating it.
    """

    setUp = ReviewCycles.setUp
    tearDown = ReviewCycles.tearDown
    attempt = ReviewCycles.attempt
    line = ReviewCycles.line
    port = ReviewCycles.port
    complete = ReviewCycles.complete
    freeze = ReviewCycles.freeze
    verdict = ReviewCycles.verdict
    writer = ReviewCycles.writer
    review = ReviewCycles.review
    round = TypedReadersAnswerRowsTheirOwnACTSExplain.round

    @contextlib.contextmanager
    def denied_writes(self):
        """SQLite itself refuses every write for the duration.

        A read-only claim wants the stronger statement: `total_changes` staying
        zero proves no row moved, not that nothing tried.
        """
        connection = self.store._connection
        denied = (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE,
                  sqlite3.SQLITE_DELETE)
        connection.set_authorizer(
            lambda action, *rest: (sqlite3.SQLITE_DENY if action in denied
                                   else sqlite3.SQLITE_OK))
        try:
            yield
        finally:
            connection.set_authorizer(None)

    # -- what the consumer came for ------------------------------------------

    def test_the_base_a_finished_round_was_built_on_survives_the_pointer(self):
        """THE CASE THE PROVIDER GAP WAS FILED FOR.

        Round two's writer is based on round one's checkpoint. By the time its
        ending re-enters, the line's `current_checkpoint_id` is round TWO's --
        so a consumer re-deriving the operand from the line would supply a
        different `based_checkpoint_id` and collide with its own committed
        grant. The reader answers the durable member instead, and the assertion
        is that the two genuinely differ here rather than that one exists.
        """
        line, first, _, _ = self.round(1, "changes-requested")
        _, second, _, _ = self.round(2, "accepted",
                                     based=first["checkpoint_id"])
        moved = line_of(self.store, line["line_id"])["current_checkpoint_id"]
        self.assertEqual(moved, second["checkpoint_id"])
        answered = writer_for_attempt(self.store,
                                      attempt_id="writer-attempt-2",
                                      generation=2)
        self.assertEqual(answered["based_checkpoint_id"],
                         first["checkpoint_id"])
        self.assertNotEqual(answered["based_checkpoint_id"], moved)

    def test_the_first_round_writer_is_based_on_nothing_and_says_so(self):
        """Absence of a base is a fact about the round, not a missing answer."""
        self.round(1, "accepted")
        answered = writer_for_attempt(self.store,
                                      attempt_id="writer-attempt-1",
                                      generation=1)
        self.assertIsNone(answered["based_checkpoint_id"])
        self.assertEqual(answered["runtime_attempt_id"], "writer-attempt-1")
        self.assertEqual(answered["assignment_generation"], 1)

    def test_an_ended_writer_and_attachment_are_answered_as_they_are(self):
        """HISTORY IS THE POINT, so there is no active-state filter.

        A finished round leaves a revoked writer and an ended attachment
        behind. Both are returned with the state they actually have rather
        than the one their granting act returned.
        """
        _, checkpoint, review, _ = self.round(1, "accepted")
        writer = writer_for_attempt(self.store, attempt_id="writer-attempt-1",
                                    generation=1)
        attachment = review_for_attempt(self.store,
                                        attempt_id="review-attempt-1",
                                        generation=1)
        self.assertEqual(writer["state"], "revoked")
        self.assertEqual(attachment["state"], "ended")
        self.assertEqual(
            writer["writer_id"],
            checkpoint_of(self.store,
                          checkpoint["checkpoint_id"])["writer_id"])
        self.assertEqual(attachment["attachment_id"], review["attachment_id"])

    def test_every_finished_round_stays_reachable_beside_the_others(self):
        """Not "the last one": each pair answers its own round."""
        _, first, _, _ = self.round(1, "changes-requested")
        self.round(2, "changes-requested", based=first["checkpoint_id"])
        answers = [writer_for_attempt(self.store,
                                      attempt_id=f"writer-attempt-{n}",
                                      generation=n) for n in (1, 2)]
        self.assertNotEqual(answers[0]["writer_id"], answers[1]["writer_id"])
        self.assertEqual([a["assignment_generation"] for a in answers], [1, 2])
        self.assertEqual(
            [review_for_attempt(self.store, attempt_id=f"review-attempt-{n}",
                                generation=n)["assignment_generation"]
             for n in (1, 2)], [1, 2])

    def test_both_readers_agree_with_the_identity_keyed_readers(self):
        """The same row, reached the other way."""
        _, checkpoint, review, _ = self.round(1, "accepted")
        self.assertEqual(
            writer_for_attempt(self.store, attempt_id="writer-attempt-1",
                               generation=1),
            writer_of(self.store,
                      checkpoint_of(self.store,
                                    checkpoint["checkpoint_id"])["writer_id"]))
        self.assertEqual(
            review_for_attempt(self.store, attempt_id="review-attempt-1",
                               generation=1),
            review_of(self.store, review["attachment_id"]))

    def test_a_writer_is_reachable_before_its_checkpoint_freezes(self):
        """The pair is durable from the grant, not from the freeze."""
        line = self.line()
        writer = self.writer(line["line_id"], 1)
        answered = writer_for_attempt(self.store,
                                      attempt_id="writer-attempt-1",
                                      generation=1)
        self.assertEqual(answered["writer_id"], writer["writer_id"])
        self.assertEqual(answered["state"], "active")

    def test_a_reopened_store_answers_the_same_history(self):
        """RECOVERY AFTER REOPEN, which is the case this exists for.

        Nothing about the answer may live in the process that made it. The
        store is closed and reopened under a DIFFERENT incarnation -- a new
        manager, exactly as a restart produces -- and the same pair still
        reaches the same writer, base and attachment.
        """
        _, first, _, _ = self.round(1, "changes-requested")
        self.round(2, "accepted", based=first["checkpoint_id"])
        before = (writer_for_attempt(self.store, attempt_id="writer-attempt-2",
                                     generation=2),
                  review_for_attempt(self.store, attempt_id="review-attempt-2",
                                     generation=2))
        self.store.close()
        self.store = ControlStore.open(self.control_path,
                                       incarnation="manager-2",
                                       clock=lambda: NOW)
        self.assertEqual(
            (writer_for_attempt(self.store, attempt_id="writer-attempt-2",
                                generation=2),
             review_for_attempt(self.store, attempt_id="review-attempt-2",
                                generation=2)), before)
        self.assertEqual(before[0]["based_checkpoint_id"],
                         first["checkpoint_id"])

    # -- absence -------------------------------------------------------------

    def test_an_attempt_nobody_granted_or_attached_is_absence(self):
        """`None`, not a refusal: never having happened is an ordinary answer.

        A refusal here would make a resuming consumer unable to tell "no
        writer yet" from "your records are wrong", which is the whole reason
        it asks.
        """
        self.round(1, "accepted")
        self.assertIsNone(writer_for_attempt(
            self.store, attempt_id="writer-attempt-9", generation=9))
        self.assertIsNone(review_for_attempt(
            self.store, attempt_id="review-attempt-9", generation=9))

    def test_another_generation_of_a_granted_attempt_is_absence(self):
        """THE PAIR IS THE KEY, not the attempt alone."""
        self.round(1, "accepted")
        self.assertIsNone(writer_for_attempt(
            self.store, attempt_id="writer-attempt-1", generation=2))
        self.assertIsNone(review_for_attempt(
            self.store, attempt_id="review-attempt-1", generation=2))

    def test_neither_reader_answers_the_other_ones_rows(self):
        """A writer attempt has no attachment, and the reverse."""
        self.round(1, "accepted")
        self.assertIsNone(review_for_attempt(
            self.store, attempt_id="writer-attempt-1", generation=1))
        self.assertIsNone(writer_for_attempt(
            self.store, attempt_id="review-attempt-1", generation=1))

    # -- typed before selection ----------------------------------------------

    def test_a_boolean_generation_refuses_at_both_readers(self):
        """`True == 1`, so an untyped lookup would SELECT round one's row and
        then compare equal to it -- twice wrong and silently."""
        self.round(1, "accepted")
        for reader, attempt_id in ((writer_for_attempt, "writer-attempt-1"),
                                   (review_for_attempt, "review-attempt-1")):
            with self.assertRaises(ContractRefusal) as caught:
                reader(self.store, attempt_id=attempt_id, generation=True)
            self.assertEqual(caught.exception.category, "integrity")
            self.assertIn("whole assignment generation",
                          str(caught.exception))

    def test_a_generation_that_only_looks_like_one_refuses(self):
        for generation in ("1", 1.0, -1, None):
            with self.assertRaises(ContractRefusal):
                writer_for_attempt(self.store, attempt_id="writer-attempt-1",
                                   generation=generation)

    def test_an_attempt_that_is_not_an_identity_refuses(self):
        for attempt_id in (None, "", 1, b"writer-attempt-1"):
            with self.assertRaises(ContractRefusal):
                review_for_attempt(self.store, attempt_id=attempt_id,
                                   generation=1)

    # -- ownership, established here -----------------------------------------

    def test_a_writer_row_no_committed_grant_explains_is_refused(self):
        """The cross-binding, driven: the row is real and the act is gone."""
        self.round(1, "accepted")
        writer = writer_for_attempt(self.store, attempt_id="writer-attempt-1",
                                    generation=1)
        self.store._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            ("review-line.grant-writer:" + writer["writer_id"],))
        with self.assertRaises(ContractRefusal) as caught:
            writer_for_attempt(self.store, attempt_id="writer-attempt-1",
                               generation=1)
        self.assertIn("no committed", str(caught.exception))

    def test_a_moved_base_refuses_rather_than_being_handed_out(self):
        """THE MEMBER THE CONSUMER COMES FOR IS THE ONE MOST WORTH BINDING.

        A row whose `based_checkpoint_id` no longer matches the grant would
        otherwise be returned as the operand a later grant replays under --
        which is precisely the collision this reader exists to prevent, dressed
        as a durable answer.
        """
        _, first, _, _ = self.round(1, "changes-requested")
        self.round(2, "accepted", based=first["checkpoint_id"])
        self.store._connection.execute(
            "UPDATE line_writers SET based_checkpoint_id = NULL "
            "WHERE runtime_attempt_id = ?", ("writer-attempt-2",))
        with self.assertRaises(ContractRefusal) as caught:
            writer_for_attempt(self.store, attempt_id="writer-attempt-2",
                               generation=2)
        self.assertEqual(caught.exception.category, "integrity")
        self.assertIn("based_checkpoint_id", str(caught.exception))

    def test_a_rewritten_worker_or_principal_refuses(self):
        """`writer_of` owns the row's shape; it does not bind these."""
        self.round(1, "accepted")
        for column, value in (("worker_id", "worker-somebody-else"),
                              ("principal", "principal-somebody-else")):
            with self.subTest(column=column):
                self.store._connection.execute(
                    f"UPDATE line_writers SET {column} = ? "
                    f"WHERE runtime_attempt_id = ?", (value,
                                                      "writer-attempt-1"))
                with self.assertRaises(ContractRefusal) as caught:
                    writer_for_attempt(self.store,
                                       attempt_id="writer-attempt-1",
                                       generation=1)
                self.assertEqual(caught.exception.category, "integrity")
                self.assertIn(column, str(caught.exception))
                self.store._connection.execute(
                    f"UPDATE line_writers SET {column} = ? "
                    f"WHERE runtime_attempt_id = ?",
                    (f"worker-1" if column == "worker_id" else "writer-1",
                     "writer-attempt-1"))

    def test_a_line_kept_under_another_profile_refuses(self):
        """A fact the act fixed from its own owner, checked against that owner.

        `grant_writer` read the line's profile before it committed, so a line
        that has since changed hands is not the one this grant was made on.
        """
        line, _, _, _ = self.round(1, "accepted")
        self.store._connection.execute(
            "UPDATE review_lines SET profile_name = 'other-profile' "
            "WHERE line_id = ?", (line["line_id"],))
        with self.assertRaises(ContractRefusal) as caught:
            writer_for_attempt(self.store, attempt_id="writer-attempt-1",
                               generation=1)
        self.assertIn("profile", str(caught.exception))

    def test_a_writer_whose_attempt_assignment_changed_refuses(self):
        """The assignment is fixed; a writer that outlives it is not evidence."""
        self.round(1, "accepted")
        self.store._connection.execute(
            "UPDATE attempts SET assignment_participant = 'baton.somebody' "
            "WHERE runtime_attempt_id = ?", ("writer-attempt-1",))
        with self.assertRaises(ContractRefusal) as caught:
            writer_for_attempt(self.store, attempt_id="writer-attempt-1",
                               generation=1)
        self.assertIn("participant", str(caught.exception))

    def test_an_attachment_row_no_committed_act_explains_is_refused(self):
        """The review reader inherits `review_of`'s binding rather than
        repeating it, and this drives that it really is inherited."""
        _, _, review, _ = self.round(1, "accepted")
        self.store._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            ("review-line.attach-review:" + review["attachment_id"],))
        with self.assertRaises(ContractRefusal) as caught:
            review_for_attempt(self.store, attempt_id="review-attempt-1",
                               generation=1)
        self.assertIn("no committed", str(caught.exception))

    def test_a_rewritten_reviewer_refuses_through_the_attempt_too(self):
        self.round(1, "accepted")
        self.store._connection.execute(
            "UPDATE review_attachments SET reviewer_worker_id = ? "
            "WHERE runtime_attempt_id = ?", ("review-worker-somebody-else",
                                             "review-attempt-1"))
        with self.assertRaises(ContractRefusal) as caught:
            review_for_attempt(self.store, attempt_id="review-attempt-1",
                               generation=1)
        self.assertEqual(caught.exception.category, "integrity")

    # -- the committed act, read whole ---------------------------------------
    #
    # W124331 review 2026-09-09T03:05Z [P1]. Every case below returned the
    # HONEST ROW before the correction. That is the worst answer a historical
    # reader can give: a consumer asks it precisely to learn whether its own
    # history is intact, and a damaged journal answered "intact".

    def damage(self, kind, identity, column, value):
        """Rewrite one column of a committed act, and give back the original."""
        operation = kind + ":" + identity
        held = self.store.operation_record(operation)[column]
        self.store._connection.execute(
            f"UPDATE operations SET {column} = ? WHERE operation_id = ?",
            (value, operation))
        return held

    def acts(self):
        """Both rounds' identities, keyed by which reader answers them."""
        _, checkpoint, review, _ = self.round(1, "accepted")
        writer = writer_for_attempt(self.store, attempt_id="writer-attempt-1",
                                    generation=1)
        return {"writer": (writer_for_attempt, "writer-attempt-1",
                           GRANT_KIND, writer["writer_id"]),
                "review": (review_for_attempt, "review-attempt-1",
                           ATTACH_KIND, review["attachment_id"])}

    def refusing(self, reader, attempt_id):
        with self.assertRaises(ContractRefusal) as caught:
            reader(self.store, attempt_id=attempt_id, generation=1)
        self.assertEqual(caught.exception.category, "integrity")
        return str(caught.exception)

    def test_a_signature_that_is_not_readable_refuses_in_our_words(self):
        """A `JSONDecodeError` carries no category, code or pairing, so a
        consumer that handles this manager's refusals does not handle it."""
        for name, (reader, attempt, kind, identity) in self.acts().items():
            with self.subTest(reader=name):
                held = self.damage(kind, identity, "signature", "{")
                self.assertIn("not readable as a journal document",
                              self.refusing(reader, attempt))
                self.damage(kind, identity, "signature", held)

    def test_an_act_that_recorded_no_result_refuses(self):
        for name, (reader, attempt, kind, identity) in self.acts().items():
            with self.subTest(reader=name):
                held = self.damage(kind, identity, "result", "null")
                self.assertIn("one exact document",
                              self.refusing(reader, attempt))
                self.damage(kind, identity, "result", held)

    def test_a_result_belonging_to_something_else_refuses(self):
        """THE MEMBER CONTRACT IS CLOSED, so a foreign document cannot pass by
        carrying none of what is asked for."""
        for name, (reader, attempt, kind, identity) in self.acts().items():
            with self.subTest(reader=name):
                held = self.damage(kind, identity, "result",
                                   json.dumps({"foreign": True}))
                self.assertIn("needs", self.refusing(reader, attempt))
                self.damage(kind, identity, "result", held)

    def test_a_journalled_boolean_generation_refuses(self):
        """`True == 1` again, one layer down: the act's OWN generation is typed
        rather than compared, or a journalled `true` satisfies an equality
        against generation one."""
        for name, (reader, attempt, kind, identity) in self.acts().items():
            with self.subTest(reader=name):
                held = self.store.operation_record(kind + ":" + identity)[
                    "signature"]
                signature = json.loads(held)
                signature["operands"]["generation"] = True
                self.damage(kind, identity, "signature",
                            json.dumps(signature))
                self.assertIn("whole assignment generation",
                              self.refusing(reader, attempt))
                self.damage(kind, identity, "signature", held)

    def test_a_signature_signed_as_another_kind_refuses(self):
        for name, (reader, attempt, kind, identity) in self.acts().items():
            with self.subTest(reader=name):
                held = self.store.operation_record(kind + ":" + identity)[
                    "signature"]
                signature = json.loads(held)
                signature["kind"] = "review-line.freeze"
                self.damage(kind, identity, "signature",
                            json.dumps(signature))
                self.assertIn("was signed as", self.refusing(reader, attempt))
                self.damage(kind, identity, "signature", held)

    def test_an_operand_set_that_is_not_this_builds_refuses(self):
        """Missing and EXTRA both. A truncated act is how a nullable operand
        like `based_checkpoint_id` becomes indistinguishable from a legitimate
        absence under `.get` equality."""
        for name, (reader, attempt, kind, identity) in self.acts().items():
            for change in ("drop", "add"):
                with self.subTest(reader=name, change=change):
                    held = self.store.operation_record(kind + ":" + identity)[
                        "signature"]
                    signature = json.loads(held)
                    if change == "drop":
                        signature["operands"].pop("participant")
                    else:
                        signature["operands"]["invented"] = "x"
                    self.damage(kind, identity, "signature",
                                json.dumps(signature))
                    self.refusing(reader, attempt)
                    self.damage(kind, identity, "signature", held)

    def test_an_identity_its_own_operands_do_not_derive_refuses(self):
        """COMPARING MEMBERS SAYS THEY AGREE; it does not say the identity
        FOLLOWS from them. Both are deterministic digests, so the row and its
        act are moved to generation five together -- every member still agrees
        and the identity no longer derives."""
        line, checkpoint, review, _ = self.round(1, "accepted")
        self.store._connection.execute(
            "UPDATE attempts SET assignment_generation = 5 "
            "WHERE runtime_attempt_id IN (?, ?)",
            ("writer-attempt-1", "review-attempt-1"))
        writer_id = checkpoint_of(self.store,
                                  checkpoint["checkpoint_id"])["writer_id"]
        for table, identity, kind, reader, attempt in (
                ("line_writers", writer_id, GRANT_KIND, writer_for_attempt,
                 "writer-attempt-1"),
                ("review_attachments", review["attachment_id"], ATTACH_KIND,
                 review_for_attempt, "review-attempt-1")):
            with self.subTest(table=table):
                self.store._connection.execute(
                    f"UPDATE {table} SET assignment_generation = 5 "
                    f"WHERE runtime_attempt_id = ?", (attempt,))
                held = self.store.operation_record(kind + ":" + identity)[
                    "signature"]
                signature = json.loads(held)
                signature["operands"]["generation"] = 5
                self.damage(kind, identity, "signature",
                            json.dumps(signature))
                result = self.store.operation_record(kind + ":" + identity)[
                    "result"]
                answer = json.loads(result)
                if "generation" in answer:
                    answer["generation"] = 5
                    self.damage(kind, identity, "result", json.dumps(answer))
                with self.assertRaises(ContractRefusal) as caught:
                    reader(self.store, attempt_id=attempt, generation=5)
                self.assertEqual(caught.exception.category, "integrity")
                self.assertIn("do not derive", str(caught.exception))

    def test_an_attempt_whose_fixed_generation_moved_refuses(self):
        """The assignment is a four-part identity and the schema keeps its
        columns together. Participant and principal alone left this open: a
        writer outlived the authorization it was granted under and still
        answered."""
        for name, (reader, attempt, _, _) in self.acts().items():
            with self.subTest(reader=name):
                self.store._connection.execute(
                    "UPDATE attempts SET assignment_generation = 99 "
                    "WHERE runtime_attempt_id = ?", (attempt,))
                self.assertIn("disagree about generation",
                              self.refusing(reader, attempt))
                self.store._connection.execute(
                    "UPDATE attempts SET assignment_generation = 1 "
                    "WHERE runtime_attempt_id = ?", (attempt,))

    def test_a_line_held_for_another_work_or_authority_refuses(self):
        for column, value in (("work_id", "01234567-W99999"),
                              ("authority_uuid", "f" * 32)):
            with self.subTest(column=column):
                self.acts()
                self.store._connection.execute(
                    f"UPDATE review_lines SET {column} = ?", (value,))
                self.assertIn("another Work or Authority",
                              self.refusing(writer_for_attempt,
                                            "writer-attempt-1"))
                self.tearDown()
                self.setUp()

    def test_a_result_recording_another_state_refuses(self):
        """THE ACT'S ACCOUNT OF ITSELF, which is not the row's state now.

        W124331 review 2026-09-09T03:14Z [P1]: closing the member set proved
        `state` PRESENT and said nothing about what it was, so nothing, a list
        and `revoked` were each accepted as what the grant returned. Preserving
        the row's historical state costs this nothing -- they describe
        different moments.
        """
        for name, (reader, attempt, kind, identity) in self.acts().items():
            for label, value in (("nothing", None), ("a list", []),
                                 ("another state", "revoked")):
                with self.subTest(reader=name, state=label):
                    held = self.store.operation_record(
                        kind + ":" + identity)["result"]
                    answer = json.loads(held)
                    answer["state"] = value
                    self.damage(kind, identity, "result",
                                json.dumps(answer))
                    self.assertIn("records state",
                                  self.refusing(reader, attempt))
                    self.damage(kind, identity, "result", held)

    def test_a_boolean_result_generation_refuses(self):
        """The same value under a different key. `_committed_history` typed the
        operand generation and left the grant's RESULT generation to ordinary
        equality, which accepts `true` for one."""
        acts = self.acts()
        reader, attempt, kind, identity = acts["writer"]
        held = self.store.operation_record(kind + ":" + identity)["result"]
        answer = json.loads(held)
        answer["generation"] = True
        self.damage(kind, identity, "result", json.dumps(answer))
        self.assertIn("whole assignment generation",
                      self.refusing(reader, attempt))
        self.damage(kind, identity, "result", held)
        # The attachment's result carries no generation, so there is nothing
        # here to type -- its closed member contract says so rather than this
        # test assuming it.
        self.assertNotIn("generation", json.loads(
            self.store.operation_record(
                acts["review"][2] + ":" + acts["review"][3])["result"]))

    def test_the_acts_original_state_is_not_required_of_the_row(self):
        """THE ONE THING THE RESULT MUST NOT BE READ FOR. The grant recorded
        `active` and the attachment recorded `active`; history is exactly what
        came after, so binding the result's state would refuse every row this
        reader exists to answer.
        """
        _, checkpoint, review, _ = self.round(1, "accepted")
        writer_id = checkpoint_of(self.store,
                                  checkpoint["checkpoint_id"])["writer_id"]
        for kind, identity in ((GRANT_KIND, writer_id),
                               (ATTACH_KIND, review["attachment_id"])):
            recorded = json.loads(
                self.store.operation_record(kind + ":" + identity)["result"])
            self.assertEqual(recorded["state"], "active")
        self.assertEqual(
            writer_for_attempt(self.store, attempt_id="writer-attempt-1",
                               generation=1)["state"], "revoked")
        self.assertEqual(
            review_for_attempt(self.store, attempt_id="review-attempt-1",
                               generation=1)["state"], "ended")

    # -- and nothing else ----------------------------------------------------

    def test_neither_reader_writes_anything(self):
        """SQLite refuses every write while they run."""
        self.round(1, "accepted")
        with self.denied_writes():
            self.assertIsNotNone(writer_for_attempt(
                self.store, attempt_id="writer-attempt-1", generation=1))
            self.assertIsNotNone(review_for_attempt(
                self.store, attempt_id="review-attempt-1", generation=1))
            self.assertIsNone(writer_for_attempt(
                self.store, attempt_id="writer-attempt-9", generation=9))

    def test_neither_reader_reaches_a_profile_or_a_port(self):
        """A reader that admitted a profile would be re-deciding eligibility,
        which is a question about whether a review MAY be attached rather than
        which one was."""
        self.round(1, "accepted")
        for participant, held in self.ports.items():
            del participant
            held.calls.clear()
        with mock.patch.object(Profile, "capabilities",
                               side_effect=AssertionError("profile reached"),
                               create=True):
            writer_for_attempt(self.store, attempt_id="writer-attempt-1",
                               generation=1)
            review_for_attempt(self.store, attempt_id="review-attempt-1",
                               generation=1)
        self.assertEqual([held.calls for held in self.ports.values()],
                         [[] for _ in self.ports])

    def test_the_readers_take_no_positional_operands(self):
        """Positional operands at a boundary like this are how an attempt and
        a generation get supplied in the wrong order."""
        self.round(1, "accepted")
        for reader in (writer_for_attempt, review_for_attempt):
            with self.assertRaises(TypeError):
                reader(self.store, "writer-attempt-1", 1)


RETENTION = "sha256:" + "7" * 64
OTHER_POLICY = "sha256:" + "9" * 64


class AbandoningPort:
    """The deployment seam an abandonment and its gate discharge cross.

    W128692. It answers the three closed documents those accepted operations
    own -- the authority's cancellation fence, its Work projection and its
    gate-discharge reply -- and decides nothing else. The two rules it models
    are the authority's own: the gate token must be the one holding the Work,
    and an operation identity that already committed replays its answer.
    """

    def __init__(self, participant, *, authority_uuid, work_id):
        self.participant = participant
        self.authority_uuid = authority_uuid
        self.work_id = work_id
        self.gate = None
        self.calls = []
        self.discharged = {}

    def cancel(self, expect, operation_id, reason, work_id, authority_uuid):
        self.calls.append(("cancel", operation_id))
        self.gate = f"runtime-quiescence:{expect['generation']}"
        return {"cause": "cancelled", "assignment": dict(expect),
                "phase": "block", "gate": self.gate, "fenced": True}

    def project_work(self, work_id):
        self.calls.append(("project_work", work_id))
        return {"authority_uuid": self.authority_uuid, "work_id": work_id}

    def satisfy_gate(self, work_id, operation_id, gate, evidence):
        self.calls.append(("satisfy_gate", operation_id))
        held = self.discharged.get(operation_id)
        if held is not None:
            return dict(held)
        if self.gate != gate:
            raise ContractRefusal("refused", "precondition",
                                  "that gate is not the one holding this Work")
        answer = {"gate": gate, "kind": "runtime-absent", "phase": "queued"}
        self.discharged[operation_id] = answer
        self.gate = None
        return dict(answer)


class Custodian:
    """The adapter seam an abandonment removes and normalizes through."""

    custodian_image_digest = "sha256:" + "c" * 64

    def __init__(self):
        self.abandoned_with = []
        self.normalized = []

    def normalize_directory(self, store, *, assignment_id, which):
        from baton_v12.worker_manager import custody

        self.normalized.append((assignment_id, which))
        return custody._answered(
            "normalize", 0,
            {"custody": "normalize", "submission": "0" * 32,
             "entries": 0, "not_ours": 0,
             "running_as": [0, 0]}, None)

    def destroy_abandoned(self, command):
        self.abandoned_with.append(dict(command))
        return {"runtime_id": command["runtime_id"], "state": "absent",
                "why": "the engine answered that this exact identity does not "
                       "exist",
                "credentials": {"lifecycle_state": "not-delivered"},
                "launch": {"lifecycle_state": "not-delivered"}}


class AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint(ReviewCycles):
    """W128692: give a declared abandoned correction's line back.

    W119114's composed proof measured what an operator declaration leaves: the
    runtime is destroyed and the generation fenced, and the LINE is still
    `writing` with the abandoned attempt's writer still `active`. Nothing but
    `freeze_checkpoint` revokes a writer, and an abandoned correction never
    reaches one -- so no successor could ever be granted the line.

    EVERYTHING BELOW GOES THROUGH ACCEPTED PUBLIC OPERATIONS. The abandonment
    is W128682's `abandon_attempt` and its gate discharge is that provider's
    own `discharge_abandoned_quiescence_gate`; nothing here writes either
    provider's rows or derives either provider's identities.
    """

    REASON = "the correction worker stopped answering and is declared abandoned"

    def corrected(self):
        """One line through round one, reviewed changes-requested, with a
        second writer granted and then left unfinished."""
        line = self.line()
        first = self.writer(line["line_id"], 1)
        checkpoint = self.freeze(first, 1)
        review = self.review(checkpoint["checkpoint_id"], 1)
        self.verdict(review, 1, "changes-requested")
        writer = self.writer(line["line_id"], 2,
                             based=checkpoint["checkpoint_id"])
        self.line_id = line["line_id"]
        self.checkpoint = checkpoint
        self.writer_row = writer
        self.abandoned_attempt = "writer-attempt-2"
        return writer

    def running(self, attempt_id):
        """The attempt as an abandonment finds it: a runtime attached, no
        worker answer and nothing accounted for.

        W275774: THE START IS THE PRODUCTION ONE, and it has to be. This used to
        be one `UPDATE ... execution_runtime = 'running'`, and W266336's release
        gate reads a fact no row update can carry: `start_submission_returned`
        -- the SUBMITTER'S OWN journalled record, which nobody but
        `request_runtime_start` writes. So every ending in this class refused with
        "start submission has not returned to the manager that made it", for want
        of a fact none of these cases is about.

        `request_runtime_start` over the narrow adapter double writes exactly the
        two facts the update wrote -- the same `runtime-<attempt>` identity and
        the `running` axis -- and the marker and the occupied lane come with them
        because the real path is what produced them. The adapter is returned so a
        case can read what it was asked.
        """
        from baton_v12.worker_manager import request_runtime_start

        from .test_attempts import Adapter

        adapter = Adapter("runtime-" + attempt_id)
        request_runtime_start(self.store, adapter, attempt_id=attempt_id)
        return adapter

    def abandonment_port(self):
        return self.ports.setdefault(
            "abandon", AbandoningPort("baton.impl", authority_uuid=AUTHORITY,
                                      work_id=WORK))

    def abandoned(self, *, discharge=True, policy=RETENTION):
        from baton_v12.worker_manager import (abandon_attempt,
                                              discharge_abandoned_quiescence_gate)

        self.corrected()
        self.running(self.abandoned_attempt)
        port = self.abandonment_port()
        self.custodian = Custodian()
        abandon_attempt(self.store, port, self.custodian,
                        attempt_id=self.abandoned_attempt, reason=self.REASON,
                        retention_policy_digest=policy)
        if discharge:
            discharge_abandoned_quiescence_gate(
                self.store, port, attempt_id=self.abandoned_attempt,
                retention_policy_digest=policy)
        return self.writer_row

    def accounted(self):
        """The accountable-launch pair a restoration refuses without.

        W275774. Built fresh per call because the launcher is per-invocation by
        contract -- it is handed a recorder bound to one store, one recovery and
        one episode -- and sharing an observer between cases would make one
        case's kernel answer another's.
        """
        from tools.stage_execution import (restoration_cessation,
                                           restoration_launcher)

        return {"launcher": restoration_launcher,
                "cessation": restoration_cessation()}

    def restore(self, **overrides):
        operands = {"attempt_id": self.abandoned_attempt, "generation": 2,
                    "retention_policy_digest": RETENTION,
                    "profile": self.profile}
        operands.update(self.accounted())
        operands.update(overrides)
        return restore_abandoned_correction(self.store, **operands)

    def settled(self, **overrides):
        """W275774: the SUPPORTED exit for an execution nobody completed.

        A claimed episode with no completion behind it holds every later caller,
        deliberately -- an exception is not evidence that a checkout stopped being
        written. `settle_restoration_execution` is the only other exit, and it
        takes the same accountable pair: the kernel's answer that no manager still
        holds this line's execution, plus the positive ending of every launch that
        episode recorded. Nothing here forges a settlement or deletes an episode.
        """
        operands = {"attempt_id": self.abandoned_attempt, "generation": 2,
                    "profile": self.profile}
        operands.update(self.accounted())
        operands.update(overrides)
        return settle_restoration_execution(self.store, **operands)

    def refused(self, act=None, **overrides):
        with self.assertRaises(ContractRefusal) as caught:
            (act or self.restore)(**overrides)
        return caught.exception

    def admit(self, round_number=3):
        """A fresh assignment asking for the line the recovery gave back.

        The attempt row is made once: a case that asks for admission before
        AND after the restore is asking the same successor twice, not two
        successors.
        """
        attempt = f"writer-attempt-{round_number}"
        held = self.store._connection.execute(
            "SELECT 1 FROM attempts WHERE runtime_attempt_id = ?",
            (attempt,)).fetchone()
        if held is None:
            self.attempt(attempt, round_number, "baton.impl",
                         f"writer-{round_number}")
        return grant_writer(self.store, line_id=self.line_id,
                            attempt_id=attempt, generation=round_number,
                            worker_id=f"worker-{round_number}",
                            profile=self.profile,
                            based_checkpoint_id=self.checkpoint[
                                "checkpoint_id"])

    # -- the recovery -------------------------------------------------------

    def test_the_line_comes_back_correction_ready_at_the_same_checkpoint(self):
        writer = self.abandoned()
        # THE STATE THE DEFECT LEAVES, measured before the act rather than
        # asserted about it.
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")
        self.assertEqual(writer_of(self.store,
                                   writer["writer_id"])["state"], "active")

        answered = self.restore()

        self.assertEqual(answered["schema"], "baton.v12.abandoned-correction/1")
        self.assertEqual(answered["state"], "correction-ready")
        self.assertEqual(answered["writer_id"], writer["writer_id"])
        self.assertEqual(answered["line_id"], self.line_id)
        self.assertEqual(answered["checkpoint_id"],
                         self.checkpoint["checkpoint_id"])
        line = line_of(self.store, self.line_id)
        self.assertEqual(line["state"], "correction-ready")
        self.assertEqual(line["current_checkpoint_id"],
                         self.checkpoint["checkpoint_id"])
        self.assertEqual(writer_of(self.store,
                                   writer["writer_id"])["state"], "revoked")

    def test_the_scratch_is_discarded_to_that_exact_checkpoint(self):
        """The profile is asked to restore the checkpoint the writer was BASED
        on, over the line's own checkout and nothing else."""
        self.abandoned()
        self.restore()
        [(repository, evidence)] = self.profile.restore_calls
        self.assertEqual(repository,
                         line_of(self.store, self.line_id)["line_path"])
        self.assertEqual(evidence, self.checkpoint["evidence"])

    def test_the_pin_the_revision_and_the_checkpoint_are_all_unmoved(self):
        """A recovery returns the SAME line to its retained checkpoint; it
        freezes nothing and moves no pin."""
        self.abandoned()
        before = line_of(self.store, self.line_id)
        checkpoint = checkpoint_of(self.store,
                                   self.checkpoint["checkpoint_id"])
        self.restore()
        after = line_of(self.store, self.line_id)
        self.assertEqual(after["revision"], before["revision"])
        self.assertEqual(after["current_checkpoint_id"],
                         before["current_checkpoint_id"])
        self.assertEqual(checkpoint_of(self.store,
                                       self.checkpoint["checkpoint_id"]),
                         checkpoint)
        self.assertEqual(self.profile.freeze_calls,
                         [(before["line_path"], 1)])

    def test_a_fresh_assignment_can_then_be_granted_the_line(self):
        """THE WHOLE POINT, and it is the transition W119114 measured as
        impossible."""
        self.abandoned()
        self.assertEqual(self.refused(self.admit).category, "refused")
        self.restore()
        granted = self.admit()
        self.assertEqual(granted["state"], "active")
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")

    # -- the exclusion, before any write ------------------------------------

    def test_two_active_writers_cannot_exist_for_this_act_to_find(self):
        """MEASURED, and it changes what the guard is FOR.

        I wrote a case that inserted a second active writer and expected the
        recovery to refuse. The store will not have it: `line_one_active_writer`
        is a partial unique index on `line_writers(line_id) WHERE state =
        'active'`, so the state the guard describes cannot be constructed at
        all. The guard therefore is not this act's protection against a second
        writer -- the index is -- and it stays as the place this act states
        the rule it depends on. That is stated here rather than left implied
        by an untestable branch.
        """
        self.abandoned()
        with self.assertRaises(sqlite3.IntegrityError):
            self.store._connection.execute(
                "INSERT INTO line_writers (writer_id, line_id, "
                "runtime_attempt_id, assignment_generation, worker_id, "
                "participant, principal, based_checkpoint_id, state, "
                "granted_at) VALUES ('writer-other', ?, 'writer-attempt-2', "
                "2, 'worker-other', 'baton.impl', 'other', NULL, 'active', ?)",
                (self.line_id, NOW))
        # AND THE GUARD IS STILL EXERCISED, from the other side: a recovery
        # whose own writer is not the line's active one refuses.
        self.store._connection.execute(
            "UPDATE line_writers SET state = 'revoked', revoked_at = ?, "
            "revocation_reason = 'checkpoint' WHERE writer_id = ?",
            (NOW, self.writer_row["writer_id"]))
        refusal = self.refused()
        self.assertEqual(refusal.category, "refused")
        self.assertEqual(self.profile.restore_calls, [])
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))

    def test_a_live_review_attachment_refuses_before_the_profile_is_asked(self):
        """A restore discards the whole checkout, and doing that under a live
        review would destroy what is being reviewed."""
        self.abandoned()
        self.attempt("review-attempt-9", 9, "baton.review", "reviewer-9")
        self.store._connection.execute(
            "INSERT INTO review_attachments (attachment_id, line_id, "
            "checkpoint_id, runtime_attempt_id, assignment_generation, "
            "reviewer_worker_id, reviewer_participant, reviewer_principal, "
            "state, attached_at) VALUES ('attachment-other', ?, ?, "
            "'review-attempt-9', 9, 'w', 'baton.review', 'p', 'active', ?)",
            (self.line_id, self.checkpoint["checkpoint_id"], NOW))
        refusal = self.refused()
        self.assertIn("active review attachment", refusal.message)
        self.assertEqual(self.profile.restore_calls, [])

    def test_a_revoked_writer_has_no_correction_to_restore(self):
        """A revoked writer is what a round that REACHED its checkpoint leaves
        behind, and there is nothing to give back for one.

        Reached by removing the COMPLETION rather than by calling the act
        twice: a second call is the replay, which is a different case and is
        covered as one.

        W275774: ASSERTED AS A REFUSAL AND A STATE, not as a word. This looked for
        "revoked" in the message; the current act reaches the LINE's state first --
        a correction still owed a restore leaves its line `writing`, and this one
        is `correction-ready` because the restoration already gave it back -- so
        the message names that instead. The property the case is about is that
        there is nothing to give back and NO EFFECT is performed for it, and that
        is what this now asserts: the refusal's exact category and code, the
        revoked writer and the released line read from the rows, and not one
        further profile call.
        """
        self.abandoned()
        answered = self.restore()
        self.store._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            (answered["operation_id"],))
        calls = len(self.profile.restore_calls)
        refusal = self.refused()
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertEqual(
            writer_of(self.store, self.writer_row["writer_id"])["state"],
            "revoked")
        self.assertEqual(line_of(self.store, self.line_id)["state"],
                         "correction-ready")
        self.assertEqual(len(self.profile.restore_calls), calls)

    # -- what the evidence has to say ---------------------------------------

    def test_no_committed_abandonment_is_not_a_restore(self):
        self.corrected()
        refusal = self.refused()
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("never behind the absence of one", refusal.message)
        self.assertEqual(self.profile.restore_calls, [])

    def test_an_undischarged_gate_is_not_a_restore(self):
        """The generation is still held at the authority, and a checkout is
        not restored for a successor that cannot be assigned."""
        self.abandoned(discharge=False)
        refusal = self.refused()
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("runtime-quiescence", refusal.message)
        self.assertEqual(self.profile.restore_calls, [])

    def test_another_generation_or_policy_selects_no_abandonment(self):
        """The two are different refusals and the difference is real: a wrong
        GENERATION selects a committed abandonment that is about another
        fenced generation, while a wrong POLICY selects an act this manager
        never committed at all."""
        self.abandoned()
        stale = self.refused(generation=1)
        self.assertEqual((stale.category, stale.code),
                         ("stale-assignment", "generation"))
        missing = self.refused(retention_policy_digest=OTHER_POLICY)
        self.assertEqual((missing.category, missing.code),
                         ("refused", "precondition"))
        self.assertEqual(self.profile.restore_calls, [])

    def test_another_profile_cannot_restore_this_line(self):
        self.abandoned()

        class Foreign(type(self.profile)):
            name = "another-profile"

        foreign = Foreign()
        foreign.held = self.profile.held
        foreign.current_revision = self.profile.current_revision
        refusal = self.refused(profile=foreign)
        self.assertEqual((refusal.category, refusal.code),
                         ("policy", "profile-uncertified"))
        self.assertEqual(foreign.restore_calls, [])

    # -- interruption, replay and concurrency --------------------------------

    def test_a_failed_restoration_admits_nobody(self):
        """W275774: the EXCLUSION, not the writer row, is what holds here.

        This asserted the writer was still `active` after the failure, which was
        true while the effect ran inside the transaction. W257624 moved the effect
        OUTSIDE every transaction -- no database lock may be held across I/O -- so
        the intent TAKES the exclusion by revoking the writer first and a failed
        restoration leaves that revocation standing. That is the state a retry has
        to find, and it admits nobody either: the line is still `writing`, no
        completion exists, and a successor is refused. What the case is about is
        unchanged; where the exclusion is recorded is not.
        """
        self.abandoned()
        self.profile.restore_refusal = ContractRefusal(
            "policy", "profile-uncertified", "the checkout could not be reset")
        self.assertEqual(self.refused().code, "profile-uncertified")
        # THE EXCLUSION IS EXACTLY WHERE THE INTENT PUT IT, and nothing is released.
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")
        self.assertEqual(
            writer_of(self.store, self.writer_row["writer_id"])["state"],
            "revoked")
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual(self.refused(self.admit).category, "refused")

    def test_the_effect_and_the_release_happen_in_one_serialized_act(self):
        """ONE SERIALIZED ACT, AND W257624 MOVED WHAT SERIALIZES IT.

        The obsolete prose this docstring carried -- "`store.transact` IS the
        serialization owner", the effect inside the write lock -- is WITHDRAWN by
        that Work's own ruling: no database lock may be held across I/O, and a
        `stat` is I/O. What serializes the act now is the exclusion the intent
        took plus the restoration lock held across the whole execution, and the
        release is the short transaction at the end. The case's subject is
        unchanged: nothing a successor could use appears until the act finishes.

        WHAT THIS NOW MEASURES, at the moment the profile is asked: the writer is
        already revoked (the intent took the exclusion), the line is still
        `writing` so no successor can be admitted, no completion exists, and the
        profile is called OUTSIDE any database transaction -- which is the
        property the old shape could not have, and the reason it changed. All
        three of the original after-assertions stand exactly as they were.
        """
        self.abandoned()
        seen = {}
        original = self.profile.restore_checkpoint

        # W275774: `**routed` FORWARDS THE PER-INVOCATION RUNNER. The production
        # act passes it to every restoration, so a wrapper that dropped it would
        # make the profile below record no launch and the completion hold.
        def watching(repository, evidence, **routed):
            seen["writer"] = writer_of(
                self.store, self.writer_row["writer_id"])["state"]
            seen["line"] = line_of(self.store, self.line_id)["state"]
            seen["completed"] = abandoned_correction_of(
                self.store, attempt_id=self.abandoned_attempt, generation=2)
            # THE EFFECT IS OUTSIDE EVERY DATABASE TRANSACTION, which is the
            # standing ruling this act was reshaped to obey. Asked of the
            # connection itself rather than inferred from the ordering.
            seen["in_transaction"] = self.store._connection.in_transaction
            seen["admission"] = self.refused(self.admit).category
            return original(repository, evidence, **routed)

        self.profile.restore_checkpoint = watching
        answered = self.restore()
        self.assertEqual(seen["writer"], "revoked")
        self.assertEqual(seen["line"], "writing")
        self.assertIsNone(seen["completed"])
        self.assertFalse(seen["in_transaction"])
        self.assertEqual(seen["admission"], "refused")
        self.assertEqual(writer_of(self.store,
                                   self.writer_row["writer_id"])["state"],
                         "revoked")
        self.assertEqual(line_of(self.store, self.line_id)["state"],
                         "correction-ready")
        self.assertEqual(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2),
            answered)

    def test_an_in_flight_duplicate_cannot_reach_a_second_effect(self):
        """THE COUNTEREXAMPLE, DRIVEN AGAIN, against the serialization.

        The reviewer's interleaving reaches a second recovery from inside the
        first one's profile effect. No second effect and no release to a
        successor happens while the first act holds its exclusion.

        W275774: WHAT REFUSES IT IS NO LONGER THE NESTED TRANSACTION. This
        expected `operation-collision` from a nested `transact`, which was the
        boundary while the effect ran inside the write lock. W257624 moved the
        effect out and put the whole execution under an exclusive non-blocking
        restoration lock, so the reentrant duplicate is now refused
        `refused/precondition` by that lock -- one execution at a time -- before
        it can reach a profile at all. Same counterexample, same conclusion, the
        exact current refusal asserted rather than an arbitrary exception.
        """
        self.abandoned()
        original = self.profile.restore_checkpoint
        resumed = {}

        def paused(repository, evidence, **routed):
            if resumed:
                return original(repository, evidence, **routed)
            resumed["b"] = self.refused(
                lambda: restore_abandoned_correction(
                    self.store, attempt_id=self.abandoned_attempt,
                    generation=2, retention_policy_digest=RETENTION,
                    profile=self.profile, **self.accounted()))
            resumed["admission"] = self.refused(self.admit).category
            return original(repository, evidence, **routed)

        self.profile.restore_checkpoint = paused
        answered = self.restore()

        self.assertEqual((resumed["b"].category, resumed["b"].code),
                         ("refused", "precondition"))
        self.assertIn("is held by another manager on this line",
                      resumed["b"].message)
        self.assertIn("one execution at a time", resumed["b"].message)
        # NO SUCCESSOR WAS ADMITTED IN THE WINDOW, and exactly one effect ran.
        self.assertEqual(resumed["admission"], "refused")
        self.assertEqual(len(self.profile.restore_calls), 1)
        self.assertEqual(answered["state"], "correction-ready")

    def test_two_overlapping_connections_produce_exactly_one_effect(self):
        """THE ACTUAL OVERLAP the owner scope asks for, not a sequential one.

        A second manager over the same store calls the recovery WHILE the first
        is inside its effect, on its own connection in its own thread.

        W275774: AND IT IS HELD RATHER THAN BLOCKED. This expected the second
        caller to block on `BEGIN IMMEDIATE` and answer the committed replay,
        which is what happened while the effect ran inside the write lock.
        W257624 moved the effect outside every transaction, so there is no lock to
        block on: the second manager finds this line's execution in flight under
        another incarnation with neither a completion nor a settlement behind it,
        and is refused `refused/precondition` -- an execution nobody has
        positively settled stays held rather than being repeated. EXACTLY ONE
        EFFECT still runs, which is what the case is for, and the replay the old
        shape measured is still available once the first act has COMPLETED: that
        is asserted here too, so nothing the case proved is dropped.
        """
        self.abandoned()
        answers = {}
        original = self.profile.restore_checkpoint
        started = threading.Event()
        # W275774: A REAL RENDEZVOUS, NOT A TIMED GUESS. This waited 0.2s inside the
        # first effect for an event that was only set AFTER that effect returned, so
        # the overlap it claimed to measure rested on the competitor happening to be
        # scheduled inside the window. The competitor now signals when it has
        # ANSWERED, and the first effect does not complete until that signal
        # arrives -- so the second call provably happened WHILE the first was inside
        # its effect. Deadlock-free by the property this case is about: the effect is
        # outside every database transaction, so the competitor can reach its own
        # refusal while the first holds nothing a reader needs.
        answered = threading.Event()

        def other():
            started.wait(5)
            # ITS OWN CONNECTION, OPENED IN ITS OWN THREAD, because a SQLite
            # connection belongs to the thread that created it -- which is the
            # whole point: this is a second manager, not a second caller.
            second = ControlStore.open(self.control_path,
                                       incarnation="manager-2",
                                       clock=lambda: NOW)
            try:
                answers["second"] = restore_abandoned_correction(
                    second, attempt_id=self.abandoned_attempt, generation=2,
                    retention_policy_digest=RETENTION, profile=self.profile,
                    **self.accounted())
            except BaseException as failure:      # recorded, not swallowed
                answers["second"] = failure
            finally:
                second.close()
                # SIGNALLED AFTER THE ANSWER IS RECORDED, so the waiter below knows
                # the competitor has finished rather than merely started.
                answered.set()

        def holding(repository, evidence, **routed):
            started.set()
            self.assertTrue(answered.wait(10),
                            "the competing manager never answered, so no overlap "
                            "was measured")
            return original(repository, evidence, **routed)

        self.profile.restore_checkpoint = holding
        runner = threading.Thread(target=other)
        runner.start()
        try:
            answers["first"] = self.restore()
        finally:
            runner.join(10)
        # AND THE COMPETITOR REALLY FINISHED, rather than being abandoned alive.
        self.assertFalse(runner.is_alive())
        self.assertIn("second", answers)

        held = answers["second"]
        self.assertIsInstance(held, ContractRefusal)
        self.assertEqual((held.category, held.code), ("refused", "precondition"))
        self.assertIn("is in flight under manager incarnation", held.message)
        self.assertIn("neither a completion nor a settlement", held.message)
        # EXACTLY ONE EFFECT, AND THE COMPLETION IS THE FIRST CALLER'S.
        self.assertEqual(len(self.profile.restore_calls), 1)
        self.assertEqual(answers["first"]["state"], "correction-ready")
        # AND THE REPLAY THE OLD SHAPE MEASURED, once the act has completed.
        after = ControlStore.open(self.control_path, incarnation="manager-3",
                                  clock=lambda: NOW)
        self.addCleanup(after.close)
        self.assertEqual(
            restore_abandoned_correction(
                after, attempt_id=self.abandoned_attempt, generation=2,
                retention_policy_digest=RETENTION, profile=self.profile,
                **self.accounted()),
            answers["first"])
        self.assertEqual(len(self.profile.restore_calls), 1)

    def test_a_second_connection_replays_without_entering_the_effect(self):
        """The cross-connection half of the same rule, and it is the store
        owner's rather than this module's.

        `transact` re-reads the replay INSIDE its write lock, so a second
        manager over the same store returns the committed recovery without
        running the action at all. A concurrent one blocks on that lock first;
        what is measured here is the part a single-threaded case can measure
        honestly -- that entering does not happen.
        """
        self.abandoned()
        first = self.restore()
        second = ControlStore.open(self.control_path, incarnation="manager-2",
                                   clock=lambda: NOW)
        self.addCleanup(second.close)
        calls = len(self.profile.restore_calls)
        self.assertEqual(
            restore_abandoned_correction(
                second, attempt_id=self.abandoned_attempt, generation=2,
                retention_policy_digest=RETENTION, profile=self.profile,
                **self.accounted()),
            first)
        self.assertEqual(len(self.profile.restore_calls), calls)

    def test_the_exclusion_is_proved_under_the_lock_and_not_before_it(self):
        """A line moved between the entry proof and the decision that authorizes
        the destructive act is caught by the re-read inside that decision, and
        NOTHING is performed for it.

        W275774: THE INJECTION POINT WAS STALE, and that is all that was wrong
        here. This hooked the first `review-line.restore-abandoned:` transaction,
        which USED to be the act that admitted the execution; under W257624 the
        admission is `_admitted_execution` and that operation identity now belongs
        to the COMPLETION -- so the move landed after the effect had already run
        and the case measured the wrong boundary. The schedule moves to just
        before the current atomic admission and the no-effect assertion STAYS:
        the pre-effect exclusion is exactly what must still hold. The separate
        case for a line moved AFTER the effect
        (`test_an_admission_during_the_restore_stops_the_completion`) keeps
        refusing the completion, and is untouched.
        """
        self.abandoned()
        original = admitted = review_cycles._admitted_execution

        def moving(store, operation_id, line, writer, checkpoint, what):
            store._connection.execute(
                "UPDATE review_lines SET state = 'reviewing' "
                "WHERE line_id = ?", (self.line_id,))
            return original(store, operation_id, line, writer, checkpoint, what)

        with mock.patch.object(review_cycles, "_admitted_execution", moving):
            refusal = self.refused()
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("no longer holds the exclusion", refusal.message)
        self.assertEqual(self.profile.restore_calls, [])
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual(review_cycles._admitted_execution, admitted)

    def test_an_interrupted_restore_finishes_under_the_same_exclusion(self):
        """The intent commits before the profile act, so a crash between them
        leaves a recorded intent with no completion -- which is exactly what a
        retry has to find.

        W275774: AND THE RETRY IS NOT FREE ANY MORE, which is the half W257624
        added rather than a change of subject. An interrupted execution's effects
        are UNKNOWN, so the bare retry is HELD and no second effect happens; the
        episode has to be POSITIVELY SETTLED first -- the kernel's answer that no
        manager still holds the execution, plus the ending of every launch it
        recorded -- and only then does the same recovery finish under the same
        exclusion. Both the completion and the two-effect attribution this case
        has always asserted are preserved.
        """
        self.abandoned()
        self.profile.restore_refusal = ContractRefusal(
            "policy", "profile-uncertified", "interrupted")
        self.refused()
        self.profile.restore_refusal = None
        # THE UNKNOWN EXECUTION HOLDS, AND IT RUNS NOTHING.
        after = len(self.profile.restore_calls)
        held = self.refused()
        self.assertEqual((held.category, held.code), ("refused", "precondition"))
        self.assertIn("neither a completion nor a settlement", held.message)
        self.assertEqual(len(self.profile.restore_calls), after)
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        # THE SUPPORTED SETTLEMENT, which decides nothing but that episode.
        account = self.settled()
        self.assertEqual(account["ended"]["exclusion"], "acquired")
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        answered = self.restore()
        self.assertEqual(answered["state"], "correction-ready")
        self.assertEqual(len(self.profile.restore_calls), 2)
        self.assertEqual(line_of(self.store, self.line_id)["state"],
                         "correction-ready")

    def test_a_completed_recovery_replays_without_touching_the_checkout(self):
        """A second call answers from the journal. It does not reset a
        checkout a later writer may now hold, which is why the completed
        record exists at all."""
        self.abandoned()
        first = self.restore()
        self.admit()
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")
        calls = len(self.profile.restore_calls)
        self.assertEqual(self.restore(), first)
        self.assertEqual(len(self.profile.restore_calls), calls)
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")

    def test_a_replay_naming_another_policy_collides(self):
        self.abandoned()
        first = self.restore()
        refusal = self.refused(retention_policy_digest=OTHER_POLICY)
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "operation-collision"))
        self.assertEqual(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2),
            first)

    def test_a_second_recovery_creates_no_second_writer_or_revocation(self):
        self.abandoned()
        first = self.restore()
        revoked = writer_of(self.store, self.writer_row["writer_id"])
        self.assertEqual(self.restore(), first)
        self.assertEqual(writer_of(self.store,
                                   self.writer_row["writer_id"]), revoked)
        held = self.store._connection.execute(
            "SELECT count(*) AS n FROM line_writers WHERE line_id = ?",
            (self.line_id,)).fetchone()["n"]
        self.assertEqual(held, 2)

    def test_an_unfinished_retry_re_proves_its_provenance_first(self):
        """REVIEW 2026-09-09T16:04Z. The recorded-intent branch was a shortcut:
        it read the writer row directly and skipped both of W128682's readers
        and the verdict, so a retry after a failed profile call restored a
        checkout on evidence that had since been broken.

        Every unfinished retry now re-proves the SAME fixed relationships
        before any effect.
        """
        from baton_v12.source_profiles import ProfileRefusal

        self.abandoned()
        self.profile.restore_refusal = ProfileRefusal("the checkout was busy")
        with self.assertRaises(ProfileRefusal):
            self.restore()
        self.profile.restore_refusal = None
        calls = len(self.profile.restore_calls)
        # THE INTENT IS COMMITTED and the retry would otherwise walk past the
        # provenance it was granted against.
        self.store._connection.execute(
            "UPDATE checkpoint_verdicts SET reviewer_principal = "
            "'somebody-else' WHERE checkpoint_id = ?",
            (self.checkpoint["checkpoint_id"],))
        refusal = self.refused()
        self.assertEqual(refusal.category, "integrity")
        self.assertEqual(len(self.profile.restore_calls), calls)
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")

    def test_an_unfinished_retry_binds_its_intent_to_the_owners(self):
        """And the adopted intent is bound back to the world it named, so a
        retry cannot finish one whose checkpoint has moved under it."""
        from baton_v12.source_profiles import ProfileRefusal

        self.abandoned()
        self.profile.restore_refusal = ProfileRefusal("the checkout was busy")
        with self.assertRaises(ProfileRefusal):
            self.restore()
        self.profile.restore_refusal = None
        self.store._connection.execute(
            "UPDATE line_writers SET based_checkpoint_id = NULL "
            "WHERE writer_id = ?", (self.writer_row["writer_id"],))
        # `_abandoned_writer` refuses a based-checkpoint-less writer as
        # `refused`; a writer that still names one but the WRONG one reaches
        # the intent binding and refuses as `integrity`. Either way the retry
        # stops before any effect.
        self.assertIn(self.refused().category, ("refused", "integrity"))
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))

    def interrupted_intent(self):
        """One committed intent whose profile call failed, and its row."""
        from baton_v12.source_profiles import ProfileRefusal

        self.abandoned()
        self.profile.restore_refusal = ProfileRefusal("the checkout was busy")
        with self.assertRaises(ProfileRefusal):
            self.restore()
        self.profile.restore_refusal = None
        row = self.store._connection.execute(
            "SELECT operation_id, signature, result FROM operations "
            "WHERE kind = 'review-line.restore-abandoned-intent'").fetchone()
        self.assertIsNotNone(row)
        return dict(row)

    def test_a_resigned_intent_cannot_authorize_a_retry_effect(self):
        """REVIEW 2026-09-09T16:31Z [P1]. `store.replay` compares the signature
        it is HANDED, so passing the row's own back compares it with itself.
        Replacing that column with canonical operand text under a FOREIGN KIND
        left the identity and result untouched and the retry wrote a
        checkout."""
        from baton_v12.worker_manager import manager_signature

        held = self.interrupted_intent()
        calls = len(self.profile.restore_calls)
        self.store._connection.execute(
            "UPDATE operations SET signature = ? WHERE operation_id = ?",
            (manager_signature("review-line.restore-abandoned-foreign",
                               json.loads(held["result"])),
             held["operation_id"]))
        refusal = self.refused()
        self.assertEqual((refusal.category, refusal.code),
                         ("integrity", "schema"))
        self.assertIn("ONE signed relationship", refusal.message)
        self.assertEqual(len(self.profile.restore_calls), calls)
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")

    def test_an_edited_intent_result_cannot_authorize_a_retry_effect(self):
        """The other half of one binding: a member changed inside the recorded
        intent no longer composes the signature the journal holds."""
        held = self.interrupted_intent()
        calls = len(self.profile.restore_calls)
        spoiled = dict(json.loads(held["result"]),
                       runtime_id="runtime-somebody-else")
        self.store._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps(spoiled), held["operation_id"]))
        self.assertEqual(self.refused().category, "integrity")
        self.assertEqual(len(self.profile.restore_calls), calls)

    def test_a_malformed_intent_refuses_through_the_contract_boundary(self):
        """Closed validation BEFORE any nested field is indexed: a null
        assignment would otherwise be a TypeError at a persisted-input
        boundary, which bypasses the portable refusal path."""
        held = self.interrupted_intent()
        calls = len(self.profile.restore_calls)
        spoiled = dict(json.loads(held["result"]), assignment=None)
        self.store._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps(spoiled), held["operation_id"]))
        refusal = self.refused()
        self.assertEqual(refusal.category, "integrity")
        self.assertEqual(len(self.profile.restore_calls), calls)

    def test_a_transient_profile_failure_stays_retryable(self):
        """A profile fault is not a journalled refusal: `ProfileRefusal` is not a
        `ContractRefusal`, nothing durable records it, and the committed intent
        stays standing for a retry.

        W275774: the old prose put the effect inside `transact` and rested the
        retryability on that rollback. W257624 moved the effect outside every
        transaction, so what makes this retryable is that the intent is already
        committed and no completion followed -- and the intent's own revocation
        stands, which is the exclusion the retry runs under. RETRYABLE STILL MEANS
        THROUGH THE SUPPORTED EXIT: an interrupted execution's effects are
        unknown, so the episode is settled positively before the same recovery
        finishes. The original conclusion -- the same act reaches
        `correction-ready` afterwards -- is unchanged.
        """
        from baton_v12.source_profiles import ProfileRefusal

        self.abandoned()
        self.profile.restore_refusal = ProfileRefusal("the checkout was busy")
        with self.assertRaises(ProfileRefusal):
            self.restore()
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")
        self.assertEqual(
            writer_of(self.store, self.writer_row["writer_id"])["state"],
            "revoked")
        self.profile.restore_refusal = None
        held = self.refused()
        self.assertEqual((held.category, held.code), ("refused", "precondition"))
        self.assertIn("neither a completion nor a settlement", held.message)
        self.settled()
        self.assertEqual(self.restore()["state"], "correction-ready")

    def test_an_admission_during_the_restore_stops_the_completion(self):
        """The profile call is the one place this act waits on somebody else,
        so the exclusion is proved again inside the write that depends on it."""
        self.abandoned()
        original = self.profile.restore_checkpoint

        def racing(repository, evidence, **routed):
            answered = original(repository, evidence, **routed)
            self.store._connection.execute(
                "UPDATE review_lines SET state = 'reviewing' WHERE line_id = ?",
                (self.line_id,))
            return answered

        self.profile.restore_checkpoint = racing
        refusal = self.refused()
        self.assertEqual(refusal.category, "refused")
        self.assertIn("no longer holds", refusal.message)
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))

    # -- the reader ----------------------------------------------------------


    # -- the reader ----------------------------------------------------------

    def test_the_reader_answers_absence_and_then_history(self):
        self.abandoned()
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        answered = self.restore()
        self.assertEqual(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2),
            answered)
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=1))

    def test_the_reader_still_answers_after_the_line_advances(self):
        """A completed recovery is a fact about one attempt's generation, and
        it stays true after a later writer holds the line and a later
        checkpoint is frozen. It does NOT claim the line is correction-ready
        now."""
        self.abandoned()
        answered = self.restore()
        granted = self.admit()
        self.freeze(granted, 3)
        self.assertEqual(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2),
            answered)
        self.assertNotEqual(line_of(self.store, self.line_id)["state"],
                            "correction-ready")

    def test_a_record_edited_member_by_member_refuses(self):
        self.abandoned()
        answered = self.restore()
        operation_id = answered["operation_id"]
        spoiled = dict(answered, line_id="line-somebody-else")
        self.store._connection.execute(
            "UPDATE operations SET result = ? WHERE operation_id = ?",
            (json.dumps(spoiled), operation_id))
        refusal = self.refused(
            lambda: abandoned_correction_of(
                self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual((refusal.category, refusal.code),
                         ("integrity", "schema"))
        self.assertIn("ONE signed relationship", refusal.message)

    def test_a_record_committed_under_another_kind_refuses(self):
        self.abandoned()
        answered = self.restore()
        self.store._connection.execute(
            "UPDATE operations SET kind = ? WHERE operation_id = ?",
            (GRANT_KIND, answered["operation_id"]))
        refusal = self.refused(
            lambda: abandoned_correction_of(
                self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual((refusal.category, refusal.code),
                         ("integrity", "schema"))
        self.assertEqual(RESTORE_KIND, "review-line.restore-abandoned")

    def test_a_broken_historical_writer_refuses_in_the_reader_and_the_act(
            self):
        """[P1] The receipt used to be checked only against a signature
        recomposed from itself, which proves internal consistency and nothing
        about the records it was earned against. Editing the old writer's
        principal makes the public `writer_for_attempt` owner refuse, and both
        exits must refuse with it."""
        self.abandoned()
        answered = self.restore()
        self.store._connection.execute(
            "UPDATE line_writers SET principal = 'somebody-else' "
            "WHERE writer_id = ?", (answered["writer_id"],))
        refusal = self.refused(
            lambda: abandoned_correction_of(
                self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual(refusal.category, "integrity")
        self.assertEqual(self.refused().category, "integrity")

    def test_a_broken_historical_verdict_refuses_before_any_profile_write(self):
        """[P1] The committed GRANT proves admission and does not re-read the
        verdict, so a retained verdict whose principal had been edited let this
        act write a checkout and complete. The decision is now read through its
        own owner."""
        self.abandoned()
        self.store._connection.execute(
            "UPDATE checkpoint_verdicts SET reviewer_principal = "
            "'somebody-else' WHERE checkpoint_id = ?",
            (self.checkpoint["checkpoint_id"],))
        refusal = self.refused()
        self.assertEqual(refusal.category, "integrity")
        self.assertEqual(self.profile.restore_calls, [])
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")

    def test_an_accepted_checkpoint_schedules_no_correction(self):
        """Only a changes-requested decision does, and the disposition is read
        from the committed verdict rather than assumed from the line."""
        self.abandoned()
        self.store._connection.execute(
            "UPDATE checkpoint_verdicts SET disposition = 'accepted' "
            "WHERE checkpoint_id = ?", (self.checkpoint["checkpoint_id"],))
        self.assertEqual(self.refused().category, "integrity")
        self.assertEqual(self.profile.restore_calls, [])

    def test_the_reader_still_follows_its_owners_after_a_later_round(self):
        """Historical validation must not become a mutable predicate: the
        owners are followed, and a later writer and a later checkpoint do not
        make an earlier recovery unreadable."""
        self.abandoned()
        answered = self.restore()
        granted = self.admit()
        self.freeze(granted, 3)
        self.assertEqual(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2),
            answered)

    def test_the_reader_performs_no_profile_or_authority_act(self):
        self.abandoned()
        self.restore()
        calls = list(self.abandonment_port().calls)
        restores = len(self.profile.restore_calls)
        abandoned_correction_of(self.store, attempt_id=self.abandoned_attempt,
                                generation=2)
        self.assertEqual(self.abandonment_port().calls, calls)
        self.assertEqual(len(self.profile.restore_calls), restores)
