"""Final independent custody and reviewed public-constructor checks; no execution."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys
import time

sys.dont_write_bytecode = True
REPO = Path('/home/sl/src/baton')
HERE = Path(__file__).resolve().parent
PROOF = HERE.parent.parent
sys.path.insert(0, str(REPO / 'v12/python/src'))
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    answer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(answer)
    return answer
reader = module('retained_reader', PROOF / 'evidence/run9-budget-150384/reconcile.py')
read = lambda path: reader.read(path, 16 * 1024 * 1024)
sha = lambda raw: 'sha256:' + hashlib.sha256(raw).hexdigest()
start = time.monotonic()
manifest_path = PROOF / 'evidence/run10-freeze-152932/candidate-manifest.json'
manifest_hash = 'sha256:4299b6db0997fdf26ceeaeb32fa3ebc88dbc73d8b43d8fab7dca4b6c2e484f21'
assert sha(read(manifest_path)) == manifest_hash
manifest = json.loads(read(manifest_path))
files = manifest['files']
assert len(files) == 358
journals = {str(PROOF.relative_to(REPO) / name) for name in ('FINDING.md', 'PLAN.md', 'PROGRESS.md')}
assert not journals.intersection(files)
for name, binding in files.items():
    rel = Path(name)
    assert not rel.is_absolute() and '..' not in rel.parts
    raw = read(REPO / rel)
    assert sha(raw) == binding['sha256'] and len(raw) == binding['bytes'], name
    if 'mode' in binding:
        assert oct((REPO / rel).stat().st_mode & 0o7777) == binding['mode'], name
for name in manifest['accepted_absences']:
    assert not os.path.lexists(REPO / name), name
package = PROOF / 'prepared-152826'
for name, expected in manifest['five_helpers'].items():
    assert files[str((package / name).relative_to(REPO))]['sha256'] == expected
# This previously read checker uses public document construction and Git reads;
# its check() returns facts, writing only its own new temporary reconstruction.
# Its historical evidence-writing __main__ is never invoked.
checks = module('reviewed_input_checker', PROOF / 'evidence/run10-freeze-152932/check_inputs.py')
answer = checks.check()
assert len(answer['actual_documents']) == 33
assert answer['runtime_profile_digest'] == 'sha256:34ff1ebdcec8ddc607109be4d6600595e650360b6d3773b95cf124ebef3b1f69'
for name, expected in answer['actual_documents'].items():
    assert files[str((package / 'frozen-config' / name).relative_to(REPO))]['sha256'] == expected
source = json.loads(read(PROOF / 'evidence/run10-freeze-152932/source-provenance.json'))
counts = {}
for name, rows in source['source_bindings'].items():
    counts[name] = len(rows)
    for row in rows:
        path = REPO / row['path']
        if row.get('absent'):
            assert not os.path.lexists(path)
        else:
            assert sha(read(path)) == row['current_sha256'], row['path']
assert counts == {'provider_chain': 45, 'source_requirements': 4, 'current_observation_sources': 3}
report = {'review_claim': 152976, 'manifest_sha256': manifest_hash, 'candidate_files': 358,
          'continuing_journals_excluded': True, 'accepted_absences_verified': manifest['accepted_absences'],
          'source_group_counts': counts, 'reviewed_constructor_check': answer,
          'seconds': time.monotonic() - start}
(HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
cost = {'current_listed_seconds': report['seconds'], 'cumulative_listed_preparation_seconds': 111.522959913941 + report['seconds'],
        'nine_failed_runtime_walls_seconds': 2002.0388815780316,
        'uncertainty': 'Retain prior untimed/failed-utility/CLI/static/host/operator/billing/rounding uncertainty. Host validation and prior suite costs not charged twice. No store, credential payload, image build or live model execution.'}
(HERE / 'spending.json').write_text(json.dumps(cost, indent=2) + '\n')
print(json.dumps({'files':358, 'actual_inputs':33, 'source_groups':counts, 'retained':answer['retained_reconstruction'], 'spending':cost}, indent=2))
