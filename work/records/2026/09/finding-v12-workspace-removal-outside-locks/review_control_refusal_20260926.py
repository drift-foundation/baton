"""Safe refusal replaces implicit reopening; usable local handles still allocate."""
import concurrent.futures
import os
import sqlite3
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, workspaces
from tests.manager.test_intake import ATTEMPT
from review_cleanup_gap_20260926 import CleanupGap


class ControlRefusal(CleanupGap):
    def test_closed_control_preserves_hold_without_reopen(self):
        storage = self.interrupted()
        group = workspaces.configured_workspace_group(self.store)
        self.assertTrue(workspaces.standing_cleanup(self.store, ATTEMPT))
        self.store.close()
        with mock.patch.object(sqlite3, "connect", side_effect=AssertionError("implicit reopen")):
            with self.assertRaises(ContractRefusal):
                workspaces.assignment_workspace(group, storage, ATTEMPT, control=self.store)
        for root in ("inputs", "workspace"):
            self.assertFalse(os.path.exists(os.path.join(storage, ATTEMPT, root)))

    def test_off_thread_shared_control_refuses_before_creation(self):
        storage = self.prepared()
        group = workspaces.configured_workspace_group(self.store)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            with self.assertRaises(ContractRefusal):
                pool.submit(workspaces.assignment_workspace, group, storage,
                            "review-shared-thread", control=self.store).result(10)
        self.assertFalse(os.path.exists(os.path.join(storage, "review-shared-thread")))

    def test_thread_local_control_allocates(self):
        storage = self.prepared()
        group = workspaces.configured_workspace_group(self.store)
        database = self.store.database
        clock = self.store._clock

        def allocate():
            local = ControlStore.open(database, incarnation="review-local", clock=clock)
            try:
                return workspaces.assignment_workspace(group, storage,
                    "review-local-thread", control=local)
            finally:
                local.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            roots = pool.submit(allocate).result(10)
        self.assertTrue(os.path.isdir(roots["inputs"]))
        self.assertTrue(os.path.isdir(roots["workspace"]))


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(ControlRefusal(name) for name in (
        "test_closed_control_preserves_hold_without_reopen",
        "test_off_thread_shared_control_refuses_before_creation",
        "test_thread_local_control_allocates"))
