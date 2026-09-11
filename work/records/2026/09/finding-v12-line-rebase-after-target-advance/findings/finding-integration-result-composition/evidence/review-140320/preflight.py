import difflib
import hashlib
import json
from pathlib import Path
import shutil
import stat
import time

started = time.monotonic()
root = Path('/home/sl/src/baton')
record = root / 'work/records/2026/09/finding-v12-line-rebase-after-target-advance/findings/finding-integration-result-composition'
out = record / 'evidence/review-140320'
prior = json.loads((record / 'evidence/dispatch-140210/result.json').read_text())
author = json.loads((record / 'evidence/result-140229.json').read_text())
expected = dict(prior['accepted_union'])
expected.update({p: {k: v[k] for k in ('sha256', 'bytes', 'mode')} for p, v in author['r_paths'].items()})
actual, errors = {}, []
for name, wanted in expected.items():
    path = root / name
    if wanted.get('state') == 'absent':
        value = {'state': 'absent'} if not path.exists() and not path.is_symlink() else {'state': 'present'}
    else:
        data = path.read_bytes()
        value = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'mode': oct(stat.S_IMODE(path.stat().st_mode))}
        if path.is_symlink() or not path.is_file():
            errors.append(name + ': type mismatch')
    actual[name] = value
    if wanted != value:
        errors.append(name + ': manifest mismatch')
diff = []
for name in author['r_paths']:
    target = out / 'candidate' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / name, target)
    base = record / 'evidence/dispatch-140210/base' / name
    diff.extend(difflib.unified_diff(base.read_text().splitlines(True), target.read_text().splitlines(True), fromfile='candidate139082/' + name, tofile='candidate140229/' + name))
(out / 'candidate.diff').write_text(''.join(diff))
ledger = json.loads((record / 'evidence/ledger-137012.json').read_text())
shutil.copyfile(record / 'evidence/ledger-137012.json', out / 'author-ledger.json')
for row in ledger['runs']:
    shutil.copyfile(root / row['log'], out / Path(row['log']).name)
result = {'claim': 140320, 'candidate': 140229, 'accepted_union': actual, 'r_paths': author['r_paths'], 'errors': errors, 'author_measured_seconds': sum(row['elapsed_seconds'] for row in ledger['runs']), 'author_runs': len(ledger['runs']), 'author_nonzero_steps': [row['step'] for row in ledger['runs'] if row['exit'] != 0], 'review_prior_charge_seconds': 8.70589725899772, 'preflight_measured_seconds': time.monotonic() - started, 'preflight_charge_seconds': 0.15, 'review_cumulative_charge_seconds': 8.85589725899772, 'review_ceiling_seconds': 15, 'author_ceiling_seconds': 85, 'unmeasured_history': 'All prior disclosed reads, searches, edits, syntax checks and manifest activity retained without reset; current dossier/read/diff inspection also disclosed.'}
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('accepted_union', 'r_paths')}, indent=2))
assert not errors, errors
