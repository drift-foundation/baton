"""Synthetic Authority contract probe; no native Job or real human approval claimed."""
import json
from tests.tools.test_disposition_command import Fixture, OWNER, WORK
case=Fixture()
case.setUp()
try:
    case.publish()
    assert all(case.receipt(k) is None for k in ('verification','review','approval','integration'))
    initial=case.approve()
    assert initial[0]==2
    case.verified()
    after_verify=case.approve()
    assert after_verify[0]==2
    case.reviewed()
    case.ended()
    assert case.receipt('approval') is None
    pending=case.run_verb('pending',*case.base(),'--work',WORK,'--participant',OWNER)
    assert pending[0]==0
    assert json.loads(pending[1])['owner_action']=='approval-due'
    withheld=case.integrated()
    assert withheld[0]==2
    assert case.receipt('approval') is None
    approved=case.approve()
    assert approved[0]==0,approved
    receipt=case.receipt('approval')
    assert receipt['actor']==OWNER
    replay=case.approve()
    assert replay[0]==0
    assert case.receipt('approval')==receipt
    print(json.dumps({'label':'Synthetic published candidate and explicit simulated reviewer/owner acts through public sessions and installed command. Not joined native evidence or real owner approval.','initial_approve_exit':initial[0],'verify_only_approve_exit':after_verify[0],'after_independent_review_action':json.loads(pending[1])['owner_action'],'withheld_integration_exit':withheld[0],'explicit_owner_approve_exit':approved[0],'approval_actor':receipt['actor'],'replay_exit':replay[0],'replay_unchanged':True},indent=2))
finally:
    case.doCleanups()
