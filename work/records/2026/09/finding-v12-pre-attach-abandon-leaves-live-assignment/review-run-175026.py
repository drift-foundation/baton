"""Bounded independent review of current W63255 corrections."""
import difflib
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
manifest_path = record / 'candidate-175002.json'
manifest = json.loads(manifest_path.read_text())
def sha(data):
    return hashlib.sha256(data).hexdigest()
def hashes():
    return {r['path']: sha((root / r['path'].removeprefix('baton:')).read_bytes()) for r in manifest['files']}
result = {'claim': 175026, 'work': 'W63255', 'manifest_sha256': sha(manifest_path.read_bytes()), 'before': hashes(),
          'python': sys.version, 'jsonschema': importlib.metadata.version('jsonschema')}
result['head'] = subprocess.check_output(['git', 'log', '-1', '--format=%H'], cwd=root, text=True).strip()
result['snapshot_rows'] = []
patch = []
for row in manifest['files']:
    name = row['path'].removeprefix('baton:')
    target = root / name
    data = target.read_bytes()
    assert sha(data) == row['sha256'] and len(data) == row['bytes']
    assert oct(stat.S_IMODE(target.stat().st_mode)) == row['target_mode']
    assert target.is_file() and not target.is_symlink()
    base = subprocess.check_output(['git', 'show', result['head'] + ':' + name], cwd=root)
    for kind, content in [('checkpoint-base', base), ('candidate', data)]:
        retained = record / 'review-snapshots-175026' / kind / name
        retained.parent.mkdir(parents=True, exist_ok=True)
        retained.write_bytes(content)
    result['snapshot_rows'].append({'path': row['path'], 'checkpoint_base_sha256': sha(base), 'candidate_sha256': sha(data), 'same_as_checkpoint': base == data})
    patch.extend(difflib.unified_diff(base.decode().splitlines(keepends=True), data.decode().splitlines(keepends=True), fromfile='a/' + name, tofile='b/' + name))
(record / 'review-checkpoint-delta-175026.patch').write_text(''.join(patch))
methods = ["test_an_interruption_after_the_fence_resumes_one_authority_effect", "test_the_fence_adopts_the_declarations_own_operation_and_reason", 'test_a_pre_attach_abandonment_resolves_and_releases_the_assignment',
           'test_a_changed_reason_collides_and_never_fences_again',
           'test_the_original_reason_replays_one_durable_declaration',
           'test_a_fence_that_did_not_fence_leaves_everything_unresolved',
           'test_the_documented_command_fences_a_pre_attach_assignment',
           'test_the_abandonment_wins_and_a_public_start_can_no_longer_pass',
           'test_an_interruption_after_the_intent_resumes_the_same_fence',
           'test_a_resource_refusal_after_the_fence_keeps_it_and_then_retries',
           'test_a_wrong_participant_refuses_before_any_fence_or_cleanup',
           'test_the_ending_decides_nothing_about_output_or_custody',
           'test_a_requested_start_refuses_the_pre_attach_fence']
selectors = ['tests.tools.test_dogfood_operator.TheRecoveryNeverAdoptsAnOlderIncarnationsRuntime.' + m for m in methods]
selectors += ['tests.tools.test_dogfood_operator.TheGrantsAreHeldAgainstTheFixedAssignment.test_every_assignment_member_refuses_with_nothing_touched']
result['argv'] = [sys.executable, '-B', str(record / 'review-focus-175026.py'), '-v'] + selectors
start = time.monotonic()
with (record / 'review-tests-175026.log').open('x') as log:
    proc = subprocess.Popen(result['argv'], cwd=root / 'v12/python', env=dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1'), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        result['exit'] = proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        result['timed_out'] = True
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
        result['exit'] = proc.returncode
    try:
        os.killpg(proc.pid, 0)
        result['group_gone'] = False
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        result['group_gone'] = True
result['elapsed_seconds'] = time.monotonic() - start
result['after'] = hashes()
result['unchanged'] = result['after'] == result['before']
result['prior_reviewer_seconds'] = 9.748021468956722
result['reviewer_measured_seconds'] = result['prior_reviewer_seconds'] + result['elapsed_seconds']
result['author_manifest_ledger'] = manifest['ledger']
(record / 'review-evidence-175026.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('before', 'after', 'argv', 'snapshot_rows')}, indent=2))
