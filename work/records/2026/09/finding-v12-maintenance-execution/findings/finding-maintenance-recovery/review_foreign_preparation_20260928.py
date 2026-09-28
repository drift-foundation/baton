"""A foreign preparation's colliding ordinal is not the target window's ownership."""
import unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import workspaces
from tests.manager.test_workspaces import Workspace

class ForeignPreparation(Workspace):
    def test_foreign_ordinal_cannot_adopt_target_held_roots(self):
        mine = workspaces.admit_preparation(self.store, "attempt-target", "target writer", "execution-target")
        other = workspaces.admit_preparation(self.store, "attempt-foreign", "foreign writer", "execution-foreign")
        try:
            self.assertEqual(mine.ordinal, other.ordinal)
            workspaces.assignment_workspace(self.group, self.storage, "attempt-target", control=self.store, preparing=mine.ordinal)
            with self.assertRaises(ContractRefusal):
                roots = workspaces.adopted_assignment_workspace(self.storage, "attempt-target", control=self.store, preparing=other.ordinal)
                workspaces.release_adopted_workspace(roots)
        finally:
            workspaces.release_preparation(self.store, other, "foreign writer returned")
            workspaces.release_preparation(self.store, mine, "target writer returned")

if __name__ == "__main__":
    unittest.main(defaultTest="ForeignPreparation.test_foreign_ordinal_cannot_adopt_target_held_roots")
