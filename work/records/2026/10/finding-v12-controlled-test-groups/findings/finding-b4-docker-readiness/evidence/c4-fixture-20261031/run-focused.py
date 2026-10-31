"""Retain the allocated focused unittest run, source hashes and owned-root cleanup."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / 'AGENTS.md').is_file())
MANIFEST = HERE.parent / 'allocation-c4-20261031/snapshot-manifest.json'
selection = json.loads(MANIFEST.read_text())
SNAPSHOT = REPO / selection['snapshot']
MODULE = 'tests.manager.test_integration_worker'
label = sys.argv[1]
assert re.fullmatch(r'[a-z0-9-]+', label)
log_path = HERE / (label + '.log')
assert not log_path.exists()

def identity():
    return {row['path']: hashlib.sha256((SNAPSHOT / row['path']).read_bytes()).hexdigest() for row in selection['files']}

before = identity()
root = Path(tempfile.mkdtemp(prefix='baton-w384944-c4-' + label + '-', dir='/var/tmp'))
env = dict(os.environ, TMPDIR=str(root), BATON_V12_DISK_ROOT=str(root), PYTHONDONTWRITEBYTECODE='1')
resolved = subprocess.run(['python3', '-B', '-m', 'tools.environment', 'interpreter'], cwd=SNAPSHOT / 'v12/python', env=env, capture_output=True, text=True, timeout=30)
assert resolved.returncode == 0, resolved.stderr
interpreter = resolved.stdout.strip()
collect_code = '''import json,unittest
s=unittest.defaultTestLoader.loadTestsFromName("tests.manager.test_integration_worker")
def ids(s):
 for t in s:
  if isinstance(t,unittest.TestSuite): yield from ids(t)
  else: yield t.id()
print(json.dumps(list(ids(s))))
'''
collection = subprocess.run([interpreter, '-B', '-c', collect_code], cwd=SNAPSHOT / 'v12/python', env=dict(env, PYTHONPATH='src'), capture_output=True, text=True, timeout=30)
assert collection.returncode == 0, collection.stderr
collected = json.loads(collection.stdout)
argv = ['just', 'test-one', MODULE]
start = time.monotonic()
timed_out = False
with log_path.open('x') as log:
    log.write(json.dumps({'argv': argv, 'cwd': str(SNAPSHOT / 'v12'), 'interpreter': interpreter, 'tmp_root': str(root), 'snapshot_commit': selection['commit']}) + '\n')
    log.flush()
    process = subprocess.Popen(argv, cwd=SNAPSHOT / 'v12', env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        process.wait(timeout=300)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
elapsed = time.monotonic() - start
after = identity()
text = log_path.read_text()
started = re.findall(r'^(test_\w+) \((tests\.[^)]+)\)', text, re.M)
# unittest's parenthesized name includes the method under this interpreter.
ids = [full if full.endswith('.' + method) else full + '.' + method for method, full in started]
remaining = sorted(str(p.relative_to(root)) for p in root.rglob('*'))
if not remaining:
    root.rmdir()
summary = {'label': label, 'exit': process.returncode, 'timed_out': timed_out, 'seconds': elapsed, 'collected': collected, 'started': ids, 'unaccounted': sorted(set(collected) - set(ids)), 'duplicate_started': len(ids) - len(set(ids)), 'summary_lines': [line for line in text.splitlines() if line.startswith(('Ran ', 'OK', 'FAILED ('))], 'source_drift': [p for p in before if before[p] != after[p]], 'temporary_root': str(root), 'remaining_paths': remaining, 'empty_root_removed': not root.exists()}
(HERE / (label + '.summary.json')).write_text(json.dumps(summary, indent=2) + '\n')
(HERE / (label + '.source-before.json')).write_text(json.dumps(before, indent=2) + '\n')
(HERE / (label + '.source-after.json')).write_text(json.dumps(after, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k not in ('collected', 'started', 'remaining_paths')}, indent=2))
print('collected', len(collected), 'started', len(ids), 'remaining paths', len(remaining))
sys.exit(process.returncode or (1 if summary['source_drift'] or summary['unaccounted'] or remaining else 0))
