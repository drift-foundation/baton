"""Preparation: drive owner-run.execute() end to end against fakedocker.py. Simulation only."""
import importlib.util,json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;S=Path(sys.argv[2])
scenario=sys.argv[1];run=S/('exec-'+scenario);run.mkdir()
opens=[];others=[]
def hook(ev,args):
    if ev=='open' and isinstance(args[0],str) and os.path.isabs(args[0]):
        p=os.path.realpath(args[0])
        if (p.startswith('/home/') or p.startswith(os.environ['HOME'])) and not p.startswith(str(P)) and not p.startswith('/home/sl/.local/state/baton-v12-venv'):opens.append(p)
sys.addaudithook(hook)
real=subprocess.Popen
def popen(argv,*a,**k):
    if argv[0]=='docker':argv=[sys.executable,'-I',str(P/'fakedocker.py'),str(run/'engine.json'),scenario,*argv[1:]]
    else:raise AssertionError('non-fake child forbidden: '+str(argv[:1]))
    return real(argv,*a,**k)
subprocess.Popen=popen
spec=importlib.util.spec_from_file_location('q1_owner',P/'owner-run.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
_check=owner.check

owner.ROOT=run/'root';owner.DEST=run/'dest'
status=owner.execute('SIMULATION-ONLY',owner.check()['packet_manifest_sha256'])
print(json.dumps(dict(scenario=scenario,exit=status,home_opens=sorted(set(opens)),non_docker_processes=others,dest=sorted(str(p.relative_to(owner.DEST)) for p in owner.DEST.rglob('*') if p.is_file() and 'commands' not in p.parts),commands=len(list((owner.DEST/'commands').glob('*.command.json')))),indent=1))

verdict=json.loads((owner.DEST/'RESULT.json').read_text())
assert status==(0 if scenario=='pass' else 1)
assert verdict['passed']==(scenario=='pass')
if scenario=='remove-fail':assert verdict['cleanup']['removed'] is None and verdict['cleanup']['ceased'] is True
else:assert verdict['cleanup']['ceased'] is True and verdict['cleanup']['removed'] is True
allowed={'selection.json','engine-version.json','image-inspect.json','image.id','launched-image.json','digest-kind.json','worker-observation.json','cleanup.json','receipt-after-removal.json','RESULT.json','container-intent.json','manager-after-removal.json','evidence-manifest.json','commands'}
assert {p.name for p in owner.DEST.iterdir()}<=allowed
assert not others and not opens,(others,opens)
print('PASS real execute simulation '+scenario)
