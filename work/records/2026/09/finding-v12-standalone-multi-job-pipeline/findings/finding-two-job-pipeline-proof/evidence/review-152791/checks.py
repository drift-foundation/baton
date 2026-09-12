"""Independent custody and supplied offline regressions; no live state access."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PROOF = HERE.parent.parent
REPO = Path('/home/sl/src/baton')
sys.path.insert(0, str(REPO / 'v12/python/src'))
spec = importlib.util.spec_from_file_location('retained_reader', PROOF / 'evidence/run9-budget-150384/reconcile.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
read = lambda path: reader.read(path, 16 * 1024 * 1024)
sha = lambda raw: 'sha256:' + hashlib.sha256(raw).hexdigest()
began = time.monotonic()
manifest = PROOF / 'evidence/accounting-152750/candidate-manifest.json'
assert sha(read(manifest)) == 'sha256:9ec9be1113ed88f170e038779ce10057714690d591e847045f804cdacd7aafc1'
journals = {str(PROOF.relative_to(REPO) / name) for name in ('FINDING.md', 'PLAN.md', 'PROGRESS.md')}
counts = {}
for name, expected in [('accounting-152750', 89), ('accounting-152563', 92), ('accounting-150501', 75), ('run9-freeze-150125', 198), ('run9-budget-150384', 19)]:
    files = json.loads(read(PROOF / 'evidence' / name / 'candidate-manifest.json'))['files']
    count = 0
    for locator, binding in files.items():
        if name == 'accounting-152563' and locator in journals:
            continue  # Exactly the three continuing journals, with explicit subsequent history.
        rel = Path(locator)
        assert not rel.is_absolute() and '..' not in rel.parts
        raw = read(REPO / rel)
        assert sha(raw) == binding['sha256'] and len(raw) == binding['bytes'], locator
        if 'mode' in binding:
            assert oct((REPO / rel).stat().st_mode & 0o7777) == binding['mode'], locator
        if name == 'accounting-152750' and locator in journals:
            (HERE / ('candidate-' + rel.name)).write_bytes(raw)
        count += 1
    assert count == expected, (name, count)
    counts[name] = count
old, new = PROOF / 'prepared-152563', PROOF / 'prepared-152750'
old_files = {str(path.relative_to(old)) for path in old.rglob('*') if path.is_file()}
new_files = {str(path.relative_to(new)) for path in new.rglob('*') if path.is_file()}
assert old_files == new_files
changed = sorted(name for name in old_files if read(old / name) != read(new / name))
assert changed == sorted(['README.md', 'accounting.py', 'run.py', 'runner-helpers.json', 'test_joined_judges.py', 'test_stats_observation.py', 'verify_offline.py']), changed
for name, expected in json.loads(read(new / 'runner-helpers.json')).items():
    assert sha(read(new / name)) == expected, name
for name in ('selected-images.json', 'execution-review.json'):
    assert not os.path.lexists(new / name)
host = json.loads(read(PROOF / 'evidence/accounting-152750/host-observation.json'))
report = {'claim': 152791, 'verified_files': counts, 'previous_manifest_exclusions': sorted(journals),
          'current_journals_captured_before_review_append': True, 'changed_package_files': changed,
          'helper_bindings_verified': 5, 'execution_markers_absent': True, 'host_evidence': host,
          'seconds': time.monotonic() - began}
(HERE / 'custody.json').write_text(json.dumps(report, indent=2) + '\n')
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
start = time.monotonic()
done = subprocess.run([sys.executable, '-B', str(new / 'verify_offline.py')], cwd=REPO, env=env, capture_output=True, text=True, timeout=40)
check = {'exit': done.returncode, 'seconds': time.monotonic() - start}
(HERE / 'proof.txt').write_text(done.stdout + done.stderr)
(HERE / 'checks.json').write_text(json.dumps(check, indent=2) + '\n')
cost = {'current_listed_seconds': report['seconds'] + check['seconds'],
        'cumulative_listed_preparation_seconds': 94.168591629989 + report['seconds'] + check['seconds'],
        'nine_failed_runtime_walls_seconds': 2002.0388815780316,
        'uncertainty': 'Prior untimed/CLI/static/host/operator/billing/rounding uncertainty retained; inner suite timing is not added twice; no repeated product suite or host probe.'}
(HERE / 'spending.json').write_text(json.dumps(cost, indent=2) + '\n')
print(json.dumps({'custody': report, 'check': check, 'spending': cost}, indent=2))
sys.exit(done.returncode)
