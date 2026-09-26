"""Adoption must not return roots already removed after its premature settlement."""
import os
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import workspaces
from test_removal_outside_the_lock import RemovalOutsideTheLock


class AdoptionLifetime(RemovalOutsideTheLock):
    def test_removal_cannot_win_before_adoption_returns_roots(self):
        self.attempt_roots()
        honest = workspaces._settled_adoption
        removals = []

        def settled(control, assignment_id, owned):
            answer = honest(control, assignment_id, owned)
            try:
                removals.append(workspaces.discard_workspace(
                    self.storage, assignment_id, control=control))
            except ContractRefusal:
                removals.append(False)
            return answer

        with mock.patch.object(workspaces, "_settled_adoption", side_effect=settled):
            roots = workspaces.adopted_assignment_workspace(
                self.storage, "assignment-1", control=self.store)
        self.assertEqual(len(removals), 1)
        self.assertTrue(os.path.isdir(roots["inputs"]),
                        "adoption returned roots deleted before its caller received them")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([AdoptionLifetime(
        "test_removal_cannot_win_before_adoption_returns_roots")])
