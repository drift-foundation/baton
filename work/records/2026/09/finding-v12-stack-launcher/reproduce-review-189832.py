import sys,json,hashlib,tempfile,time,subprocess,os
from pathlib import Path
R=Path('/home/sl/src/baton');D=R/'work/records/2026/09/finding-v12-stack-launcher'
sys.path[:0]=[str(R/'v12/python'),str(R/'v12/python/src')]
from tools import bootstrap,instance
from baton_v12.job_manager import scheduler
start=time.monotonic(); root=Path(tempfile.mkdtemp(prefix='w183883-review189832-'))
r={'scratch':str(root),'scope':'identity/schema/read checks only; no Authority or Job/control store opened'}
latest=json.loads((D/'EVIDENCE-189719.json').read_text())
r['changed_candidate_mismatches']=[p for p,h in latest['changed_this_claim'].items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]
def refused(call):
 try:
  value=call();return {'accepted':True,'value':value}
 except Exception as e:
  return {'accepted':False,'type':type(e).__name__,'detail':str(e)}
r['empty_pool']=refused(lambda:scheduler.own_pool({'schema':scheduler.POOL_SCHEMA,'variant':'empty','separation_class':scheduler.SEPARATION_CLASSES[0],'workers':[]}))
guide=(R/'v12/STACK.md').read_text().split('### A fresh installation has zero Jobs',1)[1].split('```json',1)[1].split('```',1)[0]
r['guide_json']=refused(lambda:json.loads(guide))
foreign=root/'foreign-identity.json';uuid='a'*32
foreign.write_text(json.dumps({'schema':bootstrap.IDENTITY_SCHEMA,'authority_uuid':uuid}))
r['linked_identity']=[]
for name in ('one','two'):
 dest=root/name;dest.mkdir();places=bootstrap.layout(str(dest));Path(places['identity']).symlink_to(foreign)
 r['linked_identity'].append({'destination':str(dest),'custody':refused(lambda:bootstrap.custody(instance.layout(str(dest)),str(dest))),'identity':refused(lambda:bootstrap.identity(places)),'persist':refused(lambda:bootstrap.persist_identity(places,uuid))})
r['foreign_unchanged']=json.loads(foreign.read_text())['authority_uuid']==uuid
r['audit_seconds']=time.monotonic()-start
t=time.monotonic()
p=subprocess.run(['/home/sl/.local/state/baton-v12-venv/bin/python','-m','unittest','tests.tools.test_bootstrap.TheInstanceGeneratesItsOwnIdentity'],cwd=R/'v12/python',env=dict(os.environ,PYTHONPATH='src:.',PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=30)
r['tests']={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-t}
(D/'REVIEW-EVIDENCE-189832.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
