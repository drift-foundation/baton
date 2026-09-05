"""Executable review gaps in W71918 proposal f464588c... .

These cases pass when the unwanted behavior is present. They use the
candidate's own focused-test profile and attempt fixture, but exercise seams
the candidate suite does not assert.
"""

import os
import tempfile
import unittest

from baton_v12.worker_manager import (ControlStore, attach_review, create_line,
                                      freeze_checkpoint, grant_writer,
                                      integration_checkpoint, record_verdict,
                                      writer_boundary)
from baton_v12.worker_manager.source_boundary import (adopt_source_boundary,
                                                       boundary_mounts,
                                                       nominate_source)
from baton_v12.worker_manager.workspaces import (assignment_workspace,
                                                 configure_workspace_storage)
from tests.manager import input_roots
from tests.manager.disk_roots import disk_backed_under
from tests.manager.test_review_cycles import (AUTHORITY, BASE, NOW, WORK,
                                               Profile)


class MissingLifecycleFences(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.source = os.path.join(self.temporary.name, "source")
        os.mkdir(self.source)
        disk = disk_backed_under(self)
        self.configured_storage = os.path.join(disk, "configured")
        self.other_storage = os.path.join(disk, "caller-selected")
        os.mkdir(self.configured_storage)
        os.mkdir(self.other_storage)
        self.store = ControlStore.open(
            os.path.join(self.temporary.name, "control.sqlite3"),
            incarnation="review-repro", clock=lambda: NOW)
        self.addCleanup(self.store.close)
        self.profile = Profile()
        self.group = input_roots.configured_group(self.store)
        configure_workspace_storage(self.store, self.configured_storage)

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

    def line(self, storage=None):
        return create_line(
            self.store, storage=storage or self.configured_storage,
            source=nominate_source(self.source), declared_base=BASE,
            profile=self.profile, authority_uuid=AUTHORITY, work_id=WORK)

    def writer(self, line, attempt_id="writer-attempt", generation=1):
        self.attempt(attempt_id, generation, "baton.impl", "writer-principal")
        assignment_workspace(self.group, self.other_storage, attempt_id)
        return grant_writer(
            self.store, line_id=line["line_id"], attempt_id=attempt_id,
            generation=generation, worker_id="writer-worker",
            profile=self.profile)

    def test_revoked_writer_mount_capability_remains_live(self):
        line = self.line(self.other_storage)
        writer = self.writer(line)
        composed = writer_boundary(
            self.store, writer_id=writer["writer_id"], generation=1,
            storage=self.other_storage)
        checkpoint = freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, quiescent=lambda attempt: True)
        self.assertEqual(checkpoint["revision"], 1)

        # The database says revoked, but the already-minted roots and source
        # boundary remain usable and adoptable without consulting that state.
        adopted = adopt_source_boundary(
            composed["boundary"], composed["roots"], pinned=(
                (composed["boundary"].device,
                 composed["boundary"].inode),
                (composed["boundary"].workspace_device,
                 composed["boundary"].workspace_inode)))
        self.assertEqual(boundary_mounts(adopted)[1],
                         (line["path"], "/output", True))

    def test_acceptance_needs_no_reviewer_runtime_result_or_logs(self):
        line = self.line()
        writer = self.writer(line)
        checkpoint = freeze_checkpoint(
            self.store, writer_id=writer["writer_id"], generation=1,
            profile=self.profile, quiescent=lambda attempt: True)
        self.attempt("review-attempt", 2, "baton.review", "review-principal")
        attempt = self.store._connection.execute(
            "SELECT runtime_id, execution_runtime, worker_disposition, output, "
            "verification FROM attempts WHERE runtime_attempt_id = 'review-attempt'"
        ).fetchone()
        self.assertEqual(tuple(attempt),
                         (None, "not-started", "none", "open", "none"))
        attachment = attach_review(
            self.store, checkpoint_id=checkpoint["checkpoint_id"],
            attempt_id="review-attempt", generation=2,
            reviewer_worker_id="review-worker", profile=self.profile)
        record_verdict(self.store, attachment_id=attachment["attachment_id"],
                       disposition="accepted", profile=self.profile)
        self.assertEqual(
            integration_checkpoint(self.store, line["line_id"])["checkpoint_id"],
            checkpoint["checkpoint_id"])

    def test_caller_selected_storage_mints_a_runtime_mount(self):
        line = self.line(self.other_storage)
        writer = self.writer(line)
        mounted = writer_boundary(
            self.store, writer_id=writer["writer_id"], generation=1,
            storage=self.other_storage)
        self.assertNotEqual(self.other_storage, self.configured_storage)
        self.assertEqual(boundary_mounts(mounted["boundary"])[1],
                         (line["path"], "/output", True))


if __name__ == "__main__":
    unittest.main()
