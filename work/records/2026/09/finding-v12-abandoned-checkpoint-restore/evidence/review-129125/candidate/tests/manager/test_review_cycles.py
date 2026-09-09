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
from baton_v12.worker_manager.review_cycles import (ATTACH_KIND, GRANT_KIND,
                                                     RESTORE_KIND,
                                                     abandoned_correction_of,
                                                     restore_abandoned_correction)
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

    def validate(self, repository, evidence, *, current=False):
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

    def restore_checkpoint(self, repository, evidence):
        self.restore_calls.append((repository, dict(evidence)))
        self.validate(repository, evidence)
        if self.restore_refusal is not None:
            raise self.restore_refusal
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
        self.store._connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, created_at, work_id, "
            "authority_uuid, assignment_participant, assignment_generation, "
            "assignment_claim_event_seq, assignment_principal, assignment_scope, "
            "assignment_role, assignment_grant, assignment_policy_generation) "
            "VALUES (?, 'adapter', 'adapter-digest', 'profile-digest', ?, ?, ?, "
            "?, ?, ?, ?, 'scope', 'role', 'grant', 1)",
            (attempt_id, NOW, WORK, AUTHORITY, participant, generation,
             generation, principal))
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
        discard_execution_roots(self.storage, "writer-attempt-1")
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
        discard_execution_roots(self.storage, "review-attempt-1")
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
                discard_workspace(self.storage, identity)
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

    def test_provisioning_is_serialized_before_idle_and_never_repeated(self):
        from baton_v12.worker_manager import workspaces
        original = workspaces._provision_line_access
        calls = []

        def provision(place, pinned, gid):
            self.assertTrue(self.store._connection.in_transaction)
            self.assertEqual(self.store._connection.execute("SELECT state FROM review_lines").fetchone()[0],
                             "materializing")
            calls.append(place)
            return original(place, pinned, gid)

        with mock.patch.object(workspaces, "_provision_line_access", side_effect=provision):
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

    def test_late_creator_cannot_reprovision_an_admitted_line(self):
        from baton_v12.worker_manager import workspaces
        materialize = self.profile.materialize
        inside = False
        saved = {}

        def interleave(source, path, base):
            nonlocal inside
            result = materialize(source, path, base)
            if not inside:
                inside = True
                saved["line"] = self.line()
                self.writer(saved["line"]["line_id"], 1)
                child = os.path.join(path, "live-worker-file")
                with open(child, "w") as stream:
                    stream.write("owned by live work")
                os.chmod(child, 0o600)
            return result

        with mock.patch.object(self.profile, "materialize", side_effect=interleave):
            with mock.patch.object(workspaces, "_provision_line_access",
                                   wraps=workspaces._provision_line_access) as provision:
                self.assertEqual(self.line(), saved["line"])
                self.assertEqual(provision.call_count, 1)
        self.assertEqual(os.stat(os.path.join(saved["line"]["path"], "live-worker-file")).st_mode & 0o7777, 0o600)

    def test_partial_initial_failure_keeps_materializing_and_retry_can_finish(self):
        from baton_v12.worker_manager import workspaces
        with mock.patch.object(workspaces.os, "fchmod", side_effect=PermissionError("injected")):
            with self.assertRaisesRegex(ContractRefusal, "partial provisioning"):
                self.line()
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
            {"custody": "normalize", "entries": 0, "not_ours": 0,
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
        worker answer and nothing accounted for."""
        self.store._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = 'running' "
            "WHERE runtime_attempt_id = ?", ("runtime-" + attempt_id,
                                             attempt_id))

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

    def restore(self, **overrides):
        operands = {"attempt_id": self.abandoned_attempt, "generation": 2,
                    "retention_policy_digest": RETENTION,
                    "profile": self.profile}
        operands.update(overrides)
        return restore_abandoned_correction(self.store, **operands)

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
        """
        self.abandoned()
        answered = self.restore()
        self.store._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            (answered["operation_id"],))
        refusal = self.refused()
        self.assertEqual(refusal.category, "refused")
        self.assertIn("revoked", refusal.message)

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
        self.abandoned()
        self.profile.restore_refusal = ContractRefusal(
            "policy", "profile-uncertified", "the checkout could not be reset")
        self.assertEqual(self.refused().code, "profile-uncertified")
        # THE EXCLUSION IS EXACTLY WHERE IT WAS.
        self.assertEqual(line_of(self.store, self.line_id)["state"], "writing")
        self.assertEqual(
            writer_of(self.store, self.writer_row["writer_id"])["state"],
            "active")
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual(self.refused(self.admit).category, "refused")

    def test_the_effect_and_the_release_happen_in_one_serialized_act(self):
        """REVIEW 2026-09-09T16:04Z, and the reviewer's proposal is where this
        finally lands.

        My first cut revoked at completion and checked before the write; my
        second revoked in the intent and checked again. Neither serializes an
        effect that happens BETWEEN a check and a commit. `store.transact` does:
        it takes the write lock, re-reads the replay under it, runs the action
        and commits together -- so the restoration and the release that lets a
        successor in are one act.

        WHAT THIS MEASURES is that the effect really is inside it: at the
        moment the profile is asked, the exclusion is untouched and the
        completion is not yet committed, and both change only when the
        transaction does.
        """
        self.abandoned()
        seen = {}
        original = self.profile.restore_checkpoint

        def watching(repository, evidence):
            seen["writer"] = writer_of(
                self.store, self.writer_row["writer_id"])["state"]
            seen["line"] = line_of(self.store, self.line_id)["state"]
            seen["completed"] = abandoned_correction_of(
                self.store, attempt_id=self.abandoned_attempt, generation=2)
            return original(repository, evidence)

        self.profile.restore_checkpoint = watching
        answered = self.restore()
        self.assertEqual(seen["writer"], "active")
        self.assertEqual(seen["line"], "writing")
        self.assertIsNone(seen["completed"])
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
        first one's profile effect. On one connection that is REENTRY, not a
        second transaction: a nested `transact` would release the outer act's
        savepoint. It is refused there, so no second effect and no release to a
        successor happens while the first act holds the lock.
        """
        self.abandoned()
        original = self.profile.restore_checkpoint
        resumed = {}

        def paused(repository, evidence):
            if resumed:
                return original(repository, evidence)
            resumed["b"] = self.refused(
                lambda: restore_abandoned_correction(
                    self.store, attempt_id=self.abandoned_attempt,
                    generation=2, retention_policy_digest=RETENTION,
                    profile=self.profile))
            resumed["admission"] = self.refused(self.admit).category
            return original(repository, evidence)

        self.profile.restore_checkpoint = paused
        answered = self.restore()

        self.assertEqual((resumed["b"].category, resumed["b"].code),
                         ("refused", "operation-collision"))
        self.assertIn("nested restoration", resumed["b"].message)
        # NO SUCCESSOR WAS ADMITTED IN THE WINDOW, and exactly one effect ran.
        self.assertEqual(resumed["admission"], "refused")
        self.assertEqual(len(self.profile.restore_calls), 1)
        self.assertEqual(answered["state"], "correction-ready")

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
                retention_policy_digest=RETENTION, profile=self.profile),
            first)
        self.assertEqual(len(self.profile.restore_calls), calls)

    def test_the_exclusion_is_proved_under_the_lock_and_not_before_it(self):
        """A line moved between the entry proof and the transaction is caught
        by the re-read inside the write, which is where a decision that
        authorizes a destructive act has to be made."""
        self.abandoned()
        original = store_transact = type(self.store).transact
        moved = {}

        def moving(store, operation_id, kind, signature, action):
            if operation_id.startswith("review-line.restore-abandoned:") \
                    and not moved:
                moved["yes"] = True
                store._connection.execute(
                    "UPDATE review_lines SET state = 'reviewing' "
                    "WHERE line_id = ?", (self.line_id,))
            return original(store, operation_id, kind, signature, action)

        with mock.patch.object(type(self.store), "transact", moving):
            refusal = self.refused()
        self.assertEqual(refusal.category, "refused")
        self.assertIn("no longer holds the exclusion", refusal.message)
        self.assertEqual(self.profile.restore_calls, [])
        self.assertIsNone(abandoned_correction_of(
            self.store, attempt_id=self.abandoned_attempt, generation=2))
        self.assertEqual(store_transact, original)

    def test_an_interrupted_restore_finishes_under_the_same_exclusion(self):
        """The intent commits before the profile act, so a crash between them
        leaves a recorded intent with no completion -- which is exactly what a
        retry has to find."""
        self.abandoned()
        self.profile.restore_refusal = ContractRefusal(
            "policy", "profile-uncertified", "interrupted")
        self.refused()
        self.profile.restore_refusal = None
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

    def test_a_transient_profile_failure_stays_retryable(self):
        """The effect runs inside `transact`, so its failure must not become a
        journalled refusal: `ProfileRefusal` is not a `ContractRefusal` and
        takes the fault branch, which rolls the whole transaction back and
        leaves the committed intent standing."""
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
            "active")
        self.profile.restore_refusal = None
        self.assertEqual(self.restore()["state"], "correction-ready")

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
