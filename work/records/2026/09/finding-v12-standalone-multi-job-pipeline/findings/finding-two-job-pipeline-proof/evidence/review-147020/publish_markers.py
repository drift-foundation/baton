"""Publish this reviewer's own final-input markers after full verification."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path('/home/sl/src/baton')
PROOF=ROOT/'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
PREP=PROOF/'prepared-146897'
OUT=Path(__file__).resolve().parent
def sha(p): return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):
 with p.open('x') as out: json.dump(value,out,indent=2,sort_keys=True);out.write('\n')
manifest=PROOF/'evidence/run6-freeze-146988/candidate-manifest.json'
assert sha(manifest)=='sha256:87a320bdee36cfdca8e7d18372e65ff26eeb314eeda948db3402692b328dd0a9'
files=json.loads(manifest.read_text())['files']
reviewed={str(ROOT/name):row['sha256'] for name,row in files.items()}
reviewed[str(manifest)]=sha(manifest)
for name,digest in reviewed.items(): assert sha(Path(name))==digest,name
assert len(reviewed)==569
locator='baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/review-2026-09-11T20-11-32Z.md'
assert (PROOF/'review-2026-09-11T20-11-32Z.md').is_file()
images=json.loads((PREP/'candidate-images.json').read_text())
profile=json.loads((PREP/'frozen-config/runtime-profile.json').read_text())
assert images==profile['image_variants']
review={'verdict':'accepted','review_locator':locator,'reviewer':'baton.codex','reviewed_at':'2026-09-11T20:11:32Z','config_files':{name:sha(PREP/'frozen-config'/name) for name in ('stage-execution.json','submission.json')},'reviewed_files':reviewed,'execution_authorized':False,'authorization_note':'Owner146985 withholds another model attempt. Final package acceptance is not model-run authorization.'}
for helper in ('deployment.py','run.py','target_posture.py'): assert str(PREP/helper) in reviewed
write(PREP/'selected-images.json',images)
write(PREP/'execution-review.json',review)
for name in ('selected-images.json','execution-review.json'):
 assert json.loads((PREP/name).read_text())==(images if name=='selected-images.json' else review)
 shutil.copyfile(PREP/name,OUT/name)
write(OUT/'markers.json',{'review':locator,'bindings':len(reviewed),'execution_authorized':False,'markers':{name:sha(PREP/name) for name in ('selected-images.json','execution-review.json')}})
print((OUT/'markers.json').read_text())

