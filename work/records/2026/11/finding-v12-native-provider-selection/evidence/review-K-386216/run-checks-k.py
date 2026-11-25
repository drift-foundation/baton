from pathlib import Path
import subprocess,os,json,hashlib,tarfile,tempfile,time,shutil
p=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/readiness-386214');e=Path('/var/tmp/baton-k-review-386216/checks')
root=Path(tempfile.mkdtemp(prefix='k-readiness-',dir='/var/tmp/baton-k-review-386216/t3'));repo=root/'repo';repo.mkdir()
assert not any((x/'.git').exists() for x in root.parents)
with tarfile.open(p/'q1/source.tar') as t:t.extractall(repo,filter='data')
env=dict({k:v for k,v in os.environ.items() if not k.startswith('GIT_')},PYTHONDONTWRITEBYTECODE='1');py='/home/sl/.local/state/baton-v12-venv/bin/python'
for args in (['init','-q'],['add','-f','.'],['-c','user.name=Packet fixture','-c','user.email=fixture@invalid','commit','-qm','synthetic checkpoint for preparation checks']):subprocess.run(['git','-C',str(repo),*args],env=env,check=True)
commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True,env=env).strip()
rows=[]
def run(name,args,cwd=None):
 start=time.monotonic();c=subprocess.run([py,'-B',*map(str,args)],cwd=cwd,env=env,capture_output=True,timeout=90)
 (e/(name+'.stdout')).write_bytes(c.stdout);(e/(name+'.stderr')).write_bytes(c.stderr)
 row=dict(name=name,exit_status=c.returncode,seconds=time.monotonic()-start);rows.append(row);print(row,flush=True)
 if c.returncode:print(c.stderr.decode()[-1600:],flush=True)
 return c
run('draft-q1-check',[p/'q1/owner-run.py','--check'])
run('draft-q2-check',[p/'q2/owner-run.py','--check'])
c=run('finalization',[p/'finalize.py','--repository',repo,'--checkpoint',commit,'--output',root/'final'])
assert c.returncode==0
# The exact-tree mismatch refuses before creating a successor packet.
(repo/'v12/worker/codex_agent.py').write_text('synthetic changed checkpoint\n')
subprocess.run(['git','-C',str(repo),'add','.'],env=env,check=True)
subprocess.run(['git','-C',str(repo),'-c','user.name=Packet fixture','-c','user.email=fixture@invalid','commit','-qm','synthetic mismatch'],env=env,check=True)
bad=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],env=env,text=True).strip()
c=run('checkpoint-mismatch',[p/'finalize.py','--repository',repo,'--checkpoint',bad,'--output',root/'must-not-exist']);assert c.returncode!=0 and not (root/'must-not-exist').exists();rows[-1]['expected_refusal']=True
q1=root/'final/q1';q2=root/'final/q2'
for name in ('check_preparation.py','check_runner.py'):run('q1-'+name,[q1/name],root)
for scenario in ('pass','build-fail','probe-fail','remove-fail'):
 c=run('q1-'+scenario,[q1/'check_execute.py',scenario,root],root)
# A synthetic Q1-format bundle proves binding plumbing, not an observed build.
import importlib.util,sys
sys.path.insert(0,str(q2))
spec=importlib.util.spec_from_file_location('synthetic_binding',q2/'check_image_gate.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
synthetic=root/'synthetic-offline-evidence';synthetic.mkdir()
for name,value in mod.synthetic()['retained'].items():(synthetic/name).write_text(json.dumps(value))
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in synthetic.iterdir()}
(synthetic/'evidence-manifest.json').write_text(json.dumps(manifest));mh=hashlib.sha256((synthetic/'evidence-manifest.json').read_bytes()).hexdigest()
run('image-bundle',[p/'bundle-image.py','--evidence',synthetic,'--manifest-sha256',mh,'--review','SIMULATION-ONLY','--finalized-q2',q2,'--output',root/'synthetic-bundle.json'])
(synthetic/'RESULT.json').write_text('{}')
c=run('image-bundle-tamper',[p/'bundle-image.py','--evidence',synthetic,'--manifest-sha256',mh,'--review','SIMULATION-ONLY','--finalized-q2',q2,'--output',root/'must-not-bundle.json']);assert c.returncode!=0;rows[-1]['expected_refusal']=True
for name in ('check_preflight.py','check_image_gate.py','check_collection.py'):run('q2-'+name,[q2/name],root)
for scenario in ('launch-fail','oversize','fault-terminal','provider-seam'):run('q2-'+scenario,[q2/'check_execute.py',scenario,'--evidence',e/('q2-'+scenario)],root)
for scenario in ('pass','build-fail','probe-fail','remove-fail'):
 dest=root/('exec-'+scenario)/'dest'
 if dest.exists():shutil.copytree(dest,e/('q1-'+scenario+'-synthetic'))
account=dict(synthetic_only=True,real_engine_operations=0,real_credential_reads=0,provider_calls=0,fixture_root=str(root),synthetic_checkpoint=commit,packet_manifest_sha256=hashlib.sha256((p/'packet-manifest.json').read_bytes()).hexdigest(),rows=rows,selected=19,executed=len(rows),passed=sum((x['exit_status']!=0 if x.get('expected_refusal') else x['exit_status']==0) for x in rows))
(e/'account.json').write_text(json.dumps(account,indent=2)+'\n')
print(json.dumps(account),flush=True)
# Retain failed preparation roots for diagnosis; successful roots can be removed.
if account['passed']==account['executed']==account['selected']:
 for here,dirs,files in os.walk(root):os.chmod(here,0o700)
 shutil.rmtree(root);(e/'cleanup.json').write_text(json.dumps(dict(root=str(root),removed=not root.exists()))+'\n')
