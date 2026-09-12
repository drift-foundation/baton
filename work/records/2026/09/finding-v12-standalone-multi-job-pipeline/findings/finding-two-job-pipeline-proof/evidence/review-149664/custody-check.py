from pathlib import Path
import hashlib,json,stat,time
repo=Path('/home/sl/src/baton')
p=repo/"work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof"
out=p/'evidence/review-149664'
out.mkdir(exist_ok=False)
start=time.monotonic()
def sha(f):return 'sha256:'+hashlib.sha256(f.read_bytes()).hexdigest()
m=p/'evidence/run8-freeze-149637/candidate-manifest.json'
assert sha(m)=='sha256:81747c62cd9863f9c0899e1292d80fc82b1757501caa7628e6286b933ba1dd81'
files=json.loads(m.read_text())['files']
assert len(files)==989
for name,v in files.items():
 rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts
 assert name.startswith(str(p.relative_to(repo))+'/') or name in ('v12/worker/claude_agent.py','v12/python/tests/manager/test_claude_agent.py')
 assert rel.suffix not in ('.db','.sqlite','.sqlite3') and 'credentials' not in rel.parts
 f=repo/rel;s=f.lstat()
 assert stat.S_ISREG(s.st_mode) and sha(f)==v['sha256'] and s.st_size==v['bytes'] and oct(stat.S_IMODE(s.st_mode))==v['mode'],name
posture={}
target=Path('/home/sl/.local/state/baton/v12/w71879-run8/target')
for name in ('.','demo','tests','demo/greeting.py','demo/units.py','tests/test_greeting.py'):
 s=(target/name).lstat();expected=0o2775 if name in ('.','demo','tests') else 0o644
 assert stat.S_IMODE(s.st_mode)==expected and (stat.S_ISDIR(s.st_mode) if expected==0o2775 else stat.S_ISREG(s.st_mode)),name
 posture[name]={'mode':oct(stat.S_IMODE(s.st_mode)),'projected_uid':s.st_uid,'projected_gid':s.st_gid}
prior=json.loads(Path('/tmp/w71879-review-149664-inputs.json').read_text())
(out/'input-reconstruction.json').write_text(json.dumps(prior,indent=2)+'\n')
report={'claim':149664,'manifest':sha(m),'files':len(files),'posture':posture,'host_ownership_basis':'Owner149607 successful accepted host preparation/validation; managed UID/GID projection is not host ownership evidence.','custody_seconds':time.monotonic()-start}
(out/'custody.json').write_text(json.dumps(report,indent=2)+'\n')
seconds=report['custody_seconds']+prior['verification_seconds']
cost={'current_listed_seconds':seconds,'cumulative_listed_preparation_seconds':42.841878657916915+seconds,'seven_failed_runtime_walls_seconds':1350.217186488022,'uncertainty':'Untimed edits, reads, CLI and host/login/billing uncertainty additional. Prior tests and operator validation not recounted.'}
(out/'spending.json').write_text(json.dumps(cost,indent=2)+'\n')
print(json.dumps({'custody':report,'spending':cost},indent=2))
