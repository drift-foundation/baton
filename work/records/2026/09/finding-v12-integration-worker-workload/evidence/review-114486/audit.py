"""Retain candidate and reconcile existing logs; no suite or Git mutation."""
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
RECORD = HERE.parents[1]
author = json.loads((RECORD / 'evidence/implementation-114241/audit.json').read_text())
expected = dict(author['delivered'])
expected.update({k: v for k, v in author['unchanged_this_claim'].items() if k != 'note'})
result = {'claim': 114486, 'at': datetime.now(timezone.utc).isoformat(), 'paths': {}}
for name, claimed in expected.items():
    payload = (REPO / name).read_bytes()
    output = HERE / 'candidate' / name
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    measured = hashlib.sha256(payload).hexdigest()
    result['paths'][name] = {'sha256': measured, 'matches_author': measured == claimed}
    prior = RECORD / 'evidence/review-114048/candidate' / name
    if prior.exists():
        delta = ''.join(difflib.unified_diff(prior.read_text().splitlines(True), payload.decode().splitlines(True), fromfile='review-114048/' + name, tofile='review-114486/' + name))
        output.with_suffix(output.suffix + '.diff').write_text(delta)

def methods(path):
    tree = ast.parse(path.read_text())
    return {c.name + '.' + m.name: ast.dump(m, include_attributes=False)
            for c in tree.body if isinstance(c, ast.ClassDef)
            for m in c.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name.startswith('test_')}

name = 'v12/python/tests/manager/test_integration_worker.py'
old = methods(RECORD / 'evidence/review-114048/candidate' / name)
new = methods(REPO / name)
result['tests'] = {'old': len(old), 'new': len(new),
                   'changed': sorted(k for k in old.keys() & new.keys() if old[k] != new[k]),
                   'removed': sorted(old.keys() - new.keys()), 'added': sorted(new.keys() - old.keys())}
logs = {
    'corrected-gate.txt': Path('/tmp/w110935-corrected-gate.txt'),
    'final-gate.txt': Path('/tmp/w110935-final-gate.txt'),
    'focused-author.txt': RECORD / 'evidence/implementation-114241/focused.txt',
    'prior-gate-dossier.txt': RECORD / 'evidence/review-114048/gate-dossier.txt',
    'prior-gate-final.txt': RECORD / 'evidence/review-114048/gate-final.txt'}
result['logs'] = {}
for name, source in logs.items():
    payload = source.read_bytes()
    (HERE / name).write_bytes(payload)
    body = payload.decode()
    result['logs'][name] = {'source': str(source), 'sha256': hashlib.sha256(payload).hexdigest(),
                            'summary': re.findall(r'^(?:Ran \d+ tests.*|FAILED .*|OK)$', body, re.M),
                            'failures': re.findall(r'^(?:FAIL|ERROR): .*$', body, re.M)}
base = set(result['logs']['prior-gate-dossier.txt']['failures'])
for name in ('corrected-gate.txt', 'final-gate.txt'):
    failures = set(result['logs'][name]['failures'])
    result['logs'][name]['added_vs_prior_dossier'] = sorted(failures - base)
    result['logs'][name]['missing_vs_prior_dossier'] = sorted(base - failures)
(HERE / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
