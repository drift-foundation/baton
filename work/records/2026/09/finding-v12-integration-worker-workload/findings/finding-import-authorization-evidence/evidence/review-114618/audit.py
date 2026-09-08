"""Retain exact source and completed tests without rerunning a suite."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[8]
RECORD = HERE.parents[1]
expected = {
    'v12/worker/integration_contract.py': '2f8b42eb4f82949e97c2ef660d6fa5d39384eaeb6d5688f3bb90be715175fcf2',
    'v12/python/tools/integration_bundle.py': 'c7a60dcc1fc1df989153c3368aeac4677950e42c1473088c65af998f43f63058',
    'v12/python/tests/tools/test_integration_bundle.py': 'e2f175173bed6bec4887f982d2f54b9fa29b7b7b375192db0539cc030587ac31'}
out = {'claim': 114618, 'paths': {}, 'logs': {}}
for name, claimed in expected.items():
    payload = (REPO / name).read_bytes()
    dest = HERE / 'candidate' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    measured = hashlib.sha256(payload).hexdigest()
    out['paths'][name] = {'sha256': measured, 'matches_author': measured == claimed}
    prior = RECORD / 'evidence/review-114231/candidate' / name
    delta = ''.join(difflib.unified_diff(prior.read_text().splitlines(True), payload.decode().splitlines(True), fromfile='review114231/' + name, tofile='review114618/' + name))
    (HERE / (Path(name).name + '.diff')).write_text(delta)

def methods(path):
    tree = ast.parse(path.read_text())
    return {c.name + '.' + m.name: ast.dump(m, include_attributes=False)
            for c in tree.body if isinstance(c, ast.ClassDef)
            for m in c.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')}

name = 'v12/python/tests/tools/test_integration_bundle.py'
old = methods(RECORD / 'evidence/review-114231/candidate' / name)
new = methods(REPO / name)
out['tests'] = {'old': len(old), 'new': len(new), 'removed': sorted(old.keys() - new.keys()),
                'added': sorted(new.keys() - old.keys()),
                'changed': sorted(k for k in old.keys() & new.keys() if old[k] != new[k])}
logs = {'focused-author.txt': RECORD / 'evidence/implementation-114488/focused.txt',
        'gate-tmp.txt': Path('/tmp/w114085-gate.txt'),
        'gate-author.txt': RECORD / 'evidence/implementation-114488/source-gate.txt',
        'prior-parent-final.txt': RECORD.parents[1] / 'evidence/review-114486/final-gate.txt'}
for name, source in logs.items():
    payload = source.read_bytes()
    (HERE / name).write_bytes(payload)
    text = payload.decode()
    out['logs'][name] = {'sha256': hashlib.sha256(payload).hexdigest(),
                         'summary': re.findall(r'^(?:Ran \d+ tests.*|FAILED .*|OK)$', text, re.M),
                         'failures': re.findall(r'^(?:FAIL|ERROR): .*$', text, re.M)}
out['extra_broad_failure_identities'] = sorted(set(out['logs']['gate-tmp.txt']['failures']) - set(out['logs']['prior-parent-final.txt']['failures']))
(HERE / 'audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
