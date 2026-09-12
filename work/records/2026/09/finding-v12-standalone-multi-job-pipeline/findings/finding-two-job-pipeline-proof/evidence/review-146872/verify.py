"""Independent file custody and exact delta review; no stores or providers."""
from pathlib import Path
import hashlib, json, stat, time, difflib, shutil
ROOT=Path('/home/sl/src/baton')
PROOF=ROOT/'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
OUT=Path(__file__).resolve().parent
started=time.monotonic()
def read(p): return json.loads(p.read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(p, value): assert digest(p)==value.removeprefix('sha256:'), str(p)
def manifest(p, expected):
 check(p,expected)
 data=read(p)
 for name,row in data['files'].items():
  target=ROOT/name
  assert target.is_file() and not target.is_symlink(), name
  check(target,row['sha256'])
  assert target.stat().st_size==row['bytes'], name
  if 'mode' in row: assert oct(stat.S_IMODE(target.stat().st_mode))==row['mode'], name
 return len(data['files'])
candidate=PROOF/'prepared-146797'
counts={'candidate':manifest(candidate/'candidate-manifest.json','156cb7f53d1eab4e41d1602742ddda778376250b6d1af5e7eee9e12a3c775588')}
provenance=read(candidate/'evidence/provenance.json')
for pathkey,hashkey,label in [('prior_manifest','prior_manifest_sha256','prior_preparation'),('preserved_freeze','preserved_freeze_sha256','prior_freeze')]:
 counts[label]=manifest(ROOT/provenance[pathkey],provenance[hashkey])
for name,row in provenance['provider_chain'].items():
 if row.get('expected_absence_matches'): assert not (ROOT/name).exists()
 else: check(ROOT/name,row['sha256'])
for key in ('source_requirements','current_observation_sources'):
 for name,value in provenance[key].items(): check(ROOT/name,value)
for name in provenance['unchanged_dependencies']:
 assert (candidate/name).read_bytes()==(PROOF/'prepared-146538'/name).read_bytes(),name
delta=''
for name in provenance['changed_dependencies']:
 delta+=''.join(difflib.unified_diff((PROOF/'prepared-146538'/name).read_text().splitlines(True),(candidate/name).read_text().splitlines(True),fromfile='prepared-146538/'+name,tofile='prepared-146797/'+name))
assert delta==(candidate/'evidence/correction-delta.patch').read_text()
(OUT/'independent-delta.patch').write_text(delta)
suite=Path('/tmp/w71879-146538-offline-verification-c96m6cl9')
for name in ('verification.json','verification.txt'): shutil.copyfile(suite/name,OUT/name)
result={'counts':counts,'provider_entries':len(provenance['provider_chain']),'source_requirements':len(provenance['source_requirements']),'additional_observation_sources':len(provenance['current_observation_sources']),'unchanged_dependencies':len(provenance['unchanged_dependencies']),'changed_dependencies':provenance['changed_dependencies'],'candidate_sha256':digest(candidate/'candidate-manifest.json'),'verification_seconds':time.monotonic()-started,'suite':read(suite/'verification.json'),'scope':'File hashes/modes, exact diff and offline suite. No live owner settlement, model run or host posture claim.'}
(OUT/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

