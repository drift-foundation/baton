"""Bounded four-case Docker run with exact task-label emergency cleanup."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,tempfile,time,uuid
HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/'AGENTS.md').is_file())
m=json.loads((HERE.parent/'allocation-c4-20261031/snapshot-manifest.json').read_text())
SNAP=REPO/m['snapshot']; label=sys.argv[1]; assert label.isalnum()
IMAGE='sha256:dacb6a0e11d5513a4fd774066141bb62d84e7bc0ad8be39df4ab7e96fb614ef0'
assert 1001 in os.getgroups() and os.geteuid()!=0
root=Path(tempfile.mkdtemp(prefix='baton-w384944-input-engine-',dir='/var/tmp')); os.chown(root,-1,1001); os.chmod(root,0o2770)
nonce=uuid.uuid4().hex; tasklabel='baton.w384944.run='+nonce
out=HERE/label; out.mkdir()
shim=root/'bin'; shim.mkdir()
# The shim adds only an evidence label, retaining the product's whole run vector.
(shim/'docker').write_text('''#!/usr/bin/python3
import json,os,subprocess,sys
from pathlib import Path
argv=sys.argv[1:]
if argv and argv[0]=='run': argv[1:1]=['--label',os.environ['ACCESS_TASK_LABEL']]
r=subprocess.run(['/usr/bin/docker',*argv],capture_output=True)
record={'command':argv[0] if argv else '', 'status':r.returncode}
if argv and argv[0]=='run' and r.returncode==0:
 cid=r.stdout.decode().strip() if '--detach' in argv or '-d' in argv else argv[argv.index('--name')+1]; record['id']=cid; record['stdout']=r.stdout.decode(errors='replace'); record['stderr']=r.stderr.decode(errors='replace')
 info=subprocess.run(['/usr/bin/docker','inspect',cid],capture_output=True)
 if info.returncode==0:
  d=json.loads(info.stdout)[0]; record['inspect']={k:d[k] for k in ['Id','Image','State','Mounts']}; record['inspect']['User']=d['Config']['User']; record['inspect']['Labels']=d['Config']['Labels']; record['inspect']['HostConfig']={k:d['HostConfig'].get(k) for k in ['ReadonlyRootfs','Privileged','NetworkMode','CapDrop','SecurityOpt','GroupAdd']}
if argv and argv[0] in ['logs','wait','rm']: record.update({'id':argv[-1],'stdout':r.stdout.decode(errors='replace'),'stderr':r.stderr.decode(errors='replace')})
with open(os.environ['ACCESS_ENGINE_LOG'],'a') as f:f.write(json.dumps(record)+'\\n')
sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);sys.exit(r.returncode)
'''); (shim/'docker').chmod(0o755)
env=dict(os.environ,PATH=str(shim)+':'+os.environ['PATH'],TMPDIR=str(root),BATON_V12_DISK_ROOT=str(root),BATON_V12_INPUT_DELIVERY_IMAGE=IMAGE,BATON_V12_WORKSPACE_GROUP='1001',BATON_TEST_ENGINE='docker',PYTHONDONTWRITEBYTECODE='1',ACCESS_TASK_LABEL=tasklabel,ACCESS_ENGINE_LOG=str(out/'engine.jsonl'))
def docker(*a):
 r=subprocess.run(['/usr/bin/docker',*a],capture_output=True,text=True,timeout=30); assert r.returncode==0,r.stderr; return r.stdout.strip()
def hashes():return {x['path']:hashlib.sha256((SNAP/x['path']).read_bytes()).hexdigest() for x in m['files']}
before=hashes(); old=docker('ps','-aq','--no-trunc').splitlines(); info=json.loads(docker('image','inspect',IMAGE))[0]; assert info['Id']==IMAGE and not info['Config'].get('Volumes')
(out/'preflight.json').write_text(json.dumps({'uid':os.geteuid(),'gid':os.getegid(),'groups':os.getgroups(),'image':IMAGE,'old_containers':old,'root':str(root),'task_label':tasklabel,'selected_environment':{k:env[k] for k in ['TMPDIR','BATON_V12_DISK_ROOT','BATON_V12_INPUT_DELIVERY_IMAGE','BATON_V12_WORKSPACE_GROUP','BATON_TEST_ENGINE']}},indent=2)+'\n')
(out/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
argv=['just','test-one','tests.manager.test_input_delivery.DockerDelivery','tests.manager.test_input_delivery.DockerConfiguredGroup']; start=time.monotonic(); timedout=False
with (out/'focused.log').open('x') as log:
 proc=subprocess.Popen(argv,cwd=SNAP/'v12',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:proc.wait(timeout=600)
 except subprocess.TimeoutExpired:
  timedout=True; os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=10)
elapsed=time.monotonic()-start
remaining=docker('ps','-aq','--no-trunc','--filter','label='+tasklabel).splitlines(); cleaned=[]
for cid in remaining:
 d=json.loads(docker('inspect',cid))[0]; assert d['Id']==cid and d['Image']==IMAGE and d['Config']['Labels'].get('baton.w384944.run')==nonce
 docker('rm','--force',cid); cleaned.append(cid)
assert not docker('ps','-aq','--filter','label='+tasklabel)
after=hashes(); current=docker('ps','-aq','--no-trunc').splitlines(); assert set(old)<=set(current),'old container missing'
(shim/'docker').unlink();shim.rmdir(); leftovers=sorted(str(p.relative_to(root)) for p in root.rglob('*'))
if not leftovers:root.rmdir()
result={'argv':argv,'exit':proc.returncode,'timed_out':timedout,'seconds':elapsed,'source_drift':[p for p in before if before[p]!=after[p]],'emergency_cleanup':cleaned,'task_containers_remaining':[],'old_containers_preserved':True,'temporary_root':str(root),'leftovers':leftovers,'root_removed':not root.exists()}
(out/'source-after.json').write_text(json.dumps(after,indent=2)+'\n');(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));sys.exit(proc.returncode or bool(leftovers) or bool(result['source_drift']))
