# K variant of the reviewer's capacity-recovery-probe.py (review-2026-11-20T01-53-26Z.md), same fixture and
# same drift; records the corrected guidance, the contrast (the adding act alone is refused at capacity),
# then follows the named acts IN THE NAMED ORDER and shows the exact minted set restored and the same
# request back at the fixture's binding boundary (its original interruption; not a submission).
import json,re,shlex,sys,time
from pathlib import Path
from tests.tools.test_connected_creation import CreateTimeWorkLabelsThroughTheRealCommand as Case
start=time.monotonic();case=Case();case.setUp();out={}
try:
 case.installed(jobs=[],line_declared_base='a'*40,canonical_target_id='target-1')
 wanted=[f'label-{i:02}' for i in range(32)]
 out['initial_binding_interruption']=str(case.stopped(case.labelled(*wanted)))
 out['minted_labels_count']=len(case.authority().labels_of(case.work))
 case.authority(writable=True).grant_capability('baton.slaw','manage-work-labels')
 def act(verb,labels,op):
  args=[verb,'--participant','baton.slaw','--work',case.work,'--operation-id',op]
  for label in labels:args+=['--label',label]
  code,said=case.work_verb(*args)
  return {'exit':code,'output_labels':(json.loads(said)['labels'] if code==0 else None)}
 assert act('unlabel-work',['label-00'],'drift-remove')['exit']==0
 assert act('label-work',['extra'],'drift-add')['exit']==0
 out['drifted_labels_count']=len(case.authority().labels_of(case.work))
 refusal=str(case.stopped(case.labelled(*wanted)));out['refusal']=refusal
 commands=re.findall(r'`(baton-v12-stack work [^`]+)`',refusal)
 out['ordered_guidance']=commands
 out['no_label_retry_collides']=str(case.stopped(case.argv()))
 # CONTRAST: the adding act alone -- what M385307 named first -- is refused at capacity and changes nothing.
 adding=[c for c in commands if ' label-work ' in c][0]
 code,said=case.work_verb(*(shlex.split(adding)[2:]+['--participant','baton.slaw','--operation-id','adding-first']))
 out['adding_act_alone_at_capacity']={'exit':code,'output':said}
 out['labels_unchanged_after_refused_addition']=case.authority().labels_of(case.work)==sorted(wanted[1:]+['extra'])
 # FOLLOWING THE NAMED ACTS, AS NAMED, IN ORDER.
 out['followed']=[]
 for i,command in enumerate(commands):
  code,said=case.work_verb(*(shlex.split(command)[2:]+['--participant','baton.slaw','--operation-id',f'follow-{i}']))
  out['followed'].append({'command':command,'exit':code,'labels_after':case.authority().labels_of(case.work)})
 out['restored_labels']=case.authority().labels_of(case.work)
 out['same_request_after_restoration']=str(case.stopped(case.labelled(*wanted)))
 out['submitted']=case.submitted('job-cli-first')
 out['label_events']=len(case.authority().work_label_events(case.work))
 assert commands[0].startswith('baton-v12-stack work unlabel-work ') and commands[1].startswith('baton-v12-stack work label-work ')
 assert out['adding_act_alone_at_capacity']['exit']==2 and out['labels_unchanged_after_refused_addition']
 assert all(f['exit']==0 for f in out['followed'])
 assert out['restored_labels']==wanted
 assert 'reported no binding' in out['same_request_after_restoration'] and 'minted the Work' not in out['same_request_after_restoration']
 assert out['submitted']==[]
 out['verdict']='named order followed at capacity; exact minted set restored; same request back at the binding boundary; no submission'
finally:case.doCleanups()
out['seconds']=time.monotonic()-start
Path(sys.argv[1]).write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'seconds':out['seconds'],'guidance':out['ordered_guidance'],'adding_first':out['adding_act_alone_at_capacity']['exit'],'followed':[(f['command'].split()[2],f['exit']) for f in out['followed']],'restored':out['restored_labels']==wanted,'verdict':out.get('verdict')},indent=2))
