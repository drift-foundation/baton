"""An unobservable authority journal must not disable allocation exclusion."""
import os
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import workspaces
from tests.manager.test_intake import ATTEMPT
from review_cleanup_gap_20260926 import CleanupGap


class AllocationUncertainty(CleanupGap):
    def test_permission_error_observing_journal_does_not_allow_allocation(self):
        storage = self.interrupted()
        self.assertTrue(workspaces.standing_cleanup(self.store, ATTEMPT))
        group = workspaces.configured_workspace_group(self.store)
        database = group.store_place
        self.assertTrue(os.path.isfile(database))
        self.store._connection.close()
        honest = os.stat
        observed = []

        def unreadable(path, *args, **kwargs):
            if path == database:
                observed.append(path)
                raise PermissionError("review journal observation denied")
            return honest(path, *args, **kwargs)

        refused = False
        with mock.patch.object(os, "stat", side_effect=unreadable):
            try:
                workspaces.assignment_workspace(group, storage, ATTEMPT)
            except ContractRefusal:
                refused = True
        self.assertTrue(observed, "must exercise the journal observation")
        self.assertTrue(refused, "unobservable journal allowed allocation despite durable cleanup hold")
        self.assertFalse(os.path.exists(os.path.join(storage, ATTEMPT, "inputs")))


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([AllocationUncertainty(
        "test_permission_error_observing_journal_does_not_allow_allocation")])
