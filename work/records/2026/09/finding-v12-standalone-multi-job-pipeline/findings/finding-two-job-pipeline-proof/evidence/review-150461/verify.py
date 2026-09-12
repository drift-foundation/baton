from pathlib import Path
from datetime import datetime,timedelta
import hashlib,importlib.util,json,stat,time
repo=Path('/home/sl/src/baton');p=repo/"work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof"
source=p/'evidence/run9-budget-150384';out=p/'evidence/review-150461'
start=time.monotonic()
spec=importlib.util.spec_from_file_location('retained_reader',source/'reconcile.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def raw(f,limit=16*1024*1024):return mod.read(f,limit)
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def doc(f):return json.loads(raw(f))
m=source/'candidate-manifest.json'
assert sha(raw(m))=='sha256:ffdedc1de2a95502350f20147a6e3013627d0fe4a8b8da8dc69912637f915c19'
files=doc(m)['files'];assert len(files)==19
for n,v in files.items():
 rel=Path(n);assert not rel.is_absolute() and '..' not in rel.parts and str(rel).startswith(str(p.relative_to(repo))+'/')
 b=raw(repo/rel);s=(repo/rel).lstat()
 assert sha(b)==v['sha256'] and len(b)==v['bytes'] and stat.S_ISREG(s.st_mode),n
bindings=doc(source/'source-bindings.json')
for n,v in bindings.items():
 f=Path(n);assert str(f).startswith('/home/sl/.local/state/baton/v12/w71879-run9/')
 assert f.suffix not in ('.sqlite3','.db','.sqlite') and 'credentials' not in f.parts
 b=raw(f);assert sha(b)==v['sha256'] and len(b)==v['bytes'],n
run=Path('/home/sl/.local/state/baton/v12/w71879-run9')
samples=[json.loads(l) for l in raw(run/'evidence/samples.jsonl').splitlines()]
assert len(samples)==154
states=lambda s:{x['stage_id']:x['state'] for j in s['status']['jobs'] for x in j['stages']}
assert states(samples[116])['job-a/integration']=='completed'
assert states(samples[-1])['job-b/integration']=='claimed'
claims=doc(source/'authority-assignments.json')
subject=doc(source/'subject.json')
assert doc(source/'verification-subject.json')==dict(subject,kind='verification')
report_bindings={}
for kind in ('review','approval'):
 sealed=doc(source/(kind+'-sealed.json'));report_bytes=raw(source/(kind+'-report.json'));report=json.loads(report_bytes)
 claim=claims[kind]['events'][0];ending=claims[kind]['events'][-1]
 assert sealed['assignment_ref']==claim['assignment_ref']==ending['assignment_ref'] and ending['cause']=='pass'
 assert claims[kind]['current'] is None and sealed['disposition']=='completed' and report['verdict']=='accepted'
 findings=next(x for x in sealed['outputs'] if x['name']=='findings')
 entry=next(x for x in findings['content_manifest']['entries'] if x['path']=='report.json')
 assert sha(report_bytes)==entry['content_digest'] and len(report_bytes)==entry['bytes']
 assert findings['result_metadata']['baton.checkpoint-review/1']=={'base':subject['source_base'],'head':subject['candidate'],'tree':subject['tree'],'verdict':'accepted'}
 report_bindings[kind]={'sha256':sha(report_bytes),'pass_at':ending['at'],'frozen_at':sealed['manager_observed_at']}
events=[doc(source/('verification-'+n+'.json')) for n in ('receipt','state-describe','state-work')]
for ev in events:assert ev['attempt_id']==events[0]['attempt_id'] and ev['sequence_id']==events[0]['sequence_id'] and ev['command_digest']==events[0]['command_digest']
assert events[-1]['state']=='dispatched'
attempt=events[0]['attempt_id']
assert not (run/'launch/verification'/attempt/'events/terminal.json').exists()
assert not (run/'storage'/attempt/'custody'/attempt/'sealed.json').exists()
assert not [f for f in (run/'storage'/attempt/'workspace').rglob('*') if not f.is_dir()]
def stamp(t):return datetime.fromisoformat(t.replace('Z','+00:00'))
bstart=stamp(claims['b']['events'][-1]['at']);vstart=stamp(claims['verification']['events'][0]['at']);deadline=bstart+timedelta(seconds=120)
assert (deadline-vstart).total_seconds()==119.842
assert (vstart+timedelta(seconds=180)-deadline).total_seconds()==60.158
assert (stamp(claims['review']['events'][-1]['at'])-deadline).total_seconds()==0.006
result=doc(source/'run-result.json');assert result['wall_seconds']==408.2074813900108 and result['terminal_both'] is False
stopped=result['exceptional_stops'][0]['argv'][-1]
containers=doc(source/'retained-containers.json');v=next(c for c in containers if c['id']==stopped)
assert not any(c['state']['Running'] for c in containers)
assert v['state']['ExitCode']==137 and v['state']['OOMKilled'] is False
old=doc(p/'evidence/run9-freeze-150125/candidate-manifest.json')['files']
for n,val in old.items():assert sha(raw(repo/n))==val['sha256'],n
markers={'selected-images.json':'d0da4684accfa0cba16dc712d2456745de56ef3632f315a7c17a6649407a8f5f','execution-review.json':'a91d806c71c07e344698569dd44522f80775c888ac2d28606dc519ef448beeb9'}
for n,h in markers.items():assert sha(raw(p/'prepared-150007'/n))=='sha256:'+h
report={'claim':150461,'candidate_files':19,'retained_source_files':len(bindings),'samples':154,'a_completed_sample':117,'last_sample_seconds':samples[-1]['wall_seconds'],'review_reports':report_bindings,'verification_age_at_old_deadline':119.842,'verification_remaining':60.158,'review_pass_after_old_deadline':0.006,'proposed_nonjudge_charge':(vstart-bstart).total_seconds(),'historical_terminal_both':False,'coordinator_current_state':'unverified; public opener refusal recorded by tuner; not bypassed or repeated','old_candidate_bindings':len(old),'old_markers':2,'seconds':time.monotonic()-start}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
cost={'current_listed_seconds':report['seconds'],'cumulative_listed_preparation_seconds':50.18569579989499+report['seconds'],'nine_failed_runtime_walls_seconds':2002.0388815780316,'uncertainty':'Untimed review/CLI/static reads and prior failed-utility/operator/billing/rounding costs remain additional; no model run or implementation test.'}
(out/'spending.json').write_text(json.dumps(cost,indent=2)+'\n')
print(json.dumps({'verification':report,'spending':cost},indent=2))
