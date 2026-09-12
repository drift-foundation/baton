"""Read old provider contracts with explicit independently accepted successor bytes."""
from pathlib import Path
import hashlib,json,time
R=Path('/home/sl/src/baton')
REC=R/'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
E=REC/'evidence/run10-freeze-152932'
def sha(p):return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
start=time.monotonic()
prior=json.loads((REC/'prepared-146897/evidence/provenance.json').read_text())
accepted=json.loads((REC/'evidence/accounting-152750/candidate-manifest.json').read_text())['files']
new_paths=json.loads((REC/'evidence/accounting-152563/product-base.json').read_text())
stage_paths=('v12/python/tools/stage_execution.py','v12/python/tests/tools/test_stage_execution.py')
base={n:REC/'evidence/accounting-152563'/('base-'+Path(n).name) for n in new_paths}
base.update({n:REC/'evidence/observation-correction-149854'/('base-'+Path(n).name) for n in stage_paths})
stage_accepted=json.loads((REC/'evidence/run9-freeze-150125/candidate-manifest.json').read_text())['files']
held={}
for group in ('provider_chain','source_requirements','current_observation_sources'):
 rows=[]
 for name,record in prior[group].items():
  expected=record.get('sha256') if isinstance(record,dict) else record
  p=R/name
  if not expected:
   assert not p.exists() and not p.is_symlink(),name
   rows.append({'path':name,'absent':True});continue
  target=base.get(name,p)
  assert sha(target).removeprefix('sha256:')==expected.removeprefix('sha256:'),name
  if name in base:
   newest=accepted[name] if name in new_paths else stage_accepted[name]
   assert sha(p)==newest['sha256'] and p.stat().st_size==newest['bytes'],name
  rows.append({'path':name,'base_sha256':expected,'current_sha256':sha(p),'authority':'owner152560/review152791' if name in new_paths else 'owner149847/review149919' if name in stage_paths else 'unchanged accepted provider'})
 held[group]=rows
for name in new_paths:
 assert sha(R/name)==accepted[name]['sha256'],name
v={'source_bindings':held,'three_product_paths':{n:sha(R/n) for n in new_paths},'seconds':time.monotonic()-start}
(E/'source-provenance.json').write_text(json.dumps(v,indent=2)+'\n')
print({'seconds':v['seconds'],'source_groups':{k:len(x) for k,x in held.items()},'three_product_paths_accepted':True})
