"""Reviewer regression: a different journal cannot authorize held-root deletion."""
import os
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, workspaces
from tests.job_manager import fixtures
from test_resource_guards import AHeldResourceIsNotRemoved


class StoreBinding(AHeldResourceIsNotRemoved):
    def test_unrelated_store_cannot_authorize_deletion(self):
        control, _composed, attempt, _held = self.held_episode("review-binding")
        storage = self.storage_of(control)
        home = self.home_of(control, attempt)
        with tempfile.TemporaryDirectory(dir="/var/tmp/baton-w257624",
                                         prefix="review-r3-store-") as room:
            with ControlStore.open(os.path.join(room, "unrelated.sqlite"),
                                   incarnation="unrelated",
                                   clock=lambda: fixtures.NOW) as unrelated:
                with self.assertRaises(ContractRefusal):
                    workspaces.discard_workspace(storage, attempt,
                                                 control=unrelated)
        self.assertTrue(os.path.isdir(home))


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([
        StoreBinding("test_unrelated_store_cannot_authorize_deletion")])
