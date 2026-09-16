"""C-only bounded supervisor with descendant reaping and immutable inputs."""
import ctypes,hashlib,importlib.metadata,json,os,signal,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
ROOT=R.parents[4]
number=sys.argv[1]; selectors=sys.argv[2:]
assert number.isdecimal() and selectors and all(s in ('UsefulCorrection','CountedReopen','InvalidEvidence') for s in selectors)
b=json.loads((R/'BASE-C-180069.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for f in b['read_only_inputs']:assert sha(ROOT/f['path'])==f['sha256'],f['path']
paths=[f['path'] for f in b['read_only_inputs']]+[f['path'] for f in b['new_files']]
before={p:sha(ROOT/p) for p in paths}
assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0
start=time.monotonic();timed_out=False;reaped=[];signals=[]
env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1',BATON_C_EVIDENCE=str(R/('trace-C-180069-'+number+'.json')))
command=[sys.executable,'-B','-m','unittest','-v',*['tests.tools.test_correction_restart.'+s for s in selectors]]
with (R/('run-C-180069-'+number+'.log')).open('x') as log:
 p=subprocess.Popen(command,cwd=ROOT/'v12/python',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:status=p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timed_out=True;os.killpg(p.pid,signal.SIGTERM)
  try:status=p.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);status=p.wait(timeout=5)
for sig in (signal.SIGTERM,signal.SIGKILL):
 try:os.killpg(p.pid,sig);signals.append(sig.name)
 except ProcessLookupError:pass
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  try:child,code=os.waitpid(-1,os.WNOHANG)
  except ChildProcessError:break
  if child:reaped.append([child,code])
  else:time.sleep(.02)
try:os.killpg(p.pid,0);gone=False
except ProcessLookupError:gone=True
after={p:sha(ROOT/p) for p in paths}
result={'claim':180069,'run':number,'selectors':selectors,'command':command,'status':status,'seconds':time.monotonic()-start,'timeout':timed_out,'group_gone':gone,'subreaper':True,'signals':signals,'reaped':reaped,'before':before,'after':after,'python':sys.version,'dependencies':{n:importlib.metadata.version(n) for n in ('jsonschema','jsonschema-specifications','referencing','attrs','rpds-py')}}
(R/('run-C-180069-'+number+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','seconds','timeout','group_gone')}))
raise SystemExit(0 if status==0 and not timed_out and gone and before==after else 1)
