"""Fail-closed root and traversal checks for selected output assessment."""
import os
import unittest
from unittest.mock import patch
from tests.manager.test_maintenance import MaintenanceCase
from baton_v12.worker_manager import intake

class OutputAccess(MaintenanceCase):
    def test_inaccessible_empty_root_is_not_success(self):
        root=os.path.join(self.workspace,'empty-output')
        os.mkdir(root,0o700)
        self.assertIsNotNone(intake.inaccessible_output(self.store,'attempt-1',{'result':root,'workspace':root}))

    def test_denied_traversal_is_not_success(self):
        with patch.object(os,'scandir',side_effect=PermissionError(13,'denied traversal',self.workspace)):
            self.assertIsNotNone(intake.inaccessible_output(self.store,'attempt-1',{'result':self.workspace,'workspace':self.workspace}))

if __name__ == '__main__':
    unittest.main()
