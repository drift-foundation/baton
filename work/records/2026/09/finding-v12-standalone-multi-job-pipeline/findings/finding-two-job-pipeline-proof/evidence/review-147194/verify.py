"""Independent custody checks and retained public-evidence replay; no live stores."""
from pathlib import Path
import hashlib,json,stat,time,sys,shutil,difflib
ROOT=Path('/home/sl/src/baton')
PROOF=ROOT/'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
PREP=PROOF/'prepared-147109'
OUT=Path(__file__).resolve().parent
START=time.monotonic()
def read(p): return json.loads(p.read_text())
def sha(p): return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
def checked(p,value): assert sha(p)==('sha256:'+value.removeprefix('sha256:')),str(p)
def manifest(p,value):
 checked(p,value)
 files=read(p)['files']
 for name,row in files.items():
  target=ROOT/name
  assert target.is_file() and not target.is_symlink(),name
  checked(target,row['sha256'])
  assert target.stat().st_size==row['bytes'],name
  assert oct(stat.S_IMODE(target.stat().st_mode))==row['mode'],name
 return len(files)
counts={'candidate':manifest(PREP/'candidate-manifest.json','94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2'),
'preparation':manifest(PROOF/'prepared-146897/candidate-manifest.json','d24b5349ed6a6e35b37fbc933eaa2550fea7233d2483123ba5ad985f3d1f7c37'),
'freeze':manifest(PROOF/'evidence/run6-freeze-146988/candidate-manifest.json','87a320bdee36cfdca8e7d18372e65ff26eeb314eeda948db3402692b328dd0a9')}
prov=read(PREP/'evidence/provenance.json')
for name,row in prov['provider_chain'].items():
 if row.get('expected_absence_matches'): assert not (ROOT/name).exists()
 else: checked(ROOT/name,row['sha256'])
for key in ('source_requirements','current_observation_sources','new_read_dependencies'):
 for name,value in prov[key].items(): checked(ROOT/name,value)
for name in prov['unchanged_dependencies']:
 assert (PREP/name).read_bytes()==(PROOF/'prepared-146897'/name).read_bytes(),name
delta=''
for name in prov['changed_dependencies']:
 old=PROOF/'prepared-146897'/name;new=PREP/name
 delta+=''.join(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile=str(old.relative_to(ROOT)),tofile=str(new.relative_to(ROOT))))
assert delta==(PREP/'evidence/correction-delta.patch').read_text()
(OUT/'independent-delta.patch').write_text(delta)
facts=read(PREP/'evidence/run6-status-facts.json')
samples=Path(facts['source']);assert samples==Path('/home/sl/.local/state/baton/v12/w71879-run6/evidence/samples.jsonl')
checked(samples,facts['sha256'])
rows=[json.loads(line) for line in samples.read_text().splitlines()]
assert len(rows)==len(facts['samples'])
def subset(expected,actual):
 if isinstance(expected,dict):
  assert isinstance(actual,dict)
  for key,value in expected.items(): subset(value,actual[key])
 elif isinstance(expected,list):
  assert isinstance(actual,list) and len(expected)==len(actual)
  for a,b in zip(expected,actual): subset(a,b)
 else: assert expected==actual
for expected,actual in zip(facts['samples'],rows):
 assert expected['wall_seconds']==actual['wall_seconds']
 subset(expected['status'],actual['status'])
run=Path('/home/sl/.local/state/baton/v12/w71879-run6')
checked(run/'evidence/run-result.json',prov['run6_result_sha256'])
assert (run/'evidence/run-result.json').read_bytes()==(PREP/'evidence/run6-original-result.json').read_bytes()
sys.path[:0]=[str(PREP),str(ROOT/'v12/python/src')]
from failure_observation import first_failure,provider_diagnostic
works={'a':'c71879b0-W1','b':'c71879b0-W2'};observations=[]
for job in ('job-a','job-b'):
 for index,row in enumerate(rows,1):
  status=row['status']
  if status is None: continue
  status=dict(status,jobs=[j for j in status['jobs'] if j['job_id']==job])
  failed=first_failure(status,authority_uuid='c71879b0000000000000000000000001',incarnation='w71879-run6',works=works)
  if failed:
   diagnostic=provider_diagnostic(failed,run_root=run,incarnation='w71879-run6')
   observations.append({'sample':index,'wall_seconds':row['wall_seconds'],'failure':failed,'diagnostic':diagnostic})
   break
assert [r['sample'] for r in observations]==[5,21]
assert observations==read(PREP/'evidence/run6-diagnostic-replay.json')['observations']
for row in observations:
 assert row['diagnostic']['provider_reason']=='api-error' and row['diagnostic']['authentication_cause']=='unknown'
suite=Path('/tmp/w71879-146897-offline-verification-4uffvq0l')
for name in ('verification.txt','verification.json'): shutil.copyfile(suite/name,OUT/name)
report={'counts':counts,'provider_entries':len(prov['provider_chain']),'unchanged_dependencies':len(prov['unchanged_dependencies']),'status_source_hash':sha(samples),'status_samples':len(rows),'observations':observations,'suite':read(suite/'verification.json'),'seconds':time.monotonic()-START,'scope':'Read-only published status/report replay and ordinary file custody; no runtime, credential stream, store or repair.'}
(OUT/'verification-and-replay.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'counts':counts,'samples':len(rows),'detections':[{'sample':r['sample'],'wall_seconds':r['wall_seconds'],'stage':r['failure']['stage_id'],'reason':r['diagnostic']['provider_reason']} for r in observations],'seconds':report['seconds']},indent=2))

