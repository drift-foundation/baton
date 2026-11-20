"""Independent R4 proof through bootstrap.main and job_manager.main.
Fixture bundle identity is simulated; no engine/provider/real installation.
"""
import copy, json, unittest
from baton_v12.authority import Authority, messages
from baton_v12.contracts import digest
from baton_v12.job_manager import role_contract, native_handoffs
from tests.tools.test_connected_creation import ConnectedCreationCase

class OperatorConfiguration(ConnectedCreationCase):
    def workers(self):
        workers=[w for w in super().workers() if w['role'] in ('implementation','review')]
        for w in workers:
            m=copy.deepcopy(w['deployment']['input_manifest'])
            prototype=m['outputs'][0]
            m['outputs']=[dict(prototype,name=name,type=kind,path=name,required=False)
                for name,kind in [('proposal','git-change-proposal'),('findings','directory-result'),('logs','directory-result'),('handoff','directory-result'),('response','directory-result')]]
            m.pop('manifest_digest'); m['manifest_digest']=digest(m)
            w['deployment']['input_manifest']=m
        return workers

    def test_fresh_install_then_operator_create_installs_scoped_answer_grant(self):
        routing={'reviewer':'baton.reviewer','decision_recipient':'baton.slaw'}
        self.installed(jobs=[],line_declared_base='a'*40,canonical_target_id='target-1',native_handoff_routing=routing)
        a=Authority.open(self.owned['authority_store'], expected_authority_uuid=self.owned['authority_uuid'])
        try:
            self.assertEqual(a.native_routing()['reviewer'],routing['reviewer'])
        finally:a.dispose()
        held=self.answered(template=role_contract.HANDOFF_TEMPLATE,control_profile='native-handoff/1')
        a=Authority.open(self.owned['authority_store'], expected_authority_uuid=self.owned['authority_uuid'])
        try:
            scope=a.project_work(held['work_id'])['scope']
            self.assertTrue(a.holds_capability(routing['reviewer'],messages.ANSWER_CAPABILITY,scope=scope))
            self.assertFalse(a.holds_capability(routing['reviewer'],'review',scope=scope))
            store,_=self.rows()
            self.assertTrue(native_handoffs.handoff_capable(store,held['job_id']))
            self.assertEqual(self.install_document()['native_handoff_routing'],routing)
            print('OPERATOR_CREATED',json.dumps({'job_id':held['job_id'],'work_id':held['work_id'],'template':held['template'],'scope':scope}))
        finally:a.dispose()

class InvalidDecisionRecipient(OperatorConfiguration):
    def test_invalid_decision_address_is_rejected_before_install(self):
        from tools import bootstrap
        routing={'reviewer':'baton.reviewer','decision_recipient':'not-an-address'}
        # Public install must reject this malformed participant; success followed
        # by a native_routing read refusal proves the bad policy was published.
        self.installed(jobs=[],line_declared_base='a'*40,canonical_target_id='target-1',native_handoff_routing=routing)
        a=Authority.open(self.owned['authority_store'], expected_authority_uuid=self.owned['authority_uuid'])
        try:
            try:
                value=a.native_routing()
            except Exception as error:
                self.fail('operator installation succeeded but persisted unusable routing: '+str(error))
            self.fail('operator installation accepted malformed decision recipient: '+repr(value))
        finally:a.dispose()

if __name__=='__main__':unittest.main(verbosity=2)
