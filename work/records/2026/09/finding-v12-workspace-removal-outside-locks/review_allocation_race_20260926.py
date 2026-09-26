"""Allocation must hold exclusion after its admission check returns."""
import os
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import intake, workspaces
from tests.manager.test_intake import ATTEMPT, RETENTION, Custodian
from review_cleanup_io_20260926 import CleanupIO


class AllocationRace(CleanupIO):
    def test_same_operation_retry_cannot_leave_old_remover_live_after_settlement(self):
        storage = self.prepared()
        group = workspaces.configured_workspace_group(self.store)
        honest = workspaces.discard_execution_roots
        interleaved = []
        marker = os.path.join(storage, ATTEMPT, "inputs", "review-after-settlement")

        def cleanup():
            return intake.authorize_cleanup(self.store, self.port, Custodian(),
                attempt_id=ATTEMPT, retention_policy_digest=RETENTION)

        def race(*args, **kwargs):
            if not interleaved:
                interleaved.append(True)
                cleanup()  # Second same-operation caller settles while first is paused.
                self.assertFalse(workspaces.standing_cleanup(self.store, ATTEMPT))
                workspaces.assignment_workspace(group, storage, ATTEMPT)
                os.chmod(os.path.dirname(marker), 0o700)
                with open(marker, "w") as stream:
                    stream.write("allocated after second caller settled")
            return honest(*args, **kwargs)

        with mock.patch.object(workspaces, "discard_execution_roots", side_effect=race):
            try:
                cleanup()
            except ContractRefusal:
                pass
        self.assertEqual(interleaved, [True])
        self.assertTrue(os.path.isfile(marker), "old same-operation remover deleted post-settlement allocation")

    def test_cleanup_admission_between_allocation_check_and_effect(self):
        storage = self.prepared()
        group = workspaces.configured_workspace_group(self.store)
        workspaces.discard_workspace(storage, ATTEMPT, control=self.store)
        honest = workspaces.refuse_if_held
        admitted = []

        def race(control, place, assignment, what, *args, **kwargs):
            result = honest(control, place, assignment, what, *args, **kwargs)
            admitted.append(workspaces.admit_cleanup(control, assignment,
                {"operation": "review-cleanup", "signature": "review-operands",
                 "incarnation": control.incarnation}, "review concurrent cleanup"))
            return result

        refused = False
        with mock.patch.object(workspaces, "refuse_if_held", side_effect=race):
            try:
                workspaces.assignment_workspace(group, storage, ATTEMPT)
            except ContractRefusal:
                refused = True
        self.assertEqual(len(admitted), 1, "must exercise the post-check interleaving")
        self.assertTrue(workspaces.standing_cleanup(self.store, ATTEMPT))
        self.assertTrue(refused, "allocation succeeded while concurrent cleanup owns the roots")
        self.assertFalse(os.path.exists(os.path.join(storage, ATTEMPT, "inputs")))


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(AllocationRace(name) for name in (
        "test_cleanup_admission_between_allocation_check_and_effect",
        "test_same_operation_retry_cannot_leave_old_remover_live_after_settlement"))
