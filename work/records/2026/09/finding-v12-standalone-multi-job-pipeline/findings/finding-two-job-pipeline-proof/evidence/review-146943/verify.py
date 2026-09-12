"""Independent run6 preparation custody checks; no live stores or host mutation."""
from pathlib import Path
import hashlib,json,stat,time,shutil,difflib
ROOT=Path('/home/sl/src/baton')
PROOF=ROOT/'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
OUT=Path(__file__).resolve().parent
started=time.monotonic()
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(p,expected): assert sha(p)==expected.removeprefix('sha256:'),str(p)
def manifest(p,expected):
 check(p,expected)
 files=read(p)['files']
 for name,row in files.items():
  target=ROOT/name
  assert target.is_file() and not target.is_symlink(),name
  check(target,row['sha256'])
  assert target.stat().st_size==row['bytes']
  if 'mode' in row: assert oct(stat.S_IMODE(target.stat().st_mode))==row['mode'],name
 return len(files)
candidate=PROOF/'prepared-146897'
counts={'candidate':manifest(candidate/'candidate-manifest.json','d24b5349ed6a6e35b37fbc933eaa2550fea7233d2483123ba5ad985f3d1f7c37')}
prov=read(candidate/'evidence/provenance.json')
for key in ('correction','preparation','freeze'):
 row=prov[key];counts[key]=manifest(ROOT/row['path'],row['sha256'])
for name,row in prov['provider_chain'].items():
 if row.get('expected_absence_matches'): assert not (ROOT/name).exists()
 else: check(ROOT/name,row['sha256'])
for key in ('source_requirements','current_observation_sources'):
 for name,digest in prov[key].items(): check(ROOT/name,digest)
for name in prov['unchanged_dependencies']:
 assert (candidate/name).read_bytes()==(PROOF/'prepared-146797'/name).read_bytes(),name
changed=prov['changed_dependencies']
delta=''
for row in changed:
 prior=PROOF/row['prior'];current=candidate/row['path']
 delta+=''.join(difflib.unified_diff(prior.read_text().splitlines(True),current.read_text().splitlines(True),fromfile=str(prior.relative_to(ROOT)),tofile=str(current.relative_to(ROOT))))
assert delta==(candidate/'evidence/preparation-delta.patch').read_text()
(OUT/'independent-delta.patch').write_text(delta)
assert (candidate/'evidence/generated-integration-instructions.txt').read_bytes()==(PROOF/'prepared-146797/evidence/generated-integration-instructions.txt').read_bytes()
fresh=Path('/home/sl/.local/state/baton/v12/w71879-run6')
assert not fresh.exists() and not fresh.is_symlink()
for name in ('frozen-config','validation.json','selected-images.json','execution-review.json'):
 assert not (candidate/name).exists(),name
suite=Path('/tmp/w71879-146897-offline-verification-6blji9oh')
for name in ('verification.txt','verification.json'): shutil.copyfile(suite/name,OUT/name)
result={'candidate_sha256':sha(candidate/'candidate-manifest.json'),'counts':counts,'provider_entries':len(prov['provider_chain']),'source_requirements':4,'observation_bindings':3,'unchanged_dependencies':len(prov['unchanged_dependencies']),'changed_dependencies':changed,'fresh_run6_absent':True,'final_inputs_and_markers_absent':True,'instruction_sha256':sha(candidate/'evidence/generated-integration-instructions.txt'),'suite':read(suite/'verification.json'),'seconds':time.monotonic()-started}
(OUT/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

