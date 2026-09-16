"""Independent C2 provenance audit and bounded selector supervision."""
import ast
import ctypes
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

R = Path(__file__).resolve().parent
ROOT = R.parents[4]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
candidate = json.loads((R / 'CANDIDATE-182279.json').read_text())
evidence = json.loads((R / 'EVIDENCE-182279.json').read_text())
checks = []
def check(path, expected, mode=None):
    p = ROOT / path
    actual = sha(p)
    assert actual == expected, path
    assert p.is_file() and not p.is_symlink(), path
    if mode is not None:
        assert oct(p.stat().st_mode & 0o777) == mode, path
    checks.append({'path': path, 'sha256': actual, 'mode': oct(p.stat().st_mode & 0o777)})
check(str((R / 'CANDIDATE-182279.json').relative_to(ROOT)), '055b765cf539d472fda98dabc173973162214babbd51a97b758d70499086b628')
check(str((R / 'EVIDENCE-182279.json').relative_to(ROOT)), '9091bf68a01b80484af3389f9652d2780eb3da44e464550e911058bbc644af27')
check(str((R / 'HANDOFF-182279.md').relative_to(ROOT)), 'a761b60073499c124d98cb019160ac6b83a72a65f226a50ee1ae1241c30ab012')
for row in candidate['files']:
    check(row['path'], row['sha256'], row['target_mode'])
    check(row['snapshot'], row['sha256'], row['custody_mode'])
    check(row['base_snapshot'], row['base_sha256'], row['custody_mode'])
for row in candidate['read_only_inputs']:
    check(row['path'], row['sha256'], row['mode'])
for row in [candidate['base_manifest'], candidate['patch'], *evidence['artifacts']]:
    check(row['path'], row['sha256'])
for run in evidence['runs']:
    for key in ('receipt', 'log'):
        check(run[key]['path'], run[key]['sha256'])
    recorded = json.loads((ROOT / run['receipt']['path']).read_text())
    for key in ('status', 'seconds', 'timeout', 'group_gone', 'selectors'):
        assert recorded[key] == run[key]
    assert recorded['before'] == recorded['after'] and recorded['group_gone'] and not recorded['timeout']
    if run['run'] >= 6:
        for row in candidate['files']:
            assert recorded['before'][row['path']] == row['sha256']
test_row = candidate['files'][1]
def classes(path):
    return {n.name: ast.dump(n) for n in ast.parse(path.read_text()).body if isinstance(n, ast.ClassDef)}
old = classes(ROOT / test_row['base_snapshot'])
new = classes(ROOT / test_row['path'])
assert all(new[name] == value for name, value in old.items())

selector = sys.argv[1]
assert selector in ('CountedReopen', 'CountedReopenInvalidEvidence', 'UsefulCorrection', 'UsefulCorrectionInvalidEvidence')
prefix = R / ('review-182379-' + selector)
assert ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0
command = [sys.executable, '-B', '-m', 'unittest', '-v', 'tests.tools.test_correction_restart.' + selector]
env = dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1', BATON_C_EVIDENCE=str(prefix) + '-trace.json')
started = time.monotonic()
timed_out, signals, reaped = False, [], []
with Path(str(prefix) + '.log').open('x') as log:
    process = subprocess.Popen(command, cwd=ROOT / 'v12/python', env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        status = process.wait(timeout=180)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        signals.append('SIGTERM')
        try:
            status = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            signals.append('SIGKILL')
            status = process.wait(timeout=5)
for sig in (signal.SIGTERM, signal.SIGKILL):
    try:
        os.killpg(process.pid, sig)
        signals.append(sig.name)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            child, code = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            break
        if child:
            reaped.append([child, code])
        else:
            time.sleep(.02)
try:
    os.killpg(process.pid, 0)
    gone = False
except ProcessLookupError:
    gone = True
seconds = time.monotonic() - started
stable = all(sha(ROOT / row['path']) == row['sha256'] for row in checks)
result = {'claim': 182379, 'selector': selector, 'command': command, 'cwd': str(ROOT / 'v12/python'), 'python': sys.version, 'dependencies': {n: importlib.metadata.version(n) for n in ('jsonschema', 'jsonschema-specifications', 'referencing', 'attrs', 'rpds-py')}, 'seconds': seconds, 'status': status, 'timeout': timed_out, 'group_gone': gone, 'signals': signals, 'reaped': reaped, 'source_stable': stable, 'provenance': checks, 'C1_classes_unchanged': True, 'trace_sha256': sha(Path(str(prefix) + '-trace.json')), 'log_sha256': sha(Path(str(prefix) + '.log'))}
with Path(str(prefix) + '.json').open('x') as out:
    json.dump(result, out, indent=2)
    out.write('\n')
print(json.dumps({k: result[k] for k in ('selector', 'seconds', 'status', 'timeout', 'group_gone', 'signals', 'source_stable', 'trace_sha256')}))
assert status == 0 and not timed_out and gone and stable
