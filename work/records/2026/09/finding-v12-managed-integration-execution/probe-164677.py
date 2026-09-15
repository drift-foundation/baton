"""Independent placement observations in disposable local fixtures."""
import unittest
from baton_v12.contracts import ContractRefusal
from baton_v12.integration.queue import refuse_entry, lease_of
from baton_v12.integration.reconciliation import managed_result_of
from baton_v12.worker_manager.attempts import attempt_runtime_of
from tests.tools import test_managed_integration as placement
from tests.integration import test_managed_storage as storage
from tests.integration.test_coordinator import REFUSAL


class Observations(placement.PlacementCase):
    def test_publication_has_no_started_runtime_or_authorized_result(self):
        self.custody()
        self.stopped()
        runtime = attempt_runtime_of(self.store, placement.APPLY)
        self.assertIsNone(runtime['runtime_id'])
        held = managed_result_of(self.coordinator, placement.ORCHESTRATION)
        self.assertEqual(held['state'], 'preparing')
        self.assertIsNone(held['derived_proposal_id'])
        self.assertIsNone(held['evidence'])
        self.publish()
        self.assertEqual(self.standing(), self.candidate)
        print('DEFECT: preparing result publishes without authorized derived proposal, evidence, or attached runtime/start exclusion proof')

    def test_bad_settlement_is_refused_after_target_moves(self):
        self.custody()
        self.stopped()
        with self.assertRaises(ContractRefusal):
            self.publish(settlement={})
        self.assertEqual(self.standing(), self.candidate)
        print('DEFECT: malformed settlement raises after target advanced')

    def test_grant_can_end_during_materialization_before_swap(self):
        self.custody()
        self.stopped()
        original = self.materializer.materialize
        def materialize(operands):
            refuse_entry(self.coordinator, canonical_target_id=placement.coordinator_fixtures.TARGET, entry_id='entry-1', lease_id='lease-1', fence=self.fence, settlement=REFUSAL)
            return original(operands)
        self.materializer.materialize = materialize
        with self.assertRaises(ContractRefusal):
            self.publish()
        self.assertEqual(lease_of(self.coordinator, 'lease-1')['state'], 'released')
        self.assertEqual(self.standing(), self.candidate)
        print('DEFECT: grant ended at materializer boundary, target still advanced before settlement refused')

    def test_exact_successful_publication_cannot_replay(self):
        self.custody()
        self.stopped()
        self.publish()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn('something moved the target underneath it', str(caught.exception))
        self.assertEqual(self.standing(), self.candidate)
        print('DEFECT: exact successful publication retry treats its own prior CAS as foreign target movement')


def load_tests(loader, tests, pattern):
    return unittest.TestSuite([loader.loadTestsFromModule(placement), loader.loadTestsFromModule(storage), tests])


if __name__ == '__main__':
    unittest.main(verbosity=2)
