"""Drive production assignment composition and _input on the candidate; no engine."""
import json,os
from types import SimpleNamespace
from tests.tools.test_job_task_delivery import DeliveryCase,FIRST
from tools import single_worker
from baton_v12.contracts import ContractRefusal
c=DeliveryCase(); c.setUp()
try:
 w=c.worker_serving('implementation',{})
 made=c.composed(FIRST,'Perform the newly requested task.',installed=w.given['task_bytes'])
 w.job_task=lambda *,job_id: made['task_document']
 stage=c.stage_of('implementation',FIRST)
 manifest,task=w._for_job(stage)
 row=dict(w.given['input_manifest']['work_ref'],participant=w.given['participant'],claim_generation=1,claim_principal='principal:review-probe',claim_scope='scope:deployment',claim_role='baton.impl',claim_grant='direct',claim_policy_generation=1,claim_event_seq=1,accepted_at='2026-09-02T00:00:00.000Z',decided_at='2026-09-02T00:00:00.000Z')
 assignment=single_worker._assignment_manifest(w.given,row,stage['attempt_id'],stage['offer_id'])
 root=c.inputs('actual-input'); mountpoint=os.path.join(root,manifest['sources'][0]['destination']); os.makedirs(mountpoint)
 answer={'assignment_input_digest':assignment['input_manifest_digest'],'per_job_input_digest':manifest['manifest_digest']}
 try:
  w._matches(stage,c.job_for(manifest))
  answer['worker_matches']=True
 except ContractRefusal as e:
  answer.update(worker_matches=False,match_code=e.code,match_message=e.message)
 try:
  w._input({'inputs':root},assignment,SimpleNamespace(mountpoint=mountpoint),stage)
  answer['input_succeeded']=True
 except ContractRefusal as e:
  answer.update(input_succeeded=False,code=e.code,message=e.message,task_file_published=os.path.isfile(os.path.join(root,'task.json')))
 print(json.dumps(answer,indent=2))
finally:
 c.doCleanups()
