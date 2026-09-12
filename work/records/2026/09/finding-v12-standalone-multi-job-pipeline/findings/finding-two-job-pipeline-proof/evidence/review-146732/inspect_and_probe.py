"""Read-only retained-run measurements and disposable Git status witness probe.
No production store, credentials, runtime, Git history or index is mutated.
Only Git status is executed in disposable copied fixture repositories.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, shutil, stat, struct, subprocess, sys, tempfile, time
START=time.monotonic()
ROOT=Path('/home/sl/src/baton')
RUN=Path('/home/sl/.local/state/baton/v12/w71879-run5')
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'v12/worker'))
import integration_workload as workload
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def metadata(p):
 s=p.lstat()
 return {'inode':s.st_ino,'size':s.st_size,'mode':oct(stat.S_IMODE(s.st_mode)),'mtime_ns':s.st_mtime_ns,'mtime':datetime.fromtimestamp(s.st_mtime,timezone.utc).isoformat(),'sha256':sha(p) if stat.S_ISREG(s.st_mode) else None}
def git(p,*args,optional=False):
 argv=['git']+([] if optional else ['--no-optional-locks'])+['-c','safe.directory='+str(p),'-C',str(p),*args]
 done=subprocess.run(argv,capture_output=True,text=True,timeout=10)
 assert done.returncode==0,done.stderr
 return done.stdout
def index(p):
 data=p.read_bytes();sig,version,count=struct.unpack('>4sII',data[:12]);assert sig==b'DIRC' and version in (2,3)
 pos=12;entries=[]
 for _ in range(count):
  start=pos;values=struct.unpack('>10I',data[pos:pos+40]);oid=data[pos+40:pos+60].hex();flags=struct.unpack('>H',data[pos+60:pos+62])[0];pos+=62
  assert not flags&0x4000
  end=data.index(b'\0',pos);name=data[pos:end].decode();pos=start+((end+1-start+7)//8)*8
  entries.append({'path':name,'stat':dict(zip(('ctime_s','ctime_ns','mtime_s','mtime_ns','dev','ino','mode','uid','gid','size'),values)),'oid':oid,'flags':flags})
 return {'version':version,'entries':entries,'sha256':sha(p)}
before={n:metadata(RUN/'target'/n) for n in ('.git','.git/index','.git/HEAD','.git/refs/heads/main')}
actual_index=index(RUN/'target/.git/index');source_index=index(RUN/'source/.git/index')
assert [(x['path'],x['oid'],x['flags'],x['stat']['mode']) for x in actual_index['entries']]==[(x['path'],x['oid'],x['flags'],x['stat']['mode']) for x in source_index['entries']]
attempt='attempt-c81b70054cccc2c87fba1e2ca30cb0318174f3fc54a507f2189f211e65697d73'
bundle=RUN/'state/integration-bundles'/attempt
envelope=read(bundle/'integration.json')
targets=[]
for row in envelope['paths']:
 p=RUN/'target'/row['path'];targets.append({'path':row['path'],'metadata':metadata(p),'candidate_matches':sha(p)==row['candidate']['blob']})
result=read(RUN/'state/integration/integration/result/result.json')
samples=[json.loads(x) for x in (RUN/'evidence/samples.jsonl').read_text().splitlines()]
retained=Path(tempfile.mkdtemp(prefix='w71879-146732-index-probe-'))
(retained/'FIXTURE-ONLY.txt').write_text('Disposable copy for read-command index refresh comparison; not real integration evidence.\n')
probes=[]
for label,optional in [('optional-locks-disabled',False),('ordinary-status',True)]:
 fixture=retained/label
 shutil.copytree(RUN/'source',fixture)
 holder=os.open(fixture,os.O_RDONLY|os.O_DIRECTORY)
 try:
  first=workload._repository_witness(holder)
  tree_before=git(fixture,'write-tree') if False else None
  staged_before=git(fixture,'ls-files','--stage')
  index_before=metadata(fixture/'.git/index')
  answer=git(fixture,'status','--porcelain=v1',optional=optional)
  second=workload._repository_witness(holder)
  staged_after=git(fixture,'ls-files','--stage')
  probes.append({'label':label,'status':answer,'before':first,'after':second,'witness_changed':first!=second,'index_before':index_before,'index_after':metadata(fixture/'.git/index'),'staged_entries_unchanged':staged_before==staged_after})
 finally: os.close(holder)
assert probes[0]['witness_changed'] is False and probes[1]['witness_changed'] is True
assert all(x['staged_entries_unchanged'] and x['status']=='' for x in probes)
assert before=={n:metadata(RUN/'target'/n) for n in before}
observed={'timestamp':datetime.now(timezone.utc).isoformat(),'metadata':before,'actual_index':actual_index,'source_index':source_index,'same_staged_entries':True,'target_files':targets,'source_revision':git(RUN/'source','rev-parse','HEAD','HEAD^{tree}'),'target_revision':git(RUN/'target','rev-parse','HEAD','HEAD^{tree}'),'target_status':git(RUN/'target','status','--porcelain=v1'),'cached_diff':git(RUN/'target','diff','--cached','--stat'),'integration_result':result,'run_result':read(RUN/'evidence/run-result.json'),'sample_count':len(samples),'last_claims':samples[-1]['claims'],'probes':probes,'temporary_fixture':str(retained),'seconds':time.monotonic()-START,'writer_attribution':'Unobserved exact PID/command. Provider-side Git refresh inferred from timing and stat-cache update; this fixture proves the mechanism only.'}
(OUT/'result.json').write_text(json.dumps(observed,indent=2)+'\n')
print(json.dumps({'metadata':before,'target_files':targets,'integration_result':result,'probes':probes,'temporary_fixture':str(retained),'seconds':observed['seconds']},indent=2))
