"""Reproduce the bounded corrected-source proof without modifying either supplier."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

evidence = Path(__file__).resolve().parent
child = evidence.parent.parent
parent = child.parent.parent
base_path = child / 'evidence/claim-354638/BASE-MANIFEST.json'
base = json.loads(base_path.read_text())
supplier_path = parent / 'evidence/revoked-354829/INDEX.json'
supplier = json.loads(supplier_path.read_text())
original = Path(base['copy'])
source = Path(supplier['PINS']['candidate_root'])
candidate = Path('/tmp/w354630-354939/candidate')
token_path = 'v12/python/src/baton_v12/worker_manager/tokens.py'
test_path = 'v12/python/tests/job_manager/test_native_stop_restart.py'
test_hash = 'f05726cfb92c6d2d8d35e2df859e7f540c4dfc0aa6703b3fe8cdfe08d35bfadf'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked(path, expected):
    assert path.is_file() and not path.is_symlink(), path
    data = path.read_bytes()
    assert digest(data) == expected, path
    return data


def inventory(root):
    return {str(p.relative_to(root)): digest(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}


expected_original = dict(base['all_files'], **{test_path: test_hash})
assert inventory(original) == expected_original
assert all(base['all_files'][path] == value for path, value in base['pins'].items())
product = supplier['PINS']['product']
source_bytes = {path: checked(source / path, value) for path, value in product.items()}
assert product[token_path] == 'c341c2a5535a0dd015b8d0cb8594942303e5dca5e9518c7f9b45ed76d304e2ef'
assert all(base['all_files'][path] == value for path, value in product.items() if path != token_path)
test_bytes = checked(child / 'evidence/claim-354638/test_native_stop_restart.py', test_hash)
candidate.mkdir(parents=True, exist_ok=False)
for path, value in base['all_files'].items():
    data = checked(original / path, value)
    destination = candidate / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source_bytes[token_path] if path == token_path else data)
(candidate / test_path).write_bytes(test_bytes)
(evidence / 'tokens.py').write_bytes(source_bytes[token_path])
(evidence / 'test_native_stop_restart.py').write_bytes(test_bytes)
expected = dict(expected_original, **{token_path: product[token_path]})
assert inventory(candidate) == expected
manifest = {'work': 'W354630', 'claim': 354939, 'candidate': str(candidate),
            'base_manifest': str(base_path.relative_to(parent)), 'base_manifest_sha256': digest(base_path.read_bytes()),
            'supplier_index_sha256': digest(supplier_path.read_bytes()), 'original_pins': base['pins'],
            'corrected_product_pins': product, 'all_files': expected,
            'changes_from_base': {token_path: product[token_path], test_path: test_hash}}
(evidence / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
command = ['/home/sl/.local/state/baton-v12-venv/bin/python', '-m', 'unittest', '-v', 'tests.job_manager.test_native_stop_restart']
environment = {'PYTHONPATH': 'src:.', 'PYTHONDONTWRITEBYTECODE': '1', 'BATON_V12_DISK_ROOT': '/tmp/w354630-354939'}
start = time.monotonic()
with (evidence / 'run.log').open('w') as log:
    result = subprocess.run(command, cwd=candidate / 'v12/python', env=dict(os.environ, **environment), stdout=log, stderr=subprocess.STDOUT, timeout=60)
elapsed = time.monotonic() - start
record = {'command': command, 'cwd': str(candidate / 'v12/python'), 'environment': environment,
          'timeout_seconds': 60, 'exit': result.returncode, 'seconds': elapsed,
          'cumulative_implementer_seconds': 1.351658008999948 + elapsed,
          'prior_reviewer_seconds': 0.318443649, 'combined_child_seconds': 1.670101657999948 + elapsed}
(evidence / 'run.json').write_text(json.dumps(record, indent=2) + '\n')
assert inventory(candidate) == expected
assert inventory(original) == expected_original
record['candidate_and_original_unchanged_after_run'] = True
(evidence / 'run.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
print((evidence / 'run.log').read_text())
