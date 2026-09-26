"""A pending submitter must be refused before execution-root deletion."""
import os
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import intake, workspaces
from tests.manager.test_intake import IntakeCase, ATTEMPT, RETENTION, Custodian


class IntakeOrder(IntakeCase):
    def test_pending_submitter_preserves_execution_roots(self):
        self.retained_ready("discard-after-intake")
        self.ended()
        storage = workspaces.configured_workspace_storage(self.store).place
        workspaces.assignment_workspace(workspaces.configured_workspace_group(self.store), storage, ATTEMPT)
        home = os.path.join(storage, ATTEMPT)
        inputs = os.path.join(home, "inputs")
        self.assertTrue(os.path.isdir(inputs), "fixture must provide actual execution roots")
        marker = os.path.join(inputs, "review-submit-still-pending")
        os.chmod(inputs, 0o700)
        with open(marker, "w") as stream:
            stream.write("submitter still owns this material")
        with mock.patch.object(intake.attempts, "start_submission_returned", return_value=False):
            with self.assertRaises(ContractRefusal) as refused:
                intake.authorize_cleanup(self.store, self.port, Custodian(),
                                         attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        self.assertIn("start submission has not", refused.exception.message)
        self.assertTrue(os.path.isfile(marker), "cleanup refused only after deleting pending submitter roots")


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([IntakeOrder("test_pending_submitter_preserves_execution_roots")])
