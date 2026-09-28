"""A persistent line named workspace must not be classified as the attempt layout."""
import os
import unittest
from baton_v12.worker_manager import workspaces
from tests.manager.test_maintenance import THEREVALIDATIONComparesTheLayoutItsRecordIsAbout

class LayoutBasename(THEREVALIDATIONComparesTheLayoutItsRecordIsAbout):
    def test_line_named_workspace_revalidates(self):
        place, roots = self.line_roots()
        workspaces.release_adopted_workspace(roots)
        target = os.path.join(os.path.dirname(place), "workspace")
        os.rename(place, target)
        held = os.lstat(target)
        composed = workspaces.line_assignment_workspace(self.storage, self.ATTEMPT, target, (held.st_dev, held.st_ino), control=self.store)
        self.prepared(composed)
        workspaces.release_adopted_workspace(composed)
        self.attempt_row()
        self.live_task()
        self.assertEqual(self.revalidating()["workspace"], self.workspace)

if __name__ == "__main__":
    unittest.main(defaultTest="LayoutBasename.test_line_named_workspace_revalidates")
