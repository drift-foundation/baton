"""Owned preparation must reach adoption's atomic admission, not only its early read."""
import unittest
from baton_v12.worker_manager import workspaces
from tests.manager.test_workspaces import Workspace

class PreparationAdoption(Workspace):
    def test_holder_can_adopt_before_preparation_completes(self):
        owned = workspaces.admit_preparation(self.store, "attempt-review", "review probe", "execution-review")
        try:
            workspaces.assignment_workspace(self.group, self.storage, "attempt-review", control=self.store, preparing=owned.ordinal)
            roots = workspaces.adopted_assignment_workspace(self.storage, "attempt-review", control=self.store, preparing=owned.ordinal)
            workspaces.release_adopted_workspace(roots)
        finally:
            workspaces.release_preparation(self.store, owned, "probe writer returned")

if __name__ == "__main__":
    unittest.main(defaultTest="PreparationAdoption.test_holder_can_adopt_before_preparation_completes")
