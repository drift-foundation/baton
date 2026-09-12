"""Independent final manifest and image metadata verification; no runtime."""
from pathlib import Path
import json,hashlib,stat,time,shutil
ROOT=Path('/home/sl/src/baton')
PROOF=ROOT/'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
OUT=Path(__file__).resolve().parent
started=time.monotonic()
def read(p): return json.loads(p.read_text())
def sha(p): return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
manifest=PROOF/'evidence/run6-freeze-146988/candidate-manifest.json'
assert sha(manifest)=='sha256:87a320bdee36cfdca8e7d18372e65ff26eeb314eeda948db3402692b328dd0a9'
files=read(manifest)['files'];assert len(files)==568
for name,row in files.items():
 p=ROOT/name
 assert p.is_file() and not p.is_symlink(),name
 assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],name
 assert oct(stat.S_IMODE(p.stat().st_mode))==row['mode'],name
current=read(OUT/'images.json');prior=read(PROOF/'evidence/run6-freeze-146988/images.json')
for got,expected in zip(current,prior,strict=True):
 for key in ('Id','Created','Architecture','Os','Config','RootFS','Size'): assert got[key]==expected[key],key
actual=Path('/tmp/w71879-146988-documents-5cwqwn0l/verification.json')
shutil.copyfile(actual,OUT/'actual-inputs.json')
doc=read(actual)
assert len(doc['actual_documents'])==33
result={'manifest':str(manifest.relative_to(ROOT)),'manifest_sha256':sha(manifest),'files':len(files),'images_match':True,'actual_documents':33,'helpers':{name:sha(PROOF/'prepared-146897'/name) for name in ('deployment.py','run.py','target_posture.py')},'reconstruction':str(actual),'actual_input_seconds':doc['verification_seconds'],'custody_seconds':time.monotonic()-started}
(OUT/'custody.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

