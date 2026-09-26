"""Reopening must retain the explicitly selected allocation authority."""
import os
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, workspaces
from tests.manager import input_roots
from tests.manager.test_intake import ATTEMPT
from review_cleanup_gap_20260926 import CleanupGap


class ExplicitControl(CleanupGap):
    def test_closed_explicit_control_does_not_reopen_group_minter(self):
        storage = self.interrupted()
        self.assertTrue(workspaces.standing_cleanup(self.store, ATTEMPT))
        with tempfile.TemporaryDirectory(dir=os.environ["BATON_V12_DISK_ROOT"]) as directory:
            other = ControlStore.open(os.path.join(directory, "other.sqlite3"),
                incarnation="review-other", clock=self.store._clock)
            try:
                group = input_roots.configured_group(other)
                workspaces.configure_workspace_storage(other, storage)
                self.assertFalse(workspaces.standing_cleanup(other, ATTEMPT))
                self.store._connection.close()
                with self.assertRaises(ContractRefusal):
                    workspaces.assignment_workspace(group, storage, ATTEMPT, control=self.store)
            finally:
                other.close()


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([ExplicitControl(
        "test_closed_explicit_control_does_not_reopen_group_minter")])
