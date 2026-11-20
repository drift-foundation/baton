import json,re,shlex,time,io
from contextlib import redirect_stderr
from pathlib import Path
from tests.tools.test_connected_creation import CreateTimeWorkLabelsThroughTheRealCommand as Case
start=time.monotonic();observed=[]
for count in (1,2):
 case=Case();case.setUp();out={'replacement_count':count}
 try:
  case.installed(jobs=[],line_declared_base='a'*40,canonical_target_id='target-1')
  wanted=[f'label-{i:02}' for i in range(32)]
  original=str(case.stopped(case.labelled(*wanted)));assert 'reported no binding' in original
  case.authority(writable=True).grant_capability('baton.slaw','manage-work-labels')
  def act(verb,labels,op):
   args=[verb,'--participant','baton.slaw','--work',case.work,'--operation-id',op]
   for label in labels:args+=['--label',label]
   err=io.StringIO()
   with redirect_stderr(err):code,said=case.work_verb(*args)
   return {'exit':code,'stdout':said,'stderr':err.getvalue()}
  extras=[f'extra-{i}' for i in range(count)]
  assert act('unlabel-work',wanted[:count],'drift-remove')['exit']==0
  assert act('label-work',extras,'drift-add')['exit']==0
  drift=case.authority().labels_of(case.work);assert len(drift)==32
  refusal=str(case.stopped(case.labelled(*wanted)));out['refusal']=refusal
  commands=re.findall(r'`(baton-v12-stack work [^`]+)`',refusal);out['commands']=commands
  assert len(commands)==2 and ' work unlabel-work ' in commands[0] and ' work label-work ' in commands[1]
  out['wrong_order_control']=act('label-work',wanted[:count],'wrong-order')
  assert out['wrong_order_control']['exit']==2
  assert 'maximum 32 labels' in out['wrong_order_control']['stderr']
  assert case.authority().labels_of(case.work)==drift
  record=case.authority().work_creation(case.work);out['steps']=[]
  for i,command in enumerate(commands):
   args=shlex.split(command)[2:]+['--participant','baton.slaw','--operation-id',f'follow-{i}']
   code,said=case.work_verb(*args);assert code==0,(command,said)
   out['steps'].append({'command':command,'exit':code,'label_count':len(case.authority().labels_of(case.work))})
  assert case.authority().labels_of(case.work)==wanted
  continued=str(case.stopped(case.labelled(*wanted)));out['continuation']=continued
  assert 'reported no binding' in continued and 'label-work' not in continued
  assert case.authority().work_creation(case.work)==record
  out['changed_intent_refusal']=str(case.stopped(case.argv()))
  assert 'different kind or signature' in out['changed_intent_refusal']
  assert case.submitted('job-cli-first')==[]
  out['submission_count']=0;out['events']=len(case.authority().work_label_events(case.work))
  assert out['events']==32+4*count
  out['exact_set_restored']=True
 finally:case.doCleanups()
 observed.append(out)
result={'seconds':time.monotonic()-start,'scenarios':observed}
Path(__file__).with_name('follow-guidance-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'seconds':result['seconds'],'scenarios':len(observed),'restored':all(x['exact_set_restored'] for x in observed)}))
