"""Observe filesystem calls in real cleanup and refused nested removal."""
import contextlib
import os
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import intake, workspaces
from tests.manager.test_intake import IntakeCase, ATTEMPT, RETENTION, Custodian


class CleanupIO(IntakeCase):
    def prepared(self):
        self.retained_ready("discard-after-intake")
        self.ended()
        storage = workspaces.configured_workspace_storage(self.store).place
        workspaces.assignment_workspace(workspaces.configured_workspace_group(self.store), storage, ATTEMPT)
        return storage

    @contextlib.contextmanager
    def observing(self):
        seen = []
        with contextlib.ExitStack() as stack:
            for name in ("lstat", "stat", "fstat", "readlink", "open", "scandir", "chmod", "fchmod", "unlink", "rmdir", "access"):
                honest = getattr(os, name)

                def watched(*args, _name=name, _honest=honest, **kwargs):
                    seen.append((_name, self.store._connection.in_transaction))
                    return _honest(*args, **kwargs)

                stack.enter_context(mock.patch.object(os, name, side_effect=watched))
            yield seen

    def test_enclosing_cleanup_filesystem_calls_are_outside_transactions(self):
        self.prepared()
        with self.observing() as seen:
            intake.authorize_cleanup(self.store, self.port, Custodian(),
                                     attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        self.assertTrue(seen)
        self.assertFalse([name for name, locked in seen if locked])

    def test_nested_removal_refuses_before_filesystem_calls(self):
        storage = self.prepared()
        self.store._connection.execute("BEGIN IMMEDIATE")
        try:
            with self.observing() as seen:
                with self.assertRaises(ContractRefusal):
                    workspaces.discard_workspace(storage, ATTEMPT, control=self.store)
            self.assertFalse(seen, "nested refusal happened after filesystem I/O under caller lock")
        finally:
            self.store._connection.execute("ROLLBACK")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(CleanupIO(name) for name in (
        "test_enclosing_cleanup_filesystem_calls_are_outside_transactions",
        "test_nested_removal_refuses_before_filesystem_calls"))
