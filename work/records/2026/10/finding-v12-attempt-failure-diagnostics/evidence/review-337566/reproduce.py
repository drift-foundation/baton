from pathlib import Path
import json,hashlib,subprocess,time,tempfile,os,shutil
repo=Path('/home/sl/src/baton'); dossier=repo/'work/records/2026/10/finding-v12-attempt-failure-diagnostics'; p=dossier/'execution-337453'; e=dossier/'evidence/review-337566'; e.mkdir()
root=Path(tempfile.mkdtemp(prefix='w333486-review-337566-'))/'root'; runs=[]
def run(label,args,ok=True,env=None,cwd=None):
 start=time.monotonic(); r=subprocess.run(args,capture_output=True,text=True,timeout=45,env=env,cwd=cwd or repo); elapsed=time.monotonic()-start
 (e/(label+'.log')).write_text(r.stdout+r.stderr); runs.append(dict(label=label,argv=args,returncode=r.returncode,seconds=elapsed)); assert (r.returncode==0)==ok,(label,r.stderr,r.stdout)
 return r
for line in (p/'SHA256SUMS').read_text().splitlines():
 h,n=line.split(maxsplit=1);assert hashlib.sha256((p/n.lstrip('*')).read_bytes()).hexdigest()==h,n
run('pins',['python3','-B',str(p/'verify-inputs.py')])
run('unselected-refusal',['python3','-B',str(p/'prepare.py'),'stage','--root',str(root)],False);assert not root.exists()
run('stage',['python3','-B',str(p/'prepare.py'),'stage','--root',str(root),'--acknowledge-unselected-start'])
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(root/'code/v12/python/src')+':'+str(root/'code/v12/python')+':'+str(root/'supervisor'))
run('bootstrap',['python3','-B','-m','tools.bootstrap','--inputs',str(root/'bootstrap-inputs.json'),'--destination',str(root/'instance'),'--distro','/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro','--no-repositories'],env=env,cwd=root/'code/v12/python')
run('bind',['python3','-B',str(p/'prepare.py'),'bind','--root',str(root)])
code='''import json,sys,hashlib
from pathlib import Path
import baseline
from tools import authoring_enforcement as a
r=Path(sys.argv[1]); p=baseline.held_packet(str(r/'packet/PACKET.json')); baseline.verify_imported_sources(p);a.verify_controller(p)
assert hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest()=='bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f'
c=json.loads((r/'packet/AUTHORING-COMMAND.json').read_text()); print(json.dumps(c,indent=2))
for key in ('job_store','control_store'): assert not Path(p['deployment'][key]).exists()
s=json.loads((r/'packet/submission.json').read_text());assert s['jobs'][0]['execution_limits']==dict(provider_turn_seconds=3600,verification_command_seconds=30)
assert p['bounds']['total_seconds']==4800 and p['bounds']['cleanup_seconds']==60
print('corrected controller binding, limits, absent execution stores: PASS')
'''
run('controller',['python3','-B','-c',code,str(root)],env=env,cwd=root/'code/v12/python')
neg=root.parent/'negative';shutil.copytree(p,neg)
pins=json.loads((neg/'PREPARATION-PINS.json').read_text());pins['authoring_controller']['sha256']='2da6eb36b398d730c8cc07a9df0b604de678a3fd994d5019097fa023addfb88f';(neg/'PREPARATION-PINS.json').write_text(json.dumps(pins))
r=run('superseded-controller-refusal',['python3','-B',str(neg/'prepare.py'),'stage','--root',str(root.parent/'refused'),'--acknowledge-unselected-start'],False);assert 'controller is not pinned' in r.stderr;assert not (root.parent/'refused').exists()
result=dict(manifest_sha256=hashlib.sha256((p/'PACKET-INPUTS.json').read_bytes()).hexdigest(),sealed_members=len((p/'SHA256SUMS').read_text().splitlines()),root=str(root),runs=runs,total_seconds=sum(x['seconds'] for x in runs))
(e/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copyfile(__file__,e/'reproduce.py');print(json.dumps({k:v for k,v in result.items() if k!='runs'}))
