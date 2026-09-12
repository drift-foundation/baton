from pathlib import Path
import json,re,hashlib
r=Path('/home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof');old=r/'prepared-149053';p=r/'prepared-149488';p.mkdir();e=r/'evidence/run8-preparation-149488';e.mkdir()
created=Path('/tmp/w71879-149488-created.txt').read_text()
old_ruling='M141636/return149049; run7 image and package preparation authorized; model execution not authorized'
ruling='M141636/return149484; run8 preparation and exactly one operator attempt after independent input review authorized; no agent model execution or automatic retry'
excluded={'frozen-config','image-build','__pycache__'}
for f in old.rglob('*'):
 rel=f.relative_to(old)
 if not f.is_file() or any(x in excluded for x in rel.parts) or f.name in ('validation.json','selected-images.json','execution-review.json','candidate-manifest.json','test_run7_preparation.py'):continue
 dest=p/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes())
s=(old/'deployment.py').read_text().replace('run7','run8').replace('c71879b1000000000000000000000001','c71879b2000000000000000000000001').replace('2026-09-12T02:23:07.032Z',created).replace(old_ruling.replace('run7','run8'),ruling).replace('w71879-149053-validation-','w71879-149488-validation-');(p/'deployment.py').write_text(s)
(p/'run.py').write_text((old/'run.py').read_text().replace('w71879-run7','w71879-run8'))
(p/'operator-prepare.sh').write_text((old/'operator-prepare.sh').read_text().replace('run7','run8').replace('prepared-149053/target_posture.py','prepared-149488/target_posture.py'))
for name in ('test_manifest_timestamp.py','test_report_instructions.py','test_observed_status.py','offline_fixture.py','verify_offline.py'):
 s=(old/name).read_text().replace('run7','run8').replace('w71879-149053-','w71879-149488-').replace('2026-09-12T02:23:07.032Z',created);(p/name).write_text(s)
(p/'test_early_failure.py').write_text((old/'test_early_failure.py').read_text().replace(".replace(INCARNATION, 'w71879-run7')",".replace(INCARNATION, 'w71879-run8')"))
# Preserve accepted image IDs; offline schema inputs name those same images without selecting them.
(p/'offline-images.json').write_bytes((old/'candidate-images.json').read_bytes())
for f in (p/'tasks').glob('*.json'):
 d=json.loads(f.read_text());d['task_id']=d['task_id'].replace('run7','run8');f.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
for f in (p/'policies').glob('*.json'):
 d=json.loads(f.read_text().replace('w71879-run7','w71879-run8'))
 if f.stem=='policy':d['ruling']=ruling
 f.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
for name in ('FINDING.md','PLAN.md'):(p/'record-snapshot'/name).write_bytes((r/name).read_bytes())
helpers={n:'sha256:'+hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ('run.py','deployment.py','target_posture.py','failure_observation.py')};(p/'runner-helpers.json').write_text(json.dumps(helpers,indent=2,sort_keys=True)+'\n')
# Rebase only the four copied packaging cases. Preserve their bounded equality assertions.
s=(old/'test_run7_preparation.py').read_text()
s=s.replace("PRIOR = HERE.parent / 'prepared-148870'","PRIOR = HERE.parent / 'prepared-149053'")
s=s.replace("CREATED = '2026-09-12T02:23:07.032Z'", "CREATED = '"+created+"'")
s=s.replace("RULING = '"+old_ruling+"'", "RULING = '"+ruling+"'")
# Simultaneous tokens ensure old identity comparisons advance one run only.
replacements={'run6':'run7','run7':'run8','Run7':'Run8','c71879b0000000000000000000000001':'c71879b1000000000000000000000001','c71879b1000000000000000000000001':'c71879b2000000000000000000000001','c71879b0':'c71879b1','c71879b1':'c71879b2','w71879-149053-public-bootstrap-':'w71879-149488-public-bootstrap-'}
# The already-new ruling must not be token-advanced (contains run8 only).
s=re.sub('|'.join(re.escape(x) for x in sorted(replacements,key=len,reverse=True)),lambda m:replacements[m[0]],s)
s=s.replace(".replace('2026-09-11T19:51:48.071Z', CREATED)",".replace('2026-09-12T02:23:07.032Z', CREATED)")
s=s.replace(".replace('M141636/return146894; run8 preparation authorized; model execution not authorized', RULING)",".replace('"+old_ruling.replace('run7','run8')+"', RULING)")
s=s.replace(".replace('w71879-146897-validation-', 'w71879-149053-validation-')",".replace('w71879-149053-validation-', 'w71879-149488-validation-')")
s=s.replace(".replace('prepared-146897/target_posture.py', 'prepared-149053/target_posture.py')",".replace('prepared-149053/target_posture.py', 'prepared-149488/target_posture.py')")
(p/'test_run8_preparation.py').write_text(s)
# Preserve minimal safe published run7 evidence without touching credentials or raw provider streams.
for name in ('run-result.json','first-failure.json','failure-diagnostic.json','samples.jsonl'):
 src=Path('/home/sl/.local/state/baton/v12/w71879-run7/evidence')/name
 assert src.is_file() and not src.is_symlink()
 (e/('run7-'+name)).write_bytes(src.read_bytes())
print(json.dumps({'created':created,'helpers':helpers,'fresh_run8_absent':not Path('/home/sl/.local/state/baton/v12/w71879-run8').exists()},indent=2))
