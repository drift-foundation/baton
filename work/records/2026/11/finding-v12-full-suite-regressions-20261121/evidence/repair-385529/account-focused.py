from pathlib import Path
import os,subprocess,json,re,hashlib
r=Path('/home/sl/src/baton');e=Path(__file__).resolve().parent;c=r/'work/scratch/w385517-385529/candidate/v12/python'
script='''import unittest,json
s=unittest.defaultTestLoader.loadTestsFromNames(['tests.manager.test_authoring_manager_guard','tests.tools.test_parallel_runner'])
def ids(s):
 for x in s:
  if isinstance(x,unittest.TestSuite): yield from ids(x)
  else: yield x.id()
print(json.dumps(list(ids(s))))
'''
collected=json.loads(subprocess.check_output(['/home/sl/.local/state/baton-v12-venv/bin/python','-B','-c',script],cwd=c,env=dict(os.environ,PYTHONPATH=str(c/'src')+os.pathsep+str(c)),text=True))
log=(e/'candidate-final.log').read_text();matches=list(re.finditer(r'^test_\w+ \(([^)]+)\)',log,re.M));outcomes=[]
for i,m in enumerate(matches):
 chunk=log[m.end():matches[i+1].start() if i+1<len(matches) else len(log)]
 status=re.search(r'(?:\.\.\. |\n)(ok|FAIL|ERROR)(?:\n|$)',chunk)
 assert status,chunk
 outcomes.append({'id':m.group(1),'outcome':status.group(1)})
executed=[x['id'] for x in outcomes];assert sorted(collected)==sorted(executed) and len(set(executed))==len(executed) and all(x['outcome']=='ok' for x in outcomes)
(e/'accounting.json').write_text(json.dumps({'method':'Prepared-interpreter unittest collection compared with verbose test-one outcomes; not parallel_test --account','collected':collected,'outcomes':outcomes,'counts':{'collected':len(collected),'executed':len(executed),'passed':len(executed),'failures':0,'errors':0,'skips':0,'duplicates':0,'unaccounted':0}},indent=2)+'\n')
state={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),'index_sha256':hashlib.sha256((r/'.git/index').read_bytes()).hexdigest()};(e/'protected-after.json').write_text(json.dumps(state,indent=2)+'\n'); assert state==json.loads((e/'protected-before.json').read_text())
assert not subprocess.check_output(['git','diff','--','v12'],cwd=r)
manifest=json.loads((e/'manifest.json').read_text());assert all(hashlib.sha256((c.parents[1]/x['path']).read_bytes()).hexdigest()==x['candidate_sha256'] for x in manifest['files'])
print(json.dumps({'tests':len(executed),'manifest_sha256':hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),'scratch_remaining':list(map(str,(r/'work/scratch/w385517-385529/tmp').iterdir()))}))
