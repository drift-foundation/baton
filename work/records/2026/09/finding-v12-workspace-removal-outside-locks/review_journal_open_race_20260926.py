"""Journal pathname verification must bind the connection actually opened."""
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, workspaces
from tests.manager.test_intake import ATTEMPT
from review_cleanup_gap_20260926 import CleanupGap


class JournalOpenRace(CleanupGap):
    def test_replacement_after_stat_cannot_answer_for_selected_journal(self):
        storage = self.interrupted()
        group = workspaces.configured_workspace_group(self.store)
        database = self.store.database
        self.assertTrue(workspaces.standing_cleanup(self.store, ATTEMPT))
        self.store.close()
        with tempfile.TemporaryDirectory(dir=os.path.dirname(database)) as directory:
            replacement = os.path.join(directory, "replacement.sqlite3")
            other = ControlStore.open(replacement, incarnation="review-replacement",
                                      clock=self.store._clock)
            workspaces.configure_workspace_storage(other, storage)
            other.close()
            honest = sqlite3.connect
            swapped = []

            def swap_then_open(*args, **kwargs):
                swapped.append(True)
                os.rename(database, os.path.join(directory, "original.sqlite3"))
                os.rename(replacement, database)
                return honest(*args, **kwargs)

            refused = False
            with mock.patch.object(sqlite3, "connect", side_effect=swap_then_open):
                try:
                    workspaces.assignment_workspace(group, storage, ATTEMPT, control=self.store)
                except ContractRefusal:
                    refused = True
            self.assertEqual(swapped, [True], "must swap after pathname check, before open")
            self.assertTrue(refused, "replacement journal allowed allocation over original cleanup hold")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([JournalOpenRace(
        "test_replacement_after_stat_cannot_answer_for_selected_journal")])
