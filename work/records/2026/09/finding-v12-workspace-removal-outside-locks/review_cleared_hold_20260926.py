"""Deterministic reader-boundary proof: cleared history is not a standing hold.

Simulates custody_holds' validated output, not an operator clearance receipt.
Exercises real standalone removal admission and disposable filesystem objects.
"""
import unittest
from unittest import mock

from test_removal_outside_the_lock import RemovalOutsideTheLock
from baton_v12.worker_manager import custody, workspaces


class ClearedHistory(RemovalOutsideTheLock):
    def test_cleared_history_allows_removal(self):
        self.attempt_roots()

        def history(store, assignment_id, which):
            return [{"cleared": True, "episode": 0}] if which == "workspace" else []

        with mock.patch.object(custody, "custody_holds", side_effect=history):
            self.assertTrue(workspaces.discard_workspace(
                self.storage, "assignment-1", control=self.store))


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([ClearedHistory("test_cleared_history_allows_removal")])
