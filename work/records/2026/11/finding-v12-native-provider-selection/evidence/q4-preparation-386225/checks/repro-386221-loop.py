"""Exploration only (not part of the packet): dump the status snapshots a completing run produces."""
import importlib.util,json,os,subprocess,sys,tempfile,hashlib,shutil,time
from pathlib import Path
from unittest import mock
P=Path(sys.argv[1]);out=Path(sys.argv[2]);sys.path.insert(0,str(P))
spec=importlib.util.spec_from_file_location('q2owner',P/'owner-run.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
temporary=Path(tempfile.mkdtemp(prefix='k-explore-',dir=os.environ['TMPDIR']))
owner.ROOT=temporary/'run';owner.DEST=temporary/'public';owner.LOGIN=temporary/'synthetic-login'
owner.LOGIN.write_bytes(b'{"synthetic_q2_only":true}\n');owner.LOGIN.chmod(0o600)
from check_image_gate import synthetic
binding=temporary/'synthetic-image-evidence.json';binding.write_text(json.dumps(synthetic()))
real=subprocess.Popen;state=temporary/'fake-state.json'
def popen(argv,*a,**kw):
    if argv[0]=='docker':return real([sys.executable,'-B',str(P/'fake_engine.py'),str(state),'completed',*argv[1:]],*a,**kw)
    return real(argv,*a,**kw)
import native
realdrive=native.drive;snaps=[]
def drive(job,control,ops):
    s=realdrive(job,control,ops);snaps.append(s)
    if len(snaps)>12:raise RuntimeError('exploration stop')
    return s
native.drive=drive
with mock.patch('subprocess.Popen',side_effect=popen):
    r=owner.execute('SIMULATION-ONLY',hashlib.sha256((P/'payload.json').read_bytes()).hexdigest(),binding,hashlib.sha256(binding.read_bytes()).hexdigest())
out.write_text(json.dumps(dict(result=r,snaps=snaps,files=sorted(str(p.relative_to(owner.ROOT)) for p in owner.ROOT.rglob('*') if p.is_file() and 'source/' not in str(p.relative_to(owner.ROOT)))[:200]),indent=1,default=repr))
for name in ('simulated-worker-error.txt','private-error.json','RESULT.json'):
    if (owner.ROOT/name).exists():print(name,(owner.ROOT/name).read_text()[-900:])
for here,dirs,files in os.walk(temporary):os.chmod(here,0o700)
shutil.rmtree(temporary)
