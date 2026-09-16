"""Focused reviewer revalidation; fake providers and disposable test fixtures only."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path('/home/sl/src/baton')
RECORD = Path(__file__).resolve().parent
ACCEPTANCE = ROOT / 'work/records/2026/09/finding-v12-managed-integration-execution/findings/finding-managed-integration-acceptance'
old = json.loads((RECORD / 'provenance-160468.json').read_text())
accepted = json.loads((ACCEPTANCE / 'review-evidence-174513.json').read_text())
names = {row['path'] for row in old['paths']}
current = {}
for row in accepted['revalidated_chain']:
    if row['kind'] == 'current-latest-accepted':
        current[row['path'].removeprefix('baton:')] = row['sha256']
names.update(current)

def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(names)}

result = {'work': 'W156162', 'claim': 174632, 'python': sys.version,
          'executable': sys.executable, 'jsonschema': importlib.metadata.version('jsonschema'),
          'before': hashes(), 'accepted_current_paths': len(current)}
result['old_candidate_comparison'] = [dict(path=row['path'], unchanged=result['before'][row['path']] == row['candidate_sha256'], accepted_managed_overlap=current.get(row['path']) == result['before'][row['path']]) for row in old['paths']]
result['accepted_current_mismatches'] = [name for name, sha in current.items() if result['before'][name] != sha]
argv = [sys.executable, '-B', '-m', 'unittest', '-v',
        'tests.job_manager.test_execution_limits', 'tests.manager.test_execution_limits',
        'tests.tools.test_execution_limits', 'tests.job_manager.test_store']
result['argv'] = argv
result['timeout_seconds'] = 120
started = time.monotonic()
with (RECORD / 'review-174632-tests.log').open('x') as output:
    process = subprocess.Popen(argv, cwd=ROOT / 'v12/python', env=dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1'), stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    result['pid'] = process.pid
    try:
        result['exit'] = process.wait(timeout=120)
    except subprocess.TimeoutExpired:
        result['timed_out'] = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        result['exit'] = process.returncode
    try:
        os.killpg(process.pid, 0)
        result['group_gone'] = False
        os.killpg(process.pid, signal.SIGTERM)
        time.sleep(1)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except ProcessLookupError:
        result['group_gone'] = True
result['elapsed_seconds'] = time.monotonic() - started
result['after'] = hashes()
result['unchanged_during_review'] = result['before'] == result['after']
result['prior_reviewer_seconds'] = 147.7342205499972
result['reviewer_seconds'] = result['prior_reviewer_seconds'] + result['elapsed_seconds']
result['historical_author'] = {'measured_seconds': 2530.5844189850177, 'measured_runs': 246, 'unknown_activities': 4}
(RECORD / 'review-evidence-174632.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('before', 'after')}, indent=2))
