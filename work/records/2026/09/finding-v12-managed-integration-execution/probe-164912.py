"""Independent remaining recovery and coherent-read observations, disposable fixtures."""
import unittest,os
from unittest import mock
from tests.tools import test_managed_integration as supplied
from tests.integration import test_managed_storage as storage
from baton_v12.integration import IntegrationStore
from baton_v12.integration import reconciliation as owner
from baton_v12.contracts import ContractRefusal
import integration_placement as placement
class Observations(supplied.PlacementCase):
    def ready(self):self.custody();self.stopped()
    def test_intended_after_real_swap_and_return_to_base_advances_again(self):
        self.ready()
        with mock.patch.object(placement,'record_publication_effect',side_effect=RuntimeError('after actual swap before marker')):
            with self.assertRaises(RuntimeError):self.publish()
        self.assertEqual(self.standing(),self.candidate)
        self.assertEqual(owner.publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')['state'],'intended')
        self.profile.advance(self.repository,reference=self.reference,imported=self.base,reviewed=self.candidate)
        real=self.profile.advance
        with mock.patch.object(self.profile,'advance',wraps=real) as spy:
            self.assertEqual(self.publish()['outcome'],'published')
            self.assertEqual(spy.call_count,1)
    def test_concurrent_committed_transition_produces_false_integrity_refusal(self):
        self.ready()
        with mock.patch.object(self.profile,'advance',side_effect=RuntimeError('before CAS')):
            with self.assertRaises(RuntimeError):self.publish()
        row=owner.publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')
        self.profile.advance(self.repository,reference=self.reference,imported=self.candidate,reviewed=self.base)
        other=IntegrationStore.open(os.path.join(self.node_root,'coordinator.sqlite3'),incarnation='placement-1',clock=lambda:supplied.coordinator_fixtures.NOW)
        self.addCleanup(other.close)
        real=owner._committed_act
        fired=[]
        def interleave(store,operation_id,signature):
            answer=real(store,operation_id,signature)
            if store is self.coordinator and not fired:
                fired.append(True)
                owner.record_publication_effect(other,row['publication_id'],'swapped')
            return answer
        with mock.patch.object(owner,'_committed_act',side_effect=interleave):
            with self.assertRaises(ContractRefusal) as caught:
                owner.publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')
        self.assertIn('behind its own journal',str(caught.exception))
        self.assertEqual(owner.publication_of(self.coordinator,supplied.ORCHESTRATION,'apply')['state'],'swapped')
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(supplied)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(storage))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Observations))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
