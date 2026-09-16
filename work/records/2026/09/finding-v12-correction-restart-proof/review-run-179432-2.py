"""Independent deterministic B verification; no provider or OCI qualification."""
import ctypes
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def locate(value):
    return ROOT / value.removeprefix('baton:')
manifest = json.loads((HERE / 'candidate-179255.json').read_text())
evidence = json.loads((HERE / 'EVIDENCE-179255.json').read_text())
checks = []
def check(path, expected):
    actual = sha(path)
    checks.append({'path': str(path.relative_to(ROOT)), 'expected': expected, 'actual': actual})
    assert actual == expected, str(path)
check(HERE / 'candidate-179255.json', '010aaefde8159ef52b95ddf289b981b051a2b64041a3a1638441a158cb517c50')
check(locate(manifest['base_manifest']), manifest['base_sha256'])
check(locate(manifest['patch']), manifest['patch_sha256'])
check(locate(manifest['evidence']), manifest['evidence_sha256'])
for one in manifest['files']:
    for key in ('path', 'candidate_path'):
        check(locate(one[key]), one['sha256'])
    assert stat.S_IMODE(locate(one['path']).stat().st_mode) == int(one['target_mode'], 8)
    assert locate(one['path']).is_file() and not locate(one['path']).is_symlink()
    if one['base_exists']:
        check(locate(one['base_snapshot']), one['base_sha256'])
for one in evidence['runs']:
    check(locate(one['path']), one['sha256'])
    check(locate(one['log_path']), one['log_sha256'])
for one in evidence['baseline_and_unchanged_checks']:
    file = next((f for f in manifest['files'] if f['path'] == one['path']), None)
    check(locate(file['base_snapshot']) if one['compared'] == 'B base snapshot' else locate(one['path']), one['expected'])
selectors = []
for number in (13, 14):
    selectors += json.loads((HERE / f'run-179255-{number}.json').read_text())['selectors']
before = {one['path']: sha(locate(one['path'])) for one in manifest['files']}
env = dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1', PYTHONPYCACHEPREFIX='/tmp/baton-review-179432-pycache')
command = [sys.executable, '-B', '-m', 'unittest', '-v', *selectors]
assert ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0
start = time.monotonic()
timeout = False
with (HERE / 'review-run-179432-2.log').open('x') as log:
    process = subprocess.Popen(command, cwd=ROOT / 'v12/python', env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        status = process.wait(timeout=180)
    except subprocess.TimeoutExpired:
        timeout = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            status = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            status = process.wait(timeout=5)
reaped = []
cleanup_start = time.monotonic()
while time.monotonic() - cleanup_start < 5:
    try:
        child, child_status = os.waitpid(-1, os.WNOHANG)
    except ChildProcessError:
        break
    if child:
        reaped.append([child, child_status])
    else:
        time.sleep(0.05)
seconds = time.monotonic() - start
try:
    os.killpg(process.pid, 0)
    gone = False
except ProcessLookupError:
    gone = True
after = {one['path']: sha(locate(one['path'])) for one in manifest['files']}
result = {"process_pid": process.pid, "reaped_children": reaped, "subreaper": True, 'work': 'W161234', 'claim': 179432, 'reviewer': 'baton.codex', 'candidate_sha256': sha(HERE / 'candidate-179255.json'), 'checks': checks, 'command': command, 'status': status, 'timeout': timeout, 'group_gone': gone, 'seconds': seconds, 'prior_reviewer_seconds': 4.108358147001127, 'cumulative_reviewer_seconds': seconds + 32.19685840301099, 'author_seconds': 146.81700767797884, 'before': before, 'after': after, 'python': sys.version, 'dependencies': {name: importlib.metadata.version(name) for name in evidence['environment']['dependencies']}, 'log_sha256': sha(HERE / 'review-run-179432-2.log'), 'qualification': 'Deterministic fake/replay and local subprocess only; simulated OCI; no actual engine or live provider.'}
with (HERE / 'review-evidence-179432-2.json').open('x') as out:
    json.dump(result, out, indent=2)
    out.write('\n')
print(json.dumps({key: result[key] for key in ('status', 'seconds', 'timeout', 'group_gone', 'cumulative_reviewer_seconds')}))
assert before == after and status == 0 and not timeout and gone
