"""Review the sole fixture correction, retaining prior broader evidence."""
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

root = Path('/home/sl/src/baton')
record = Path(__file__).resolve().parent
prior = json.loads((record / 'review-evidence-174632.json').read_text())
manifest_path = record / 'candidate-174738.json'
manifest = json.loads(manifest_path.read_text())
row = manifest['files'][0]
name = row['path'].removeprefix('baton:')
target = root / name
data = target.read_bytes()
start_comment = data.index(b'        # THE PIN IS A FLOOR, NOT AN EQUALITY')
end_assertion = data.index(b'        self.assertGreaterEqual(schema.SCHEMA_VERSION, 5)\n', start_comment) + len(b'        self.assertGreaterEqual(schema.SCHEMA_VERSION, 5)\n')
baseline = data[:start_comment] + b'        self.assertEqual(schema.SCHEMA_VERSION, 5)\n' + data[end_assertion:]
def sha(data):
    return hashlib.sha256(data).hexdigest()
def hashes():
    return {p: sha((root / p).read_bytes()) for p in prior['after']}
result = {'work': 'W156162', 'claim': 174782, 'manifest_sha256': sha(manifest_path.read_bytes()),
          'candidate_sha256': sha(data), 'candidate_bytes': len(data),
          'mode': oct(stat.S_IMODE(target.stat().st_mode)), 'regular_non_symlink': target.is_file() and not target.is_symlink(),
          'reconstructed_baseline_sha256': sha(baseline), 'before': hashes(),
          'python': sys.version, 'jsonschema': importlib.metadata.version('jsonschema')}
assert result['candidate_sha256'] == row['sha256']
assert result['candidate_bytes'] == row['bytes']
assert result['mode'] == row['target_mode']
assert result['regular_non_symlink']
assert result['reconstructed_baseline_sha256'] == row['baseline_sha256'] == prior['after'][name]
result['other_changed_paths'] = [p for p in prior['after'] if p != name and prior['after'][p] != result['before'][p]]
assert not result['other_changed_paths'], result['other_changed_paths']
result['argv'] = [sys.executable, '-B', '-m', 'unittest', '-v', 'tests.tools.test_execution_limits.TheJobOwnerAnswersOneBoundaryWithoutADelivery']
start = time.monotonic()
with (record / 'review-174782-tests.log').open('x') as log:
    process = subprocess.Popen(result['argv'], cwd=root / 'v12/python', env=dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1'), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        result['exit'] = process.wait(timeout=20)
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
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        result['group_gone'] = True
result['elapsed_seconds'] = time.monotonic() - start
result['reviewer_measured_seconds'] = prior['reviewer_seconds'] + result['elapsed_seconds']
result['author_measured_seconds'] = prior['historical_author']['measured_seconds'] + manifest['ledger']['seconds']
result['after'] = hashes()
result['unchanged_during_review'] = result['after'] == result['before']
(record / 'review-evidence-174782.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('before', 'after')}, indent=2))
