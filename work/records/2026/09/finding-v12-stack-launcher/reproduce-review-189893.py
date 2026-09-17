import os,sys,json,tempfile,time,subprocess,hashlib
from pathlib import Path
R=Path('/home/sl/src/baton');D=R/'work/records/2026/09/finding-v12-stack-launcher'
sys.path[:0]=[str(R/'v12/python'),str(R/'v12/python/src')]
from tools import bootstrap,instance
start=time.monotonic();root=Path(tempfile.mkdtemp(prefix='w183883-review189893-'))
r={'scratch':str(root)}
a=json.loads((D/'EVIDENCE-189861.json').read_text())
r['changed_candidate_mismatches']=[p for p,h in a['changed_this_claim'].items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]
foreign=root/'foreign.json';foreign.write_text(json.dumps({'schema':bootstrap.IDENTITY_SCHEMA,'authority_uuid':'a'*32}))
def result(call):
 try:return {'accepted':True,'value':call()}
 except Exception as e:return {'accepted':False,'type':type(e).__name__,'detail':str(e)}
link=root/'linked';link.mkdir();places=bootstrap.layout(str(link));Path(places['identity']).symlink_to(foreign)
r['link_read']=result(lambda:bootstrap.identity(places))
r['link_collision']=result(lambda:bootstrap.persist_identity(places,'a'*32))
r['link_custody']=result(lambda:bootstrap.custody(instance.layout(str(link)),str(link)))
fifo=root/'fifo';fifo.mkdir();fp=bootstrap.layout(str(fifo));os.mkfifo(fp['identity'])
r['fifo_custody']=result(lambda:bootstrap.custody(instance.layout(str(fifo)),str(fifo)))
code='from tools import bootstrap; import sys; print(bootstrap.identity(bootstrap.layout(sys.argv[1])))'
t=time.monotonic()
try:
 p=subprocess.run(['/home/sl/.local/state/baton-v12-venv/bin/python','-c',code,str(fifo)],cwd=R/'v12/python',env=dict(os.environ,PYTHONPATH='src:.',PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=2)
 r['fifo_read']={'timeout':False,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
except subprocess.TimeoutExpired:
 r['fifo_read']={'timeout':True,'limit_seconds':2,'child_killed_and_reaped_by_subprocess_run':True}
r['fifo_seconds']=time.monotonic()-t
large=root/'large';large.mkdir();lp=bootstrap.layout(str(large));good=foreign.read_bytes();Path(lp['identity']).write_bytes(good+b' '*(65536-len(good))+b'NOT JSON')
r['trailing_invalid_bytes_read']=result(lambda:bootstrap.identity(lp))
r['entire_record_json']=result(lambda:json.loads(Path(lp['identity']).read_bytes()))
r['audit_seconds']=time.monotonic()-start
t=time.monotonic()
p=subprocess.run(['/home/sl/.local/state/baton-v12-venv/bin/python','-m','unittest','tests.tools.test_bootstrap.TheInstanceGeneratesItsOwnIdentity'],cwd=R/'v12/python',env=dict(os.environ,PYTHONPATH='src:.',PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=30)
r['tests']={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-t}
(D/'REVIEW-EVIDENCE-189893.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
