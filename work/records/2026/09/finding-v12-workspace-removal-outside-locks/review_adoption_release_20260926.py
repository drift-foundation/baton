"""Release retry and failed composition must retain a usable settlement path."""
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import workspaces
from test_removal_outside_the_lock import RemovalOutsideTheLock


class AdoptionRelease(RemovalOutsideTheLock):
    def test_failed_release_can_retry(self):
        self.attempt_roots()
        roots = workspaces.adopted_assignment_workspace(self.storage, "assignment-1", control=self.store)
        with mock.patch.object(workspaces, "_settled_adoption", side_effect=RuntimeError("settlement failed")):
            with self.assertRaisesRegex(RuntimeError, "settlement failed"):
                workspaces.release_adopted_workspace(roots)
        self.assertIsNotNone(roots._adoption)
        self.assertTrue(workspaces.standing_adoption(self.store, "assignment-1"))
        workspaces.release_adopted_workspace(roots)
        self.assertIsNone(roots._adoption)
        self.assertFalse(workspaces.standing_adoption(self.store, "assignment-1"))
        workspaces.release_adopted_workspace(roots)

    def test_rejected_line_composition_leaves_no_unowned_adoption(self):
        self.attempt_roots()
        with self.assertRaises(ContractRefusal):
            workspaces.line_assignment_workspace(
                self.storage, "assignment-1", self.storage, (0, 0), control=self.store)
        self.assertFalse(workspaces.standing_adoption(self.store, "assignment-1"),
                         "no roots were returned, but their adoption remains without a release handle")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(AdoptionRelease(name) for name in (
        "test_failed_release_can_retry",
        "test_rejected_line_composition_leaves_no_unowned_adoption"))
