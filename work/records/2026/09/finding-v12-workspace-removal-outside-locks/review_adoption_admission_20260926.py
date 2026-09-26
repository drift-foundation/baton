"""Read-before-use is not reciprocal admission: removal may win after adoption's read."""
import unittest
from unittest import mock
from test_removal_outside_the_lock import RemovalOutsideTheLock
from baton_v12.worker_manager import workspaces
from baton_v12.contracts import ContractRefusal


class AdoptionAdmission(RemovalOutsideTheLock):
    def test_adoption_cannot_finish_after_removal_admitted(self):
        self.attempt_roots()
        honest = workspaces.refuse_if_held
        admitted = []

        def checked(control, storage, assignment_id, what):
            answer = honest(control, storage, assignment_id, what)
            admitted.append(workspaces._admitted_removal(
                control, assignment_id, "review competing removal",
                workspaces._pinned_home(storage, assignment_id)))
            return answer

        with mock.patch.object(workspaces, "refuse_if_held", side_effect=checked):
            with self.assertRaises(ContractRefusal):
                workspaces.adopted_assignment_workspace(
                    self.storage, "assignment-1", control=self.store)
        self.assertEqual(len(admitted), 1)


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([AdoptionAdmission("test_adoption_cannot_finish_after_removal_admitted")])
