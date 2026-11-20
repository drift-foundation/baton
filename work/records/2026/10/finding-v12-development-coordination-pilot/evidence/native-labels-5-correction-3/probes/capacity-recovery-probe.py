import json,re,shlex,time
from pathlib import Path
from tests.tools.test_connected_creation import CreateTimeWorkLabelsThroughTheRealCommand as Case
start=time.monotonic();case=Case();case.setUp();out={}
try:
 case.installed(jobs=[],line_declared_base='a'*40,canonical_target_id='target-1')
 wanted=[f'label-{i:02}' for i in range(32)]
 out['initial_binding_interruption']=str(case.stopped(case.labelled(*wanted)))
 case.authority(writable=True).grant_capability('baton.slaw','manage-work-labels')
 def act(verb,labels,op):
  args=[verb,'--participant','baton.slaw','--work',case.work,'--operation-id',op]
  for label in labels:args+=['--label',label]
  code,said=case.work_verb(*args)
  return {'exit':code,'output':said}
 assert act('unlabel-work',['label-00'],'drift-remove')['exit']==0
 assert act('label-work',['extra'],'drift-add')['exit']==0
 refusal=str(case.stopped(case.labelled(*wanted)));out['refusal']=refusal
 commands=re.findall(r'`(baton-v12-stack work [^`]+)`',refusal)
 out['ordered_guidance']=commands
 args=shlex.split(commands[0])[2:]+['--participant','baton.slaw','--operation-id','follow-first']
 code,said=case.work_verb(*args);out['first_suggested_act']={'exit':code,'output':said}
 out['labels_after_refused_restoration']=case.authority().labels_of(case.work)
 # Contrast confirms a valid bounded repair exists without changing intent.
 out['remove_extra_first']=act('unlabel-work',['extra'],'repair-remove')
 out['restore_missing_second']=act('label-work',['label-00'],'repair-add')
 out['restored_labels']=case.authority().labels_of(case.work)
 out['same_request_after_restoration']=str(case.stopped(case.labelled(*wanted)))
 assert code==2
 assert out['restored_labels']==wanted
 assert 'reported no binding' in out['same_request_after_restoration']
finally:case.doCleanups()
out['seconds']=time.monotonic()-start
Path('/home/sl/src/baton/work/scratch/w383217/<packet>/probes/capacity-recovery-results.json (redirected from the reviewer's with_name)').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'seconds':out['seconds'],'guidance':out['ordered_guidance'],'first_act':out['first_suggested_act'],'reversed_order_restores':out['restored_labels']==wanted},indent=2))
