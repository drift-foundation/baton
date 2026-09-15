"""Independent capacity/intake checks; simulated custodian, real disposable owners."""
import json
import unittest

from tests.job_manager.test_managed_integration_capacity import CapacityCase, capacity
from baton_v12.worker_manager.intake import intake_receipt_of
from baton_v12.contracts import ContractRefusal


class IndependentCustody(CapacityCase):
    def test_every_retained_artifact_and_intake_act_matches_its_owner(self):
        store, _, _, _ = self.registered()
        answer = self.prepared(store)
        member = next(row for row in answer['members'] if row['phase'] == 'prepare')
        report = json.loads(member['collected_report'])
        receipt = intake_receipt_of(self._control, 'prepare-attempt-1')
        expected = sorted([{key: artifact[key] for key in ('artifact_id', 'content_digest', 'bytes')}
                           for artifact in receipt['artifacts']], key=lambda row: row['artifact_id'])
        self.assertEqual(report['artifacts'], expected)
        self.assertEqual(report['intake_operation'], receipt['operation'])
        self.assertEqual(report['manifest_digest'], receipt['manifest_digest'])
        self.assertEqual(receipt['assignment'], json.loads(member['assignment']))
        replay = capacity.end_integration_execution(store, self._control,
            execution_attempt_id='prepare-attempt-1', outcome='succeeded', exclusion='runtime-destroyed')
        self.assertEqual(replay, answer)

    def test_missing_intake_refuses_without_ending_then_exact_custody_can_continue(self):
        store, _, _, _ = self.registered()
        self.admit('prepare', 'prepare-attempt-1', 'prepare-offer-1', store)
        self.collected('prepare-attempt-1', collect=False)
        before = capacity.integration_capacity_of(store, self.ORCHESTRATION)
        with self.assertRaises(ContractRefusal):
            capacity.end_integration_execution(store, self._control,
                execution_attempt_id='prepare-attempt-1', outcome='succeeded', exclusion='runtime-destroyed')
        self.assertEqual(capacity.integration_capacity_of(store, self.ORCHESTRATION), before)
        from baton_v12.worker_manager.output import frozen_output_of
        self.taken('prepare-attempt-1', frozen_output_of(self._control, 'prepare-attempt-1'))
        self.destroyed('prepare-attempt-1')
        answer = capacity.end_integration_execution(store, self._control,
            execution_attempt_id='prepare-attempt-1', outcome='succeeded', exclusion='runtime-destroyed')
        member = next(row for row in answer['members'] if row['phase'] == 'prepare')
        self.assertEqual(member['state'], 'ended')
        self.assertEqual(json.loads(member['collected_report'])['custody'], 'accepted')


if __name__ == '__main__':
    unittest.main(verbosity=2)
