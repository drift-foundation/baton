"""Retain corrected child bytes and audit scheduled test changes; no suite."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[8]
RECORD = HERE.parents[1]
prior = RECORD / 'evidence/review-114618/candidate'
expected = {
    'v12/worker/integration_contract.py': '74f53b031f392a615141c1d2be6552989658b6f5b15b82cc9f16294a3ee5be92',
    'v12/python/tools/integration_bundle.py': 'c7a60dcc1fc1df989153c3368aeac4677950e42c1473088c65af998f43f63058',
    'v12/python/tests/tools/test_integration_bundle.py': 'af16d77052b94aa85c707966f673ac1b1cbb26eec013b709be76f704e391bd38'}
result = {'claim': 114869, 'paths': {}}
for name, claimed in expected.items():
    data = (REPO / name).read_bytes()
    out = HERE / 'candidate' / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    old = (prior / name).read_bytes()
    (HERE / (Path(name).name + '.diff')).write_text(''.join(difflib.unified_diff(old.decode().splitlines(True), data.decode().splitlines(True), fromfile='review114618/' + name, tofile='review114869/' + name)))
    measured = hashlib.sha256(data).hexdigest()
    result['paths'][name] = {'sha256': measured, 'matches_author': measured == claimed, 'changed': data != old}

def methods(path):
    return {c.name + '.' + m.name: ast.dump(m, include_attributes=False)
            for c in ast.parse(path.read_text()).body if isinstance(c, ast.ClassDef)
            for m in c.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')}

name = 'v12/python/tests/tools/test_integration_bundle.py'
old, new = methods(prior / name), methods(HERE / 'candidate' / name)
result['tests'] = {'old': len(old), 'new': len(new), 'changed': sorted(k for k in old.keys() & new.keys() if old[k] != new[k]), 'removed': sorted(old.keys() - new.keys()), 'added': sorted(new.keys() - old.keys())}
parent_audit = json.loads((RECORD.parents[1] / 'evidence/review-114828/audit.json').read_text())
result['parent_hashes'] = {name: {'sha256': hashlib.sha256((REPO / name).read_bytes()).hexdigest(), 'matches_parent_review': hashlib.sha256((REPO / name).read_bytes()).hexdigest() == parent_audit['paths'][name]['sha256']} for name in ('v12/worker/integration_workload.py', 'v12/worker/integration_entry.py', 'v12/python/tests/manager/test_integration_worker.py')}
(HERE / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
