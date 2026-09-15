"""Independent target-owner cutpoint checks; disposable fixtures, fake receipts."""
import unittest,os
from unittest import mock
from tests.tools import test_managed_integration as supplied
from tests.integration import test_managed_storage as storage
from baton_v12.integration import IntegrationStore,refuse_entry
from baton_v12.integration import reconciliation as owner
from baton_v12.integration.queue import entries_of
from baton_v12.contracts import ContractRefusal
import integration_placement as placement
class Observations(supplied.PlacementCase):
    def ready(self):self.custody();self.stopped()
    def test_applied_receipt_settles_after_target_moved_back_to_base(self):
        self.ready()
        with mock.patch.object(placement,'record_publication_effect',side_effect=RuntimeError('after owner apply before coordinator marker')):
            with self.assertRaises(RuntimeError):self.publish()
        self.assertEqual(self.standing(),self.candidate)
        self.profile.advance(self.repository,reference=self.reference,imported=self.base,reviewed=self.candidate)
        with mock.patch.object(self.profile,'advance',side_effect=AssertionError('duplicate swap')):
            answer=self.publish()
        self.assertEqual(answer['outcome'],'resumed')
        self.assertEqual(self.standing(),self.base)
        self.assertEqual(entries_of(self.coordinator,supplied.coordinator_fixtures.TARGET)[0]['state'],'integrated')
    def test_grant_lost_during_recover_still_allows_apply(self):
        self.ready()
        with mock.patch.object(self.target_owner,'apply',side_effect=RuntimeError('before apply')):
            with self.assertRaises(RuntimeError):self.publish()
        real=self.target_owner.recover
        def recover(request):
            refuse_entry(self.coordinator,lease_id='lease-1',canonical_target_id=supplied.coordinator_fixtures.TARGET,
                         entry_id='entry-1',fence=self.fence,settlement={'reason':'policy','detail':{'why':'released during recover'}})
            return real(request)
        with mock.patch.object(self.target_owner,'recover',side_effect=recover):
            with self.assertRaises(ContractRefusal):self.publish()
        self.assertEqual(self.standing(),self.candidate)
    def test_concurrent_transition_is_now_read_from_one_snapshot(self):
        self.ready()
        with mock.patch.object(self.target_owner,'apply',side_effect=RuntimeError('before apply')):
            with self.assertRaises(RuntimeError):self.publish()
        row=owner.publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')
        self.profile.advance(self.repository,reference=self.reference,imported=self.candidate,reviewed=self.base)
        other=IntegrationStore.open(os.path.join(self.node_root,'coordinator.sqlite3'),incarnation='placement-1',clock=lambda:supplied.coordinator_fixtures.NOW)
        self.addCleanup(other.close)
        real=owner._committed_act;fired=[]
        def interleave(store,operation_id,signature):
            answer=real(store,operation_id,signature)
            if store is self.coordinator and not fired:
                fired.append(True);owner.record_publication_effect(other,row['publication_id'],'swapped')
            return answer
        with mock.patch.object(owner,'_committed_act',side_effect=interleave):
            answer=owner.publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')
        self.assertEqual(answer['state'],'intended')
        self.assertEqual(owner.publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')['state'],'swapped')
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(supplied)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(storage))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Observations))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
