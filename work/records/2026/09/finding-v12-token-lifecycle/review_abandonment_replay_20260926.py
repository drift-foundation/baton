"""Independent W275774: committed abandonment must retry its failed token return."""
import unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts, intake, tokens
from tests.manager.test_intake import ATTEMPT, RETENTION, TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence as Fixture

class AbandonmentReplay(unittest.TestCase):
    def test_committed_abandonment_retries_failed_return(self):
        fixture = Fixture()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.addCleanup(fixture.tearDown)
        fixture.running_attempt()
        fixture.fence_for_this_attempt()
        attempts.pin_boundary_identity(fixture.store, attempt_id=ATTEMPT, source=(66, 111), workspace=(66, 4242))
        attempt = fixture.attempt_row()
        governance = tokens.workspace_governance()
        reserved = governance.reserve(fixture.store, attempt, operation=attempts._start_operation_id(attempt))
        reserved.bind(attempt['runtime_id'])()
        reserved.settle(attempt['runtime_id'])
        class FailingReturn:
            def release(self, *args, **kwargs):
                raise ContractRefusal('refused', 'precondition', 'injected token return failure after committed abandonment')
        adapter = fixture.Abandoner()
        def end(govern):
            return intake.abandon_attempt(fixture.store, fixture.port, adapter, attempt_id=ATTEMPT, reason=fixture.REASON, retention_policy_digest=RETENTION, govern=govern)
        with self.assertRaises(ContractRefusal):
            end(FailingReturn())
        domain = tokens.domain_of('workspace', '66:4242')
        self.assertEqual(len(tokens.outstanding(fixture.store, domain)), 1)
        answer = end(governance)
        self.assertEqual(answer['cleanup']['cleanup'], 'retained')
        self.assertEqual(tokens.outstanding(fixture.store, domain), [], 'replayed abandonment skipped the original resource return')

if __name__ == '__main__':
    unittest.main(defaultTest='AbandonmentReplay')
