"""Independent run7 preparation custody checks; no engine or host mutation."""
from pathlib import Path
import ast, hashlib, json, os, stat, time
ROOT = Path('/home/sl/src/baton')
PROOF = ROOT / 'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
PACKAGE = PROOF / 'prepared-149053'
OUT = Path(__file__).resolve().parent
start = time.monotonic()
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def manifest(relative, expected):
    path = PROOF / relative
    assert sha(path) == expected, relative
    files = json.loads(path.read_text())['files']
    for name, row in files.items():
        path = ROOT / name
        facts = path.lstat()
        assert stat.S_ISREG(facts.st_mode), name
        assert sha(path) == row['sha256'].removeprefix('sha256:'), name
        assert facts.st_size == row['bytes'] and oct(stat.S_IMODE(facts.st_mode)) == row['mode'], name
    return len(files)
counts = {}
for path, digest in [
    ('evidence/image-preparation-149053/candidate-manifest.json', 'fa2f9526995166f66c195704b71bfb4504c3713d6820362565641b88246c9037'),
    ('evidence/diagnostic-148870/candidate-manifest.json', '0c13a9034aef59636214749876bb83960c18a457dc79a992cf1c6b2c15d0028f'),
    ('prepared-147109/candidate-manifest.json', '94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2'),
    ('evidence/run6-freeze-146988/candidate-manifest.json', '87a320bdee36cfdca8e7d18372e65ff26eeb314eeda948db3402692b328dd0a9')]:
    counts[path] = manifest(path, digest)
old = json.loads((PROOF / 'prepared-146897/evidence/provenance.json').read_text())
for name, row in old['provider_chain'].items():
    if row.get('expected_absence_matches'):
        assert not os.path.lexists(ROOT / name), name
    else:
        assert sha(ROOT / name) == row['sha256'].removeprefix('sha256:'), name
bindings = {}
for group in ('source_requirements', 'current_observation_sources'):
    for name, expected in old[group].items():
        assert sha(ROOT / name) == expected.removeprefix('sha256:'), name
        bindings[name] = expected
context = PACKAGE / 'image-context'
rows = json.loads((PACKAGE / 'image-context-manifest.json').read_text())
found = {str(path.relative_to(context)) for path in context.rglob('*') if path.is_file() or path.is_symlink()}
assert found == set(rows) | {'Dockerfile.provider'}
for name in found:
    actual = context / name
    prior = PROOF / 'prepared-141676/image-context' / name
    assert stat.S_ISREG(actual.lstat().st_mode) and actual.stat().st_mode == prior.stat().st_mode, name
    if name != 'worker/claude_agent.py':
        assert actual.read_bytes() == prior.read_bytes(), name
    else:
        assert sha(actual) == '489399897c3f0ae94f06be9da47adde3f05210fa0ecfd7faad295daf6accfe2a'
    if name in rows:
        assert sha(actual) == rows[name]['sha256'].removeprefix('sha256:') and actual.stat().st_size == rows[name]['bytes']
helpers = json.loads((PACKAGE / 'runner-helpers.json').read_text())
assert set(helpers) == {'run.py','deployment.py','target_posture.py','failure_observation.py'}
for name, expected in helpers.items():
    assert sha(PACKAGE / name) == expected.removeprefix('sha256:')
for name in ('failure_observation.py', 'target_posture.py', 'test_stats_observation.py', 'test_provider_detail.py'):
    assert (PACKAGE / name).read_bytes() == (PROOF / 'prepared-148870' / name).read_bytes()
for path in PACKAGE.glob('*.py'):
    ast.parse(path.read_text(), filename=str(path))
assert not os.path.lexists('/home/sl/.local/state/baton/v12/w71879-run7')
for name in ('candidate-images.json','selected-images.json','execution-review.json','validation.json','frozen-config','image-build'):
    assert not os.path.lexists(PACKAGE / name), name
result = {'claim':149156,'manifests':counts,'provider_chain_entries':len(old['provider_chain']),'composition_observer_bindings':len(bindings),'context_files':len(found),'helpers':helpers,'actual_run_and_preparation_outputs_absent':True,'seconds':time.monotonic()-start,'scope':'Custody, continuity and syntax only; no Docker mutation, host/Git preparation, runtime or credential access.'}
(OUT / 'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
