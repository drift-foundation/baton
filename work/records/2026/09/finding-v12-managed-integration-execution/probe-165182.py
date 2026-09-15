"""Independent corrected admission cases and content replay observation.

All database writes are in disposable test fixtures, never the Baton ledger.
"""
import json
import unittest
from unittest import mock
from tests.job_manager import test_managed_integration_capacity as supplied
from baton_v12.integration import refuse_entry
from baton_v12.contracts import ContractRefusal

class Observations(supplied.CapacityCase):
    def ready(self):
        store,stage,_,_=self.registered();self.prepared(store);self.coordinated()
        return store,stage
    def test_release_during_authorization_refuses_and_keeps_planned(self):
        store,stage=self.ready()
        real=self.authorization.authorized
        def authorize(operands):
            answer=real(operands)
            refuse_entry(self.coordinated(),**self.grant,
                         settlement={'reason':'policy','detail':{'why':'independent release during authorization'}})
            return answer
        with mock.patch.object(self.authorization,'authorized',side_effect=authorize):
            with self.assertRaises(ContractRefusal):self.applying(store,stage)
        result=supplied.capacity.integration_capacity_of(store,self.ORCHESTRATION)
        self.assertEqual(next(x for x in result['members'] if x['phase']=='apply')['state'],'planned')
    def test_candidate_binding_collision_and_exact_replay_after_release(self):
        store,stage=self.ready()
        first=self.applying(store,stage)
        operation=store.operation_record('integration-capacity.admit:'+stage['attempt_id'])
        self.assertIn('derived-proposal-1',operation['signature'])
        self.assertIn('derived-result-1',operation['signature'])
        refuse_entry(self.coordinated(),**self.grant,
                     settlement={'reason':'policy','detail':{'why':'after completed admission'}})
        self.assertEqual(self.applying(store,stage),first)
        self.authorization.answer.update(derived_proposal_id='another-proposal',derived_result_id='another-result',derived_result_digest='sha256:'+'f'*64)
        with self.assertRaises(ContractRefusal) as caught:self.applying(store,stage)
        self.assertEqual(caught.exception.code,'operation-collision')
    def test_new_content_authorization_collides_with_old_admission(self):
        """Changed content fault must collide rather than return historical admission.

        Mirrors the supplied preparation-content transition fixture, scheduling
        it before retry instead of during the first authorization callback.
        """
        store,stage=self.ready()
        first=self.applying(store,stage)
        old=next(x for x in first['members'] if x['phase']=='apply')['parent_content_digest']
        changed='sha256:'+'7'*64
        self.assertNotEqual(changed,old)
        store._connection.execute('UPDATE integration_capacity_members SET collected_digest = ? WHERE phase = ?', (changed,'prepare'))
        with self.assertRaises(ContractRefusal) as caught:self.applying(store,stage)
        self.assertEqual(caught.exception.code,'operation-collision')
        self.assertEqual(self.authorization.asked[-1]['content_digest'],changed)
        operation=store.operation_record('integration-capacity.admit:'+stage['attempt_id'])
        self.assertIn(old,operation['signature'])
        self.assertNotIn(changed,operation['signature'])
        print('VERIFIED: changed-content retry collides; original content remains signed')

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(supplied)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Observations))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
