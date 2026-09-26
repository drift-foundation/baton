"""A process-wide matching descriptor is not the selected SQLite connection."""
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, workspaces
from tests.manager.test_intake import ATTEMPT
from review_cleanup_gap_20260926 import CleanupGap


class ConnectionAttribution(CleanupGap):
    def test_other_handle_cannot_attest_to_replacement_connection(self):
        storage = self.interrupted()
        group = workspaces.configured_workspace_group(self.store)
        database = self.store.database
        self.assertTrue(workspaces.standing_cleanup(self.store, ATTEMPT))
        self.store.close()
        with tempfile.TemporaryDirectory(dir=os.path.dirname(database)) as directory:
            replacement = os.path.join(directory, "replacement.sqlite3")
            original = os.path.join(directory, "original.sqlite3")
            other = ControlStore.open(replacement, incarnation="review-replacement",
                                      clock=self.store._clock)
            workspaces.configure_workspace_storage(other, storage)
            other.close()
            witness = os.open(database, os.O_RDONLY)
            honest = sqlite3.connect
            swapped = []

            def swap_open_restore(*args, **kwargs):
                swapped.append(True)
                os.rename(database, original)
                os.rename(replacement, database)
                opened = honest(*args, **kwargs)
                os.rename(database, replacement)
                os.rename(original, database)
                return opened

            try:
                refused = False
                with mock.patch.object(sqlite3, "connect", side_effect=swap_open_restore):
                    try:
                        workspaces.assignment_workspace(group, storage, ATTEMPT, control=self.store)
                    except ContractRefusal:
                        refused = True
                self.assertEqual(swapped, [True])
                self.assertTrue(refused, "unrelated original descriptor vouched for replacement SQLite connection")
            finally:
                os.close(witness)


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([ConnectionAttribution(
        "test_other_handle_cannot_attest_to_replacement_connection")])
