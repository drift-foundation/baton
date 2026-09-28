"""A known container ID is not proof its running generation ceased."""
import unittest
from tests.manager import test_maintenance as fixture
from baton_v12.worker_manager import workspaces, tokens
from baton_v12.contracts import ContractRefusal

class UnprovedTransfer(unittest.TestCase):
    def test_live_bound_container_cannot_be_declared_stopped_by_caller(self):
        case = fixture.TheORDINARYEndingCompletesWithNoHelperOrItHolds()
        case.setUp()
        self.addCleanup(case.doCleanups)
        held = case.pinned_attempt()
        domain = tokens.domain_of("workspace", tokens.workspace_identity(held))
        token = tokens.acquire(case.case.store, domain, operation="review-live-start", execution=case.intake.ATTEMPT, attempt=case.intake.ATTEMPT)
        tokens.journal_launch(case.case.store, token, token["operation"])
        tokens.bind_container(case.case.store, token, held["runtime_id"], launch=token["operation"])
        # No destroy, observation, writer listing or committed cessation occurred.
        with self.assertRaises(ContractRefusal):
            workspaces.admit_cleanup(case.case.store, case.intake.ATTEMPT,
                {"operation":"review-forged-cleanup", "signature":"probe", "incarnation":case.case.store.incarnation},
                "cleanup without cessation evidence", cessation={"container":held["runtime_id"], "stopped":True, "helpers":[]})

if __name__ == "__main__":
    unittest.main()
