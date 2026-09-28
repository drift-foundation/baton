"""Genuine preparation ownership from another store must not exempt this store's writer."""
import os
import unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, workspaces
from tests.manager.test_workspaces import Workspace

class CrossStoreReentry(Workspace):
    def test_other_store_capability_cannot_reenter_target_preparation(self):
        workspaces.assignment_workspace(self.group, self.storage, "attempt-target", control=self.store)
        other_storage = os.path.join(self.root, "other-storage")
        os.mkdir(other_storage)
        other = ControlStore.open(os.path.join(self.root, "other.sqlite3"), incarnation="other-instance", clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(other.close)
        workspaces.configure_workspace_storage(other, other_storage)
        mine = workspaces.admit_preparation(self.store, "attempt-target", "target writer", "target-execution")
        theirs = workspaces.admit_preparation(other, "attempt-target", "other writer", "other-execution")
        try:
            self.assertEqual(mine.ordinal, theirs.ordinal)
            with self.assertRaises(ContractRefusal):
                workspaces.admit_preparation(self.store, "attempt-target", "foreign reentry", "target-execution", holding=theirs)
        finally:
            workspaces.release_preparation(other, theirs, "other writer returned")
            workspaces.release_preparation(self.store, mine, "target writer returned")

if __name__ == "__main__":
    unittest.main(defaultTest="CrossStoreReentry.test_other_store_capability_cannot_reenter_target_preparation")
