"""Snapshot the handed-back candidate and compare with the previous review."""
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
RECORD = HERE.parents[1]
REPO = HERE.parents[6]
prior = RECORD / 'evidence/review-114486'
names = json.loads((prior / 'audit.json').read_text())['paths']
result = {'claim': 114828, 'at': datetime.now(timezone.utc).isoformat(), 'paths': {}}
for name in names:
    data = (REPO / name).read_bytes()
    out = HERE / 'candidate' / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    old = (prior / 'candidate' / name).read_bytes()
    out.with_suffix(out.suffix + '.diff').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True), data.decode().splitlines(True), fromfile='review-114486/' + name, tofile='review-114828/' + name)))
    result['paths'][name] = {'sha256': hashlib.sha256(data).hexdigest(), 'changed': data != old}

def methods(path):
    return {c.name + '.' + m.name: ast.dump(m, include_attributes=False)
            for c in ast.parse(path.read_text()).body if isinstance(c, ast.ClassDef)
            for m in c.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')}

name = 'v12/python/tests/manager/test_integration_worker.py'
old, new = methods(prior / 'candidate' / name), methods(HERE / 'candidate' / name)
result['tests'] = {'old': len(old), 'new': len(new), 'changed': sorted(k for k in old.keys() & new.keys() if old[k] != new[k]), 'removed': sorted(old.keys() - new.keys()), 'added': sorted(new.keys() - old.keys())}
source = Path('/tmp/w110935-gate3.txt')
data = source.read_bytes()
(HERE / 'gate3.txt').write_bytes(data)
result['gate3'] = {'sha256': hashlib.sha256(data).hexdigest(), 'summary': re.findall(r'^(?:Ran \d+ tests.*|FAILED .*|OK)$', data.decode(), re.M), 'failures': re.findall(r'^(?:FAIL|ERROR): .*$', data.decode(), re.M)}
(HERE / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
