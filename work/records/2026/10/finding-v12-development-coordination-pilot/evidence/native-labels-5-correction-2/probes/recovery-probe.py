import json,time
from pathlib import Path
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import creation
from tests.job_manager.test_creation import CreationCase,FakeAuthorization,FakeBinding,request,WORK_A,JOB
start=time.monotonic();observed={}
def refusal(case,**kw):
 try:return {'result':case.created(**kw)}
 except ContractRefusal as exc:return {'refusal':str(exc),'code':exc.code,'rows':case.rows()}
case=CreationCase();case.setUp()
try:
 auth=FakeAuthorization(known=False)
 observed['interruption']=refusal(case,authorization=auth,request=request(labels=['v12']),binding=FakeBinding(refusal=ContractRefusal('refused','precondition','binding interrupted')))
 auth.labels=['hot','v12']
 observed['own_work_relabelled']=refusal(case,authorization=auth,request=request(labels=['v12']))
 observed['follow_guidance_without_label']=refusal(case,authorization=auth,request=request())
 auth.labels=['v12']
 observed['restore_exact_set_and_retry']=refusal(case,authorization=auth,request=request(labels=['v12']))
finally:case.doCleanups()
class RacingAuthorization(FakeAuthorization):
 def __init__(self):super().__init__(labels=['v12']);self.reads=0
 def work_of(self,work_id):
  self.reads+=1
  return None if self.reads==1 else super().work_of(work_id)
case=CreationCase();case.setUp()
try:
 auth=RacingAuthorization()
 observed['race_first']=refusal(case,authorization=auth,request=request(labels=['v12']))
 observed['race_retry']=refusal(case,authorization=auth,request=request(labels=['v12']))
 observed['race_follow_guidance_without_label']=refusal(case,authorization=auth,request=request())
finally:case.doCleanups()
case=CreationCase();case.setUp()
try:
 auth=FakeAuthorization(labels=['v12'],minted=f'{creation.CREATE_KIND}.work:{WORK_A}')
 observed['old_identity_labelled']=refusal(case,authorization=auth,request=request(labels=['v12']))
 observed['old_identity_unlabelled']=refusal(case,authorization=auth,request=request())
finally:case.doCleanups()
observed['seconds']=time.monotonic()-start
Path('/home/sl/src/baton/work/scratch/w383217/labels5-correction/probes/recovery-results.json').write_text(json.dumps(observed,indent=2)+'\n')
print(json.dumps({k:v.get('refusal','completed') if isinstance(v,dict) else v for k,v in observed.items()},indent=2))
