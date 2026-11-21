from pathlib import Path
import hashlib,json,subprocess,difflib
r=Path('/home/sl/src/baton');e=Path(__file__).resolve().parent;c=r/'work/scratch/w385517-385529/candidate';base=json.loads((e/'protected-before.json').read_text())['head']; files=[];patch=[]
for path in ['v12/python/tests/manager/test_authoring_manager_guard.py','v12/python/tests/tools/test_parallel_runner.py','v12/python/tools/parallel_test.py']:
 before=subprocess.check_output(['git','show',base+':'+path],cwd=r);after=(c/path).read_bytes()
 for label,data in [('base',before),('candidate',after)]:
  target=e/label/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 files.append({'path':path,'base_sha256':hashlib.sha256(before).hexdigest(),'candidate_sha256':hashlib.sha256(after).hexdigest()})
 patch.extend(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+path,tofile='b/'+path))
(e/'candidate.patch').write_text(''.join(patch));tree=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
manifest={'base':base,'tree_sha256':tree,'files':files,'patch_sha256':hashlib.sha256((e/'candidate.patch').read_bytes()).hexdigest()};(e/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
