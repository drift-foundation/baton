"""Verify the missing-input finding and available custody; no render or repair."""
from pathlib import Path
import hashlib, json, os, stat, sys, time
ROOT = Path('/home/sl/src/baton')
PROOF = ROOT / 'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
PACKAGE = PROOF / 'prepared-149053'
OUT = Path(__file__).resolve().parent
start = time.monotonic()
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
manifest = PROOF / 'evidence/run7-freeze-149249/candidate-manifest.json'
assert sha(manifest) == 'dfe1c346ddf07c2b6bcd359a028e2a0f2eb4b6f61f10a97a21d0c707044d905b'
given = json.loads(manifest.read_text())
for name, row in given['files'].items():
    assert not any(part in name for part in ('.sqlite', '.db', 'credentials.json')), name
    path = ROOT / name
    facts = path.lstat()
    assert stat.S_ISREG(facts.st_mode), name
    assert sha(path) == row['sha256'].removeprefix('sha256:'), name
    assert facts.st_size == row['bytes'] and oct(stat.S_IMODE(facts.st_mode)) == row['mode'], name
for name in given['expected_absent_at_observation']:
    assert not os.path.lexists(ROOT / name), name
assert not os.path.lexists(PACKAGE / 'frozen-config')
assert sha(PACKAGE / 'deployment.py') == 'f0cbf8e54cbc9b62a0019c4c2fa9a9e96ca7cd59b4cc592c536db7cd0b97bc9b'
sys.path.insert(0, str(PROOF / 'evidence/run7-freeze-149249'))
from check_inputs import check_images
images = check_images()  # Read-only comparison of owner helper reports and bound retained metadata.
actual_images = [json.loads(line) for line in (OUT / 'current-images.jsonl').read_text().splitlines()]
actual_containers = [json.loads(line) for line in (OUT / 'current-containers.jsonl').read_text().splitlines()]
for kind in ('provider', 'integration'):
    retained = json.loads((PACKAGE / 'image-build' / (kind + '.inspect.json')).read_text())
    current = next(row for row in actual_images if row['Id'] == images[kind]['id'])
    for key in current:
        assert current[key] == retained[key], (kind, key)
    container = next(row for row in actual_containers if row['Id'] == images[kind]['inspection_container'])
    held = json.loads((PACKAGE / 'image-build' / (kind + '.container.inspect.json')).read_text())
    assert container['Image'] == current['Id'] and container['State'] == held['State']
    assert container['State']['Status'] == 'created' and not container['State']['Running'] and container['State']['Pid'] == 0
    assert container['readonly'] and container['network'] == 'none' and not container['mounts']
validation = json.loads((PACKAGE / 'validation.json').read_text())
temporary = Path(validation['temporary_path_retained'])
for key, name in [('configuration', 'stage-execution.json'), ('submission', 'submission.json')]:
    assert sha(temporary / name) == validation['documents'][key].removeprefix('sha256:')
run = Path('/home/sl/.local/state/baton/v12/w71879-run7')
for name in ('authority.sqlite3','integration.sqlite3','jobs.sqlite3','control.sqlite3','state','storage','launch','credentials','evidence'):
    assert not os.path.lexists(run / name), name
result = {'claim':149299,'available_files_verified':len(given['files']),'images':images,'actual_rendered_path':str(PACKAGE / 'frozen-config'),'actual_rendered_path_absent':True,'actual_rendered_file_count':0,'freeze_complete':False,'temporary_validation_digests_match':True,'seconds':time.monotonic()-start,'scope':'Read-only review of absent actual inputs and available evidence. No store/credential reads, rendering, reconstruction, Docker copy/build/start, host repair or model execution.'}
(OUT / 'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
