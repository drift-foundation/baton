"""Bounded W133361 static author check; no live writes or product execution."""
import difflib
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import time

started = time.perf_counter()
root = Path(__file__).resolve().parents[7]
author = Path(__file__).resolve().parent
record = author.parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def describe(path):
    info = path.lstat()
    assert stat.S_ISREG(info.st_mode), str(path)
    data = path.read_bytes()
    return {"sha256": digest(data), "bytes": len(data), "mode": oct(stat.S_IMODE(info.st_mode)), "regular": True}


proposal = json.loads((record / 'evidence/config-change-proposal.json').read_text())
base = (author / 'before/baton.json').read_bytes()
live = Path(proposal['source_path'])
assert base == live.read_bytes()
assert digest(base) == proposal['source_sha256']
before = json.loads(base)
after = json.loads((author / 'baton.next.json').read_bytes())
expected = json.loads(base)
generation, instruction = proposal['changes']
assert generation['json_pointer'] == '/generation'
assert instruction['json_pointer'] == '/teams/baton/roles/impl/instructions'
assert before['generation'] == generation['before'] == 8
assert generation['after'] == 9
assert before['teams']['baton']['roles']['impl']['instructions'] == instruction['before']
append = (record / 'MANAGED-TURN-INSTRUCTION-v1.txt').read_bytes().removesuffix(b'\n')
assert instruction['after'].encode() == instruction['before'].encode() + b' ' + append
expected['generation'] = generation['after']
expected['teams']['baton']['roles']['impl']['instructions'] = instruction['after']
assert after == expected

preparation = json.loads((author / 'preparation.json').read_text())
policies = []
diff = ''
for entry in preparation['policy_files']:
    name = entry['path']
    original = author / 'before' / name
    current = root / name
    original_info, current_info = describe(original), describe(current)
    assert original_info['sha256'] == entry['base_sha256']
    assert current_info['mode'] == entry['base_mode']
    assert current.lstat().st_mode & stat.S_IWUSR
    diff += ''.join(difflib.unified_diff(original.read_text().splitlines(True), current.read_text().splitlines(True), fromfile='a/' + name, tofile='b/' + name))
    policies.append({'path': name, 'base': {**original_info, 'mode': entry['base_mode']}, 'candidate': current_info})
(author / 'policy.diff').write_text(diff)
assert 'neither progressed nor' not in (root / 'docs/AGENTS-MAILBOX-PROTO.md').read_text()

preservation = json.loads((record / 'evidence/recovery-preservation-133448.json').read_text())
for entry in preservation['paths']:
    path = root / entry['path']
    if entry.get('exists') is False:
        assert not path.exists() and not path.is_symlink(), str(path)
    else:
        actual = describe(path)
        assert all(actual[key] == entry[key] for key in ('sha256', 'bytes', 'mode', 'regular')), str(path)

command = ['git', 'diff', '--check']
check_start = time.perf_counter()
check = subprocess.run(command, cwd=root, capture_output=True, text=True)
check_elapsed = time.perf_counter() - check_start
(author / 'whitespace-check.txt').write_text(check.stdout + check.stderr)
assert check.returncode == 0, check.stdout + check.stderr
manifest = {
    'work': 'W133361', 'author': 'baton.tuner', 'claim': 133517,
    'decision': 'FINDING.md: owner acceptance133489; CORRECTION-RECOVERY-v1.md',
    'policy_files': policies,
    'config': {'live_path': str(live), 'base': describe(author / 'before/baton.json'), 'live_mode': describe(live)['mode'], 'candidate_path': 'evidence/author/baton.next.json', 'candidate': describe(author / 'baton.next.json'), 'changed_json_pointers': [entry['json_pointer'] for entry in proposal['changes']]},
    'review_inputs': {name: describe(record / name) for name in ('FINDING.md', 'PLAN.md', 'CORRECTION-RECOVERY-v1.md', 'MANAGED-TURN-INSTRUCTION-v1.txt', 'OPERATIONS-CHECKLIST-v1.md', 'evidence/config-change-proposal.json', 'evidence/recovery-preservation-133448.json')},
    'policy_diff': describe(author / 'policy.diff'),
    'verification': {'command': 'python3 work/records/2026/09/finding-acp-turn-ended-with-held-claim/evidence/author/verify.py', 'status': 'passed', 'internal_elapsed_seconds': time.perf_counter() - started, 'whitespace_command': command, 'whitespace_elapsed_seconds': check_elapsed, 'whitespace_exit_code': check.returncode, 'preservation_entries_matched': len(preservation['paths']), 'exact_config_delta': True, 'exact_role_append_bytes': True, 'live_config_unchanged': True},
    'budget': {'author_allocation_seconds': 15, 'author_charged_seconds': 1, 'author_remaining_seconds': 14, 'accounting': 'Conservative one-second charge covers preparation, static verification and supporting read-only checks; measured timings retained in preparation.json, this manifest and command-log.json. No repeat or borrowing.', 'review_reserved_seconds': 15, 'operations_reserved_seconds': 90},
    'limitations': 'Candidate only. Independent review, live config acceptance, lifecycle replacement, actual instruction delivery and P handoff proof remain pending. No product tests run; P budgets unchanged.'
}
(author / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest['verification'], indent=2))
