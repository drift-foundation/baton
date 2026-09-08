"""Independent candidate, baseline and assertion audit; no notifier execution."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
RECORD = HERE.parents[1]
supplied = RECORD / 'evidence/correction-2026-09-08'
prior = RECORD / 'evidence/review-114371/candidate'
manifest = json.loads((supplied / 'manifest.json').read_text())
result = {'claim': 114925, 'at': datetime.now(timezone.utc).isoformat(), 'paths': {}}
for name, hashes in manifest.items():
    data = (REPO / name).read_bytes()
    baseline = (prior / name).read_bytes()
    out = HERE / 'candidate' / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    measured = hashlib.sha256(data).hexdigest()
    result['paths'][name] = {'sha256': measured, 'matches_manifest': measured == hashes['candidate_sha256'], 'matches_snapshot': data == (supplied / 'candidate' / name).read_bytes(), 'baseline_matches': hashlib.sha256(baseline).hexdigest() == hashes['baseline_sha256']}

def methods(path):
    return {c.name + '.' + m.name: ast.dump(m, include_attributes=False)
            for c in ast.parse(path.read_text()).body if isinstance(c, ast.ClassDef)
            for m in c.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')}

name = 'tools/test_codex_copilot_notifier.py'
old, new = methods(prior / name), methods(HERE / 'candidate' / name)
result['tests'] = {'prior': len(old), 'current': len(new), 'changed': sorted(k for k in old.keys() & new.keys() if old[k] != new[k]), 'removed': sorted(old.keys() - new.keys()), 'added': sorted(new.keys() - old.keys())}
data = (supplied / 'unittest.txt').read_bytes()
(HERE / 'unittest-author.txt').write_bytes(data)
result['author_verification'] = {'sha256': hashlib.sha256(data).hexdigest(), 'summary': re.findall(r'^(?:Ran \d+ tests.*|FAILED .*|OK)$', data.decode(), re.M)}
result['canonical_source_hashes'] = {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in ('src/baton_work/projection.py', 'src/baton_work/transitions.py')}
(HERE / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
