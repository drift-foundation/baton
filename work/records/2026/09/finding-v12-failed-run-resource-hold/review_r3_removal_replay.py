"""Repeated execution-root removal must retain its public result contract."""
import unittest
from baton_v12.worker_manager import workspaces
from test_resource_guards import AHeldResourceIsNotRemoved


class RemovalReplay(AHeldResourceIsNotRemoved):
    def test_repeated_execution_removal_reports_no_remaining_roots(self):
        control, _composed, attempt, held = self.held_episode("removal-replay")
        self.clearing(control, attempt, held)
        storage = self.storage_of(control)
        first = workspaces.discard_execution_roots(storage, attempt,
                                                   control=control)
        self.assertEqual(sorted(first), ["inputs", "workspace"])
        self.assertEqual(workspaces.discard_execution_roots(
            storage, attempt, control=control), ())


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([RemovalReplay(
        "test_repeated_execution_removal_reports_no_remaining_roots")])
