"""Lifetime must survive grant binding and recomposition with a persistent line."""
import os
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import workspaces
from test_removal_outside_the_lock import RemovalOutsideTheLock


class AdoptionTransfer(RemovalOutsideTheLock):
    def assert_removal_excluded(self, roots):
        with self.assertRaises(ContractRefusal):
            workspaces.discard_workspace(self.storage, "assignment-1", control=self.store)
        self.assertTrue(os.path.isdir(roots["inputs"]))

    def test_bare_adoption_excludes_until_explicit_release(self):
        self.attempt_roots()
        roots = workspaces.adopted_assignment_workspace(self.storage, "assignment-1", control=self.store)
        self.assert_removal_excluded(roots)
        workspaces.release_adopted_workspace(roots)
        self.assertTrue(workspaces.discard_workspace(self.storage, "assignment-1", control=self.store))

    def test_grant_binding_preserves_removal_exclusion(self):
        self.attempt_roots()
        adopted = workspaces.adopted_assignment_workspace(self.storage, "assignment-1", control=self.store)
        roots = workspaces._granted_roots(adopted, lambda: True)
        self.assert_removal_excluded(roots)

    def test_line_roots_preserve_inputs_exclusion(self):
        self.attempt_roots()
        place = os.path.join(self.storage, workspaces._REVIEW_LINE_HOME, "review-transfer")
        os.makedirs(place)
        held = os.stat(place)
        roots = workspaces.line_assignment_workspace(
            self.storage, "assignment-1", place, (held.st_dev, held.st_ino), control=self.store)
        self.assert_removal_excluded(roots)


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(AdoptionTransfer(name) for name in (
        "test_bare_adoption_excludes_until_explicit_release",
        "test_grant_binding_preserves_removal_exclusion",
        "test_line_roots_preserve_inputs_exclusion"))
