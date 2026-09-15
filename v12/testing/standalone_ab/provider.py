#!/usr/bin/python3
"""Synthetic provider executable; no manager API, store, or receipt access."""
import json
import hashlib
from pathlib import Path
import re
import subprocess
import sys


def fixture():
    return json.loads((Path(__file__).resolve().parent / 'fixtures/scenario.json').read_text())


def match(pattern, prompt):
    found = re.search(pattern, prompt)
    if found is None:
        raise ValueError('unsupported provider task operands')
    return found.group(1)


def tree(root, expected):
    """Match the fixture bytes before accepting or writing any candidate."""
    for name, body in expected.items():
        path = root / name
        if path.is_symlink() or not path.is_file() or path.read_text() != body:
            raise ValueError('incompatible scenario tree: ' + name)


def verify(root, check):
    subprocess.run(['/usr/bin/python3', '-B', check], cwd=root, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)


def answer(prompt, room, *, data=None):
    data = fixture() if data is None else data
    role = match(r'\[BATON-SYNTHETIC standalone-ab-v1 role=([a-z]+)\]', prompt)
    if role not in ('a', 'b', 'verification', 'review', 'approval', 'integrator'):
        raise ValueError('unknown scenario role')
    task_roles = (role,) if role in ('a', 'b') else ('a', 'b')
    for task_role in task_roles:
        required = (Path(__file__).resolve().parent / ('fixtures/task-' + task_role + '.md')).read_text()
        if required not in prompt:
            raise ValueError('incompatible scenario task contract')
    if role == 'integrator':
        return integrate(prompt, data)
    reviewing = prompt.startswith('You are reviewing a change on a read-only source tree at ')
    if not reviewing:
        if role not in ('a', 'b') or 'Edit files here directly.' not in prompt:
            raise ValueError('unsupported implementation task')
        tree(room, data['baseline'])
        for name in data['b']:
            if name not in data['baseline'] and (room / name).exists():
                raise ValueError('implementation must start from the original baseline')
        for name, body in data[role].items():
            (room / name).write_text(body)
        return
    source = Path(match(r'^You are reviewing a change on a read-only source tree at (.+?)\. Do not', prompt))
    expected = dict(data['baseline'])
    for name in (('a', 'b') if role in ('verification', 'review', 'approval') else (role,)):
        expected.update(data[name])
    tree(source, expected)
    check = 'check_greeting.py' if role == 'a' else 'check_hours.py'
    verify(source, check)
    if role in ('verification', 'review', 'approval'):
        subject = json.loads((source.parent / 'judgment.json').read_text())
        if subject['kind'] != role or not subject['candidate'] or not subject['causal_observations']:
            raise ValueError('foreign or incomplete derived judgment')
        causal = subject['causal_observations']
        if causal['base']['status'] == 0 or 'hours_to_seconds' not in causal['base']['output']:
            raise ValueError('baseline did not fail for missing hours behavior')
        expected_digest = 'sha256:' + hashlib.sha256(data['b']['check_hours.py'].encode()).hexdigest()
        for name in ('base', 'isolated', 'combined'):
            if causal[name]['command'] != ['python3', 'check_hours.py'] or causal[name]['test_digest'] != expected_digest:
                raise ValueError('causal observation ran another test')
            if name != 'base' and causal[name]['status'] != 0:
                raise ValueError('candidate causal check failed')
        head = subprocess.run(['git', '--no-optional-locks', '-c', 'safe.directory=' + str(source),
                               '-C', str(source), 'rev-parse', 'HEAD'], check=True,
                              capture_output=True, text=True, timeout=10).stdout.strip()
        if head != subject['candidate']:
            raise ValueError('derived judgment candidate differs')
    report = room / match(r'When you are done, write your decision to (.+?) as a JSON', prompt)
    if report.parent != room or report.name != 'review-report.json':
        raise ValueError('foreign review output')
    report.write_text(json.dumps({'schema': 'baton.review-report/1', 'verdict': 'accepted',
        'findings': 'SIMULATED provider judgment for standalone-ab-v1/' + role +
        ': exact synthetic candidate bytes match; ran ' + check +
        '. A scope includes tests/test_greeting.py and preserves ordinary-name coverage; B adds hours tests and preserves minutes.'}) + '\n')


def integrate(prompt, data):
    # The production workload already performed correlation and whole-path
    # preflight. This simulated provider independently bounds its own effects.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import integration_contract as contract
    bundle = Path(match(r'The approved evidence bundle is mounted read-only at (.+?)\.', prompt))
    target = Path(match(r'The target is (.+?) and it is the only tree', prompt))
    report = Path(match(r'Write your bounded baton.integration-report/1 report to (.+?) and write', prompt))
    taken = contract.read_bundle(str(bundle))
    rows = taken['envelope']['paths']
    if {one['path'] for one in rows} != set(data['a']):
        raise ValueError('unsupported integration scope')
    tree(target, data['baseline'])
    staged = {}
    for row in rows:
        if row['operation'] != 'edit' or row['candidate']['mode'] != '100644':
            raise ValueError('unsupported integration operation')
        body = (bundle / 'blobs' / row['candidate']['blob']).read_bytes()
        if body != data['a'][row['path']].encode():
            raise ValueError('foreign integration candidate')
        staged[row['path']] = body
    for name, body in staged.items():
        (target / name).write_bytes(body)
    verify(target, 'check_greeting.py')
    report.write_text(json.dumps({'schema': 'baton.integration-report/1',
        'assignment_digest': match(r'The assignment it answers is (sha256:[a-f0-9]{64})\.', prompt),
        'bundle_digest': match(r'Its measured identity is (sha256:[a-f0-9]{64})\.', prompt),
        'outcome': 'imported', 'phase': 'verification', 'paths': sorted(staged),
        'verification': {'argv': ['python3', 'check_greeting.py'], 'status': 0}, 'code': None}) + '\n')


def main():
    if sys.argv[1:-1] != ['--print', '--dangerously-skip-permissions', '--output-format', 'json']:
        raise ValueError('unsupported provider invocation')
    answer(sys.argv[-1], Path.cwd())
    print(json.dumps({'type': 'result', 'is_error': False, 'result': 'SIMULATED standalone-ab-v1'}))


if __name__ == '__main__':
    try:
        main()
    except Exception as failure:
        print(json.dumps({'type': 'result', 'is_error': True, 'result': type(failure).__name__}), flush=True)
        sys.exit(1)
