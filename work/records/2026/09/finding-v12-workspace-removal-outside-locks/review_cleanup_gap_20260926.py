"""Independent cleanup completion-gap exclusion and retry regression."""
import os
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import intake, workspaces
from tests.manager.test_intake import ATTEMPT, RETENTION, Custodian
from review_cleanup_io_20260926 import CleanupIO


class CleanupGap(CleanupIO):
    def interrupted(self):
        storage = self.prepared()
        transact = self.store.transact
        reached = []

        def stop(operation_id, kind, *args, **kwargs):
            if kind == "runtime.destroy":
                reached.append(operation_id)
                raise RuntimeError("review interruption before cleanup commit")
            return transact(operation_id, kind, *args, **kwargs)

        with mock.patch.object(self.store, "transact", side_effect=stop):
            with self.assertRaisesRegex(RuntimeError, "review interruption"):
                self.cleanup()
        self.assertEqual(len(reached), 1)
        for root in ("inputs", "workspace"):
            self.assertFalse(os.path.exists(os.path.join(storage, ATTEMPT, root)))
        return storage

    def cleanup(self):
        return intake.authorize_cleanup(self.store, self.port, Custodian(),
                                        attempt_id=ATTEMPT, retention_policy_digest=RETENTION)

    def test_allocation_refuses_uncommitted_cleanup_gap(self):
        storage = self.interrupted()
        with self.assertRaises(ContractRefusal):
            workspaces.assignment_workspace(workspaces.configured_workspace_group(self.store), storage, ATTEMPT)

    def test_retry_does_not_delete_newly_allocated_material(self):
        storage = self.interrupted()
        try:
            workspaces.assignment_workspace(workspaces.configured_workspace_group(self.store), storage, ATTEMPT)
        except ContractRefusal:
            # Excluding the new allocation is also a valid protection.
            self.cleanup()
            return
        inputs = os.path.join(storage, ATTEMPT, "inputs")
        os.chmod(inputs, 0o700)
        marker = os.path.join(inputs, "review-fresh-allocation")
        with open(marker, "w") as stream:
            stream.write("created after removal completion, before cleanup commit")
        try:
            self.cleanup()
        except ContractRefusal:
            pass
        self.assertTrue(os.path.isfile(marker), "cleanup retry deleted newly allocated material")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(CleanupGap(name) for name in (
        "test_allocation_refuses_uncommitted_cleanup_gap",
        "test_retry_does_not_delete_newly_allocated_material"))
