"""Publication regressions and permissive admission defect observations."""
import unittest
from unittest import mock
from tests.tools import test_managed_integration as supplied
from baton_v12.integration import refuse_entry
from baton_v12.integration.queue import entries_of
from baton_v12.contracts import ContractRefusal
class Observations(supplied.PlacementCase):
    def ready(self):self.custody();self.stopped()
    def test_final_target_read_release_prevents_apply(self):
        self.ready()
        real=self.profile.revision;reads=[]
        def revision(*args,**kwargs):
            result=real(*args,**kwargs);reads.append(result)
            if len(reads)==2:
                refuse_entry(self.coordinator,lease_id='lease-1',canonical_target_id=supplied.coordinator_fixtures.TARGET,
                             entry_id='entry-1',fence=self.fence,settlement={'reason':'policy','detail':{'why':'released during final target read'}})
            return result
        with mock.patch.object(self.profile,'revision',side_effect=revision):
            with self.assertRaises(ContractRefusal):self.publish()
        self.assertEqual(self.standing(),self.base)
        self.assertEqual(len(self.target_owner.asked),0)
    def test_fresh_receipt_drift_refuses_settlement(self):
        self.ready()
        real=self.target_owner.apply
        def apply(request):
            answer=real(request)
            self.profile.advance(self.repository,reference=self.reference,imported=self.base,reviewed=self.candidate)
            return answer
        with mock.patch.object(self.target_owner,'apply',side_effect=apply):
            with self.assertRaises(ContractRefusal):self.publish()
        self.assertEqual(self.standing(),self.base)
        self.assertNotEqual(entries_of(self.coordinator,supplied.coordinator_fixtures.TARGET)[0]['state'],'integrated')

from tests.job_manager import test_managed_integration_capacity as capacity_tests
class AdmissionObservations(capacity_tests.CapacityCase):
    """Permissive defect observations, not required behavior."""
    def ready(self):
        store,stage,_,_=self.registered();self.prepared(store);self.coordinated()
        return store,stage
    def test_authorization_release_still_admits(self):
        store,stage=self.ready()
        real=self.authorization.authorized
        def authorize(operands):
            answer=real(operands)
            refuse_entry(self.coordinated(), **self.grant,
                         settlement={'reason':'policy','detail':{'why':'released during authorization'}})
            return answer
        with mock.patch.object(self.authorization,'authorized',side_effect=authorize):
            result=self.applying(store,stage)
        self.assertEqual(next(x for x in result['members'] if x['phase']=='apply')['state'],'admitted')
        from baton_v12.integration.queue import live_grant
        with self.assertRaises(ContractRefusal):live_grant(self.coordinated(),**self.grant)
    def test_candidate_change_replays_without_authorization_binding(self):
        store,stage=self.ready()
        first=self.applying(store,stage)
        asked=len(self.authorization.asked)
        self.authorization.answer.update(derived_proposal_id='other-approved-proposal',
                                          derived_result_id='other-approved-result',
                                          derived_result_digest='sha256:'+'f'*64)
        self.assertEqual(self.applying(store,stage),first)
        self.assertEqual(len(self.authorization.asked),asked)
        operation=store.operation_record('integration-capacity.admit:'+stage['attempt_id'])
        self.assertNotIn('derived-proposal-1',operation['signature'])
        self.assertNotIn('authorization',operation['signature'])
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(supplied)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(capacity_tests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Observations))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(AdmissionObservations))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
