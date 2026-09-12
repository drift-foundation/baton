"""Review checks in disposable fixtures, with retained output; no live run."""
import ast
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
started = time.monotonic()
spec = importlib.util.spec_from_file_location('custody_reader', PROOF / 'evidence/run9-budget-150384/reconcile.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
read = lambda path: mod.read(path, 16 * 1024 * 1024)
sha = lambda raw: 'sha256:' + hashlib.sha256(raw).hexdigest()
manifest_path = PROOF / 'evidence/accounting-152563/candidate-manifest.json'
assert sha(read(manifest_path)) == 'sha256:55f4bb56a338363072af0cb20ac81734276fe88f5548460830dc71bbe84860d5'
counts = {}
for name, expected in [('accounting-152563', 95), ('accounting-150501', 75), ('run9-freeze-150125', 198), ('run9-budget-150384', 19)]:
    files = json.loads(read(PROOF / 'evidence' / name / 'candidate-manifest.json'))['files']
    assert len(files) == expected
    for locator, binding in files.items():
        rel = Path(locator)
        assert not rel.is_absolute() and '..' not in rel.parts
        raw = read(REPO / rel)
        assert sha(raw) == binding['sha256'] and len(raw) == binding['bytes'], locator
        if 'mode' in binding:
            assert oct((REPO / rel).stat().st_mode & 0o7777) == binding['mode'], locator
    counts[name] = expected
bases = json.loads(read(PROOF / 'evidence/accounting-152563/product-base.json'))
old_methods = {}
for path, binding in bases.items():
    base = read(PROOF / 'evidence/accounting-152563' / ('base-' + Path(path).name))
    assert sha(base) == binding['sha256'] and len(base) == binding['bytes']
    assert read(REPO / path) == read(PROOF / 'evidence/accounting-152563/product-candidate' / path)
    if '/tests/' in path:
        def methods(raw):
            tree = ast.parse(raw)
            return {cls.name + '.' + fun.name: ast.dump(fun, include_attributes=False)
                    for cls in tree.body if isinstance(cls, ast.ClassDef)
                    for fun in cls.body if isinstance(fun, (ast.FunctionDef, ast.AsyncFunctionDef))}
        prior, current = methods(base), methods(read(REPO / path))
        assert all(current.get(name) == body for name, body in prior.items())
        old_methods[path] = {'unchanged': len(prior), 'added': len(current) - len(prior)}
for name in ('selected-images.json', 'execution-review.json'):
    assert not os.path.lexists(PROOF / 'prepared-152563' / name)
result = {'custody': counts, 'test_methods': old_methods, 'seconds': time.monotonic() - started}
(HERE / 'custody.json').write_text(json.dumps(result, indent=2) + '\n')
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(REPO / 'v12/python/src') + ':' + str(REPO / 'v12/python'))
commands = [
    ('product', [sys.executable, '-B', '-m', 'unittest', 'tests.manager.test_store', 'tests.manager.test_workspaces', '-v']),
    ('proof', [sys.executable, '-B', str(PROOF / 'prepared-152563/verify_offline.py')]),
]
checks = {}
for name, argv in commands:
    start = time.monotonic()
    done = subprocess.run(argv, cwd=REPO / 'v12/python', env=env, capture_output=True, text=True, timeout=40)
    checks[name] = {'argv': argv, 'exit': done.returncode, 'seconds': time.monotonic() - start}
    (HERE / (name + '.txt')).write_text(done.stdout + done.stderr)
(HERE / 'checks.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps({'custody': result, 'checks': checks}, indent=2))
sys.exit(any(item['exit'] for item in checks.values()))
