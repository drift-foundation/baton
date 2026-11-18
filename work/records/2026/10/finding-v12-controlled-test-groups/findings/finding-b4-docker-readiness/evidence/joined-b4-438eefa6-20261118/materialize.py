"""Materialize the selected commit through read-only Git object reads."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/'AGENTS.md').is_file())
COMMIT='438eefa68f592e159f42cf1d190c7d7de4afde12'
SNAP=REPO/'work/scratch/w384944-joined-438eefa6-20261118'
SNAP.mkdir(exist_ok=False)
files={}
def export(paths):
 entries=subprocess.check_output(['git','ls-tree','-rz','--full-tree',COMMIT,'--',*paths],cwd=REPO).split(b'\0')
 for entry in filter(None,entries):
  meta,rawpath=entry.split(b'\t',1);mode,kind,blob=meta.decode().split();path=rawpath.decode();assert kind=='blob' and mode in ('100644','100755','120000'),entry
  if path in files:continue
  content=subprocess.check_output(['git','show',COMMIT+':'+path],cwd=REPO)
  dest=SNAP/path;dest.parent.mkdir(parents=True,exist_ok=True)
  if mode=='120000':os.symlink(content.decode(),dest)
  else:dest.write_bytes(content);dest.chmod(int(mode,8)&0o777)
  files[path]=dict(sha256=hashlib.sha256(content).hexdigest(),mode=mode,blob=blob)
export(['v12'])
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
inputs=json.loads(subprocess.check_output([sys.executable,'-c','import json;from tools.parallel_test import consumed_inputs;print(json.dumps(consumed_inputs()))'],cwd=SNAP/'v12/python',env=env,text=True))
export(inputs)
for path in inputs:assert any(p==path or p.startswith(path+'/') for p in files),path
result=dict(commit=COMMIT,snapshot=str(SNAP.relative_to(REPO)),declared_consumed_inputs=inputs,files=files)
(HERE/'source-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(snapshot=result['snapshot'],files=len(files),consumed_files=sum(not p.startswith('v12/') for p in files),declared_paths=len(inputs))))
