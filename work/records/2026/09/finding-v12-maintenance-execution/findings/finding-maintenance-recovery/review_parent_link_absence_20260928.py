"""A missing child through a substituted parent is not authenticated absence."""
import os
import tempfile
import unittest
from tests.manager import test_maintenance as fixture
from baton_v12.worker_manager import intake, workspaces
from baton_v12.contracts import ContractRefusal

class ParentLinkAbsence(unittest.TestCase):
    def test_parent_link_to_empty_directory_does_not_prove_roots_absent(self):
        case = fixture.TheORDINARYEndingCompletesWithNoHelperOrItHolds()
        case.setUp()
        self.addCleanup(case.doCleanups)
        storage = workspaces.configured_workspace_storage(case.case.store).place
        home = os.path.join(storage, case.intake.ATTEMPT)
        target = tempfile.TemporaryDirectory(prefix="review-parent-link-")
        self.addCleanup(target.cleanup)
        os.rename(home, home + "-original")
        os.symlink(target.name, home)
        with self.assertRaises(ContractRefusal):
            intake._output_root_identities(case.case.store, case.intake.ATTEMPT)

if __name__ == "__main__":
    unittest.main()
