from pathlib import Path
import hashlib,json,stat,time
repo=Path('/home/sl/src/baton')
p=repo/"work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof"
e=p/'evidence/review-150148'
start=time.monotonic()
def sha(f):return 'sha256:'+hashlib.sha256(f.read_bytes()).hexdigest()
m=p/'evidence/run9-freeze-150125/candidate-manifest.json'
assert sha(m)=='sha256:aa78787caaf0796d303c703bc745e758d46e67dde671a6668d6e95de3b9ac5a2'
files=json.loads(m.read_text())['files'];assert len(files)==198
for n,v in files.items():
 rel=Path(n);assert not rel.is_absolute() and '..' not in rel.parts
 assert n.startswith(str(p.relative_to(repo))+'/') or n in ('v12/python/tools/stage_execution.py','v12/python/tests/tools/test_stage_execution.py')
 assert rel.suffix not in ('.db','.sqlite','.sqlite3') and 'credentials' not in rel.parts
 f=repo/rel;s=f.lstat()
 assert stat.S_ISREG(s.st_mode) and sha(f)==v['sha256'] and s.st_size==v['bytes'] and oct(stat.S_IMODE(s.st_mode))==v['mode'],n
posture={}
for name in ('.','demo','tests','demo/greeting.py','demo/units.py','tests/test_greeting.py'):
 f=Path('/home/sl/.local/state/baton/v12/w71879-run9/target')/name;s=f.lstat()
 expected=0o2775 if name in ('.','demo','tests') else 0o644
 assert stat.S_IMODE(s.st_mode)==expected and (stat.S_ISDIR(s.st_mode) if expected==0o2775 else stat.S_ISREG(s.st_mode)),name
 posture[name]={'mode':oct(stat.S_IMODE(s.st_mode)),'projected_uid':s.st_uid,'projected_gid':s.st_gid}
prior=json.loads(Path('/tmp/w71879-review-150148-inputs.json').read_text())
(e/'input-reconstruction.json').write_text(json.dumps(prior,indent=2)+'\n')
report={'claim':150148,'manifest':sha(m),'verified_files':198,'posture':posture,'ownership_basis':'Owner150121 successful reviewed host helper/validation; projected65534 IDs do not establish real65532:1001.','seconds':time.monotonic()-start}
(e/'custody.json').write_text(json.dumps(report,indent=2)+'\n')
seconds=report['seconds']+prior['verification_seconds']
cost={'current_listed_seconds':seconds,'cumulative_listed_preparation_seconds':49.96827617987374+seconds,'eight_failed_runtime_walls_seconds':1593.8314001880208,'uncertainty':'Untimed review/markers/CLI/host/billing additional; prior tests and operator validation not repeated or recounted.'}
(e/'spending.json').write_text(json.dumps(cost,indent=2)+'\n')
print(json.dumps({'custody':report,'spending':cost},indent=2))
