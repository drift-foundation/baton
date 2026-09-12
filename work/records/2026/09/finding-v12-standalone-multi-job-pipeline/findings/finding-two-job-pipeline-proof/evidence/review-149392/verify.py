"""Independent final input custody and current metadata verification; no execution."""
from pathlib import Path
import hashlib, json, os, stat, time
ROOT = Path('/home/sl/src/baton')
PROOF = ROOT / 'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
PACKAGE = PROOF / 'prepared-149053'
OUT = Path(__file__).resolve().parent
start = time.monotonic()
def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
manifest = PROOF / 'evidence/run7-freeze-149356/candidate-manifest.json'
assert sha(manifest) == 'sha256:6e95a68815f0d1c353dc7f78836dc762132176a92f17f28ac0b39b6b88052224'
given = json.loads(manifest.read_text())
for name, row in given['files'].items():
    assert not any(part in name for part in ('.sqlite', '.db', 'credentials.json')), name
    path = ROOT / name
    facts = path.lstat()
    assert stat.S_ISREG(facts.st_mode), name
    assert sha(path) == 'sha256:' + row['sha256'].removeprefix('sha256:'), name
    assert facts.st_size == row['bytes'] and oct(stat.S_IMODE(facts.st_mode)) == row['mode'], name
reconstruction = json.loads((OUT / 'post-render.json').read_text())
config = PACKAGE / 'frozen-config'
names = {str(path.relative_to(config)) for path in config.rglob('*') if path.is_file() or path.is_symlink()}
assert len(names) == 33 and names == set(reconstruction['actual_documents'])
for name in names:
    assert sha(config / name) == reconstruction['actual_documents'][name]
assert reconstruction['actual_configuration'] == 'sha256:bebe5ae64ade6c67857fba14fc6cf9145401157ed3e3b3f479aa16375b4e43d2'
assert reconstruction['actual_submission'] == 'sha256:1486585695d9ca9c5dd3bf8da684ca7417761dbe3eb4bb207c1e9ffcfee52937'
images = json.loads((PACKAGE / 'candidate-images.json').read_text())
assert images == json.loads((config / 'runtime-profile.json').read_text())['image_variants']
build = json.loads((PACKAGE / 'image-build/result.json').read_text())
assert images == build['images'] and build['complete'] and not build['selected']
current_images = [json.loads(line) for line in (OUT / 'current-images.jsonl').read_text().splitlines()]
current_containers = [json.loads(line) for line in (OUT / 'current-containers.jsonl').read_text().splitlines()]
for kind, image in images.items():
    retained = json.loads((PACKAGE / 'image-build' / (kind + '.inspect.json')).read_text())
    current = next(row for row in current_images if row['Id'] == image)
    for key in current:
        assert current[key] == retained[key], (kind, key)
    container = next(row for row in current_containers if row['Id'] == build['inspection_containers'][kind])
    held = json.loads((PACKAGE / 'image-build' / (kind + '.container.inspect.json')).read_text())
    assert container['Image'] == image and container['State'] == held['State']
    assert container['State']['Status'] == 'created' and container['State']['Pid'] == 0 and not container['State']['Running']
    assert container['readonly'] and container['network'] == 'none' and not container['mounts']
helpers = json.loads((PACKAGE / 'runner-helpers.json').read_text())
for name, expected in helpers.items():
    assert sha(PACKAGE / name) == expected
    assert str((PACKAGE / name).relative_to(ROOT)) in given['files']
target = Path('/home/sl/.local/state/baton/v12/w71879-run7/target')
for relative in ('demo/greeting.py','demo/units.py','tests/test_greeting.py'):
    assert stat.S_IMODE((target / relative).stat().st_mode) == 0o644
for relative in ('','demo','tests'):
    assert stat.S_IMODE((target / relative).stat().st_mode) == 0o2775
for name in ('selected-images.json','execution-review.json'):
    assert not os.path.lexists(PACKAGE / name), name
result = {'claim':149392,'verified_candidate_files':len(given['files']),'candidate_manifest':sha(manifest),'actual_inputs':len(names),'images':images,'helpers':helpers,'current_inspection_containers_never_started':True,'actual_target_modes_match':True,'real_host_uid_gid_basis':'Owner149242 accepted preparation attestation; managed projection is not independent actual UID/GID proof.','seconds':time.monotonic()-start,'prior_checker_claim':reconstruction['claim'],'independent_reconstruction':reconstruction['retained_reconstruction'],'model_execution_authorized':False}
(OUT / 'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
