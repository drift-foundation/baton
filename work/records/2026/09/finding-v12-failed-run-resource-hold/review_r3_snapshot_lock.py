"""A read snapshot is not the write lock needed for resource removal."""
import os
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, custody, workspaces
from tests.job_manager import fixtures
from test_resource_guards import AHeldResourceIsNotRemoved


class SnapshotIsNotRemovalAuthority(AHeldResourceIsNotRemoved):
    def test_stale_readonly_snapshot_cannot_delete_newly_held_resource(self):
        control, composed, attempt, held = self.held_episode("snapshot-lock")
        self.clearing(control, attempt, held)
        storage = self.storage_of(control)
        with ControlStore.open_readonly(self.control_path,
                                       incarnation="snapshot-reader",
                                       clock=lambda: fixtures.NOW) as reader:
            with reader.snapshot():
                self.assertTrue(custody.custody_holds(reader, attempt,
                                                      "result")[0]["cleared"])
                with self.assertRaises(ContractRefusal):
                    custody.normalize_directory(control, composed,
                                                assignment_id=attempt,
                                                which="result")
                self.assertFalse(custody.custody_holds(control, attempt,
                                                       "result")[-1]["cleared"])
                with self.assertRaises(ContractRefusal):
                    workspaces.discard_workspace(storage, attempt,
                                                 control=reader)
        self.assertTrue(os.path.isdir(self.home_of(control, attempt)))


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([SnapshotIsNotRemovalAuthority(
        "test_stale_readonly_snapshot_cannot_delete_newly_held_resource")])
