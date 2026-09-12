from pathlib import Path
import json, hashlib, shutil, stat
r=Path('/home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof')
old=r/'prepared-148870'; p=r/'prepared-149053'; p.mkdir()
created=Path('/tmp/w71879-149053-created.txt').read_text()
ruling='M141636/return149049; run7 image and package preparation authorized; model execution not authorized'
for f in old.rglob('*'):
    if not f.is_file() or '__pycache__' in f.parts or f.name=='candidate-manifest.json':continue
    dest=p/f.relative_to(old)
    if f.name=='candidate-images.json':dest=p/'offline-images.json'
    if f.name=='test_run6_preparation.py':continue
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes())
# The bounded execution helpers change identity only. Detail/posture byte-identical.
s=(old/'deployment.py').read_text().replace('run6','run7').replace('c71879b0000000000000000000000001','c71879b1000000000000000000000001').replace('2026-09-11T19:51:48.071Z',created).replace('M141636/return146894; run7 preparation authorized; model execution not authorized',ruling).replace('w71879-146897-validation-','w71879-149053-validation-')
(p/'deployment.py').write_text(s)
(p/'run.py').write_text((old/'run.py').read_text().replace('w71879-run6','w71879-run7'))
(p/'operator-prepare.sh').write_text((old/'operator-prepare.sh').read_text().replace('run6','run7').replace('prepared-146897/target_posture.py','prepared-149053/target_posture.py'))
for name in ('test_manifest_timestamp.py','test_report_instructions.py','test_observed_status.py','offline_fixture.py','verify_offline.py'):
    s=(old/name).read_text().replace('run6','run7').replace('w71879-146897-','w71879-149053-').replace('2026-09-11T19:51:48.071Z',created).replace("'candidate-images.json'","'offline-images.json'")
    (p/name).write_text(s)
# Historical replay stays genuine; bind its UUID/Works explicitly, separately from fresh runner.
s=(old/'test_early_failure.py').read_text().replace("INCARNATION = 'w71879-run6'", "INCARNATION = 'w71879-run6'\nHISTORICAL_UUID = 'c71879b0000000000000000000000001'\nHISTORICAL_WORKS = {name: 'c71879b0-W' + str(i) for i, name in enumerate(('a', 'b', 'verification', 'review', 'approval'), 1)}").replace('authority_uuid=runner.UUID, incarnation=INCARNATION, works=runner.WORKS','authority_uuid=HISTORICAL_UUID, incarnation=INCARNATION, works=HISTORICAL_WORKS')
(p/'test_early_failure.py').write_text(s)
for f in (p/'tasks').glob('*.json'):
    d=json.loads(f.read_text());d['task_id']=d['task_id'].replace('run6','run7');f.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
for f in (p/'policies').glob('*.json'):
    d=json.loads(f.read_text().replace('w71879-run6','w71879-run7'))
    if f.stem=='policy':d['ruling']=ruling
    f.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
for name in ('FINDING.md','PLAN.md'):(p/'record-snapshot'/name).write_bytes((r/name).read_bytes())
# Immutable accepted image context; only reviewed adapter changes.
shutil.copytree(r/'prepared-141676/image-context',p/'image-context')
manifest=json.loads((r/'prepared-141676/image-context-manifest.json').read_text())
for name,entry in manifest.items():
    data=(p/'image-context'/name).read_bytes()
    assert 'sha256:'+hashlib.sha256(data).hexdigest()==entry['sha256'] and len(data)==entry['bytes'],name
adapter=Path('/home/sl/src/baton/v12/worker/claude_agent.py').read_bytes()
assert hashlib.sha256(adapter).hexdigest()=='489399897c3f0ae94f06be9da47adde3f05210fa0ecfd7faad295daf6accfe2a'
(p/'image-context/worker/claude_agent.py').write_bytes(adapter)
manifest['worker/claude_agent.py']={'sha256':'sha256:'+hashlib.sha256(adapter).hexdigest(),'bytes':len(adapter)}
(p/'image-context-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
provenance={'version':'2.1.247','owner_copy_events':[148760,148865],'review':'review-2026-09-12T02-08-32Z.md','source_container':'a2b00b62bdbb3f413b6e4e9539cf71190b237430a8856367567315b4f98ef5af','source_image':'sha256:26cdfe7df693d3cfad0190e879e93ba9f3fea2086ecb5c7f1f4c2fe598aced99','immutable_base':'sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4','files':{}}
for name,path,hash_,size,mode in [
('package.json','/tmp/w71879-148686-provider-package.json','204e690591b935992fff95f6d2af6aeac86be074719da7900f1c4e4056f37efe',1476,0o644),
('install.cjs','/tmp/w71879-148768-provider-install.cjs','5cbab1670597f492cd4eeb946f3c344ebcb1fbd43c623ba192c9b33744461b85',7196,0o644),
('cli-wrapper.cjs','/tmp/w71879-148768-provider-cli-wrapper.cjs','61ad63033d9c8155d5e60a29f45dc4665afa07631c0b108e62cc83bf45ba490e',4997,0o644),
('bin/claude.exe','/tmp/w71879-148768-provider-claude.exe','5fb321bf417ffc5cd4e3f36e7c9c7e029bf47aaa36d5621db979fcc5e6eabe15',250162696,0o755)]:
    f=Path(path);s=f.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size==size and stat.S_IMODE(s.st_mode)==mode
    with f.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==hash_
    provenance['files']['/usr/local/lib/node_modules/@anthropic-ai/claude-code/'+name]={'sha256':'sha256:'+hash_,'bytes':size,'mode':mode,'owner_copy':path}
(p/'provider-installation.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
print(p)
print('Fresh external root absent:',not Path('/home/sl/.local/state/baton/v12/w71879-run7').exists())
