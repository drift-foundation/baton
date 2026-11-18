"""Serial bounded verification of immutable accepted source; no repair."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,tempfile,time,uuid
H=Path(__file__).resolve().parent
R=next(p for p in H.parents if (p/'AGENTS.md').exists())
m=json.loads((H/'source-manifest.json').read_text());S=R/m['snapshot']
image=json.loads((H/'build-result.json').read_text())['image']
private='sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4'
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def docker(*args):
 r=subprocess.run(['/usr/bin/docker',*args],capture_output=True,text=True,timeout=30);assert r.returncode==0,r.stderr;return r.stdout.strip()
def hashes():return {p:hashlib.sha256((S/p).read_bytes()).hexdigest() for p in m['files']}
before=hashes();assert all(before[p]==v['sha256'] for p,v in m['files'].items());write(H/'source-before.json',before)
old=docker('ps','-aq','--no-trunc').splitlines();write(H/'containers-before.json',old)
results=[]
for n,selection in enumerate(json.loads((H/'selection.json').read_text()),1):
 out=H/('%02d'%n);out.mkdir();root=Path(tempfile.mkdtemp(prefix='baton-w384944-joined-',dir='/var/tmp'));os.chown(root,-1,1001);os.chmod(root,0o2770)
 nonce=uuid.uuid4().hex;shim=root/'bin';shim.mkdir()
 (shim/'docker').write_text('''#!/usr/bin/python3
import json,os,subprocess,sys,uuid
from pathlib import Path
args=sys.argv[1:];cidfile=None
if args and args[0] in ['build','pull']:
 with open(os.environ['ENGINE_LOG'],'a') as f:f.write(json.dumps({'forbidden_command':args})+'\\n')
 sys.exit(125)
if args and args[0]=='run':
 cidfile=Path(os.environ['TMPDIR'])/('cid-'+uuid.uuid4().hex)
 args[1:1]=['--pull=never','--label',os.environ['TASK_LABEL'],'--cidfile',str(cidfile)]
r=subprocess.run(['/usr/bin/docker',*args],capture_output=True)
record={'command':args[0] if args else '', 'status':r.returncode}
if cidfile and cidfile.exists():
 cid=cidfile.read_text().strip();record['id']=cid;cidfile.unlink()
 info=subprocess.run(['/usr/bin/docker','inspect',cid],capture_output=True)
 if info.returncode==0:
  d=json.loads(info.stdout)[0];record['inspect']={k:d[k] for k in ['Id','Image','State','Mounts']};record['labels']=d['Config']['Labels']
if args and args[0] in ['run','logs','wait','rm']:record.update(stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace'))
with open(os.environ['ENGINE_LOG'],'a') as f:f.write(json.dumps(record)+'\\n')
sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);sys.exit(r.returncode)
''');(shim/'docker').chmod(0o755)
 env=dict(os.environ,PATH=str(shim)+':'+os.environ['PATH'],TMPDIR=str(root),BATON_V12_DISK_ROOT=str(root),BATON_V12_INITIAL_ACCESS_ENGINE='1',BATON_V12_PRIVATE_LINE_IMAGE=private,BATON_V12_WORKSPACE_GROUP='1001',BATON_TEST_ENGINE='docker',PYTHONDONTWRITEBYTECODE='1',W384944_SNAPSHOT=str(S),W384944_LEDGER=str(out/'ledger.json'),ENGINE_LOG=str(out/'engine.jsonl'),TASK_LABEL='baton.w384944.run='+nonce)
 for key in ['INPUT_DELIVERY','WORKER_ENTRY','CUSTODY','LIFECYCLE']:env['BATON_V12_'+key+'_IMAGE']=image
 argv=['/home/sl/.local/state/baton-v12-venv/bin/python',str(H/'audit-tests.py'),selection]
 write(out/'invocation.json',dict(argv=argv,cwd=str(S/'v12'),timeout_seconds=600,cleanup_timeout_seconds=120,environment={k:v for k,v in env.items() if k.startswith(('BATON_','W384944_')) or k in ['TMPDIR','TASK_LABEL','PATH']},root=str(root)))
 start=time.monotonic();timedout=False
 with (out/'tests.log').open('x') as log:
  proc=subprocess.Popen(argv,cwd=S/'v12',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:proc.wait(timeout=600)
  except subprocess.TimeoutExpired:
   timedout=True;os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=10)
 elapsed=time.monotonic()-start
 remaining=docker('ps','-aq','--no-trunc','--filter','label='+env['TASK_LABEL']).splitlines()
 for cid in remaining:
  d=json.loads(docker('inspect',cid))[0];assert d['Config']['Labels'].get('baton.w384944.run')==nonce and d['Image'] in [image,private];docker('rm','--force',cid)
 current=docker('ps','-aq','--no-trunc').splitlines();records=[json.loads(x) for x in (out/'engine.jsonl').read_text().splitlines()] if (out/'engine.jsonl').exists() else []
 created=sorted({x['id'] for x in records if x.get('id')});assert not set(created)&set(current)
 (shim/'docker').unlink();shim.rmdir();leftovers=sorted(str(p.relative_to(root)) for p in root.rglob('*'))
 if not leftovers:root.rmdir()
 after=hashes();drift=[p for p in before if before[p]!=after[p]]
 ledger=json.loads((out/'ledger.json').read_text()) if (out/'ledger.json').exists() else {}
 result=dict(selection=selection,exit=proc.returncode,seconds=elapsed,timed_out=timedout,passed=len(ledger.get('passed',[])),started=len(ledger.get('started',[])),skipped=ledger.get('skipped',[]),created_container_ids=created,emergency_cleanup=remaining,containers_remaining=[],old_containers_preserved=set(old)<=set(current),source_drift=drift,leftovers=leftovers,root_removed=not root.exists())
 result['ok']=proc.returncode==0 and not timedout and not drift and not leftovers and not remaining and result['old_containers_preserved'] and not any('forbidden_command' in x for x in records)
 write(out/'result.json',result);results.append(result);write(H/'results.json',results);print(json.dumps({k:result[k] for k in ['selection','exit','seconds','passed','ok']}),flush=True)
 if not result['ok']:break
write(H/'source-after.json',hashes())
plan=json.loads((H/'build-plan.json').read_text());docker('image','rm',plan['tag'])
collected=json.loads((H/'collected.json').read_text());expected=[i for ids in collected.values() for i in ids];passed=[];started=[];subtests=[]
for n in range(1,len(results)+1):
 p=H/('%02d'%n)/'ledger.json'
 if p.exists():
  ledger=json.loads(p.read_text());passed+=ledger['passed'];started+=ledger['started'];subtests+=ledger['subtests']
summary=dict(commit=m['commit'],expected=len(expected),started=len(started),passed=len(passed),subtests=len(subtests),unrun=sorted(set(expected)-set(started)),all_passed=len(passed)==len(expected) and all(x['ok'] for x in results),created_container_count=sum(len(x['created_container_ids']) for x in results),worker_tag_removed=plan['tag'],source_unchanged=hashes()==before)
write(H/'summary.json',summary);print(json.dumps(summary),flush=True)
