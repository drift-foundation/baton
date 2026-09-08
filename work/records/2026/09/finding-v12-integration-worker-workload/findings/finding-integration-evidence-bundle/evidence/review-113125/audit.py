"""Independent candidate/test audit and read-only real-Git vector probe."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path('/home/sl/src/baton')
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(REPO/'v12/python'), str(REPO/'v12/python/src')]
from tools import integration_bundle as producer

expected = {
    'v12/worker/integration_contract.py': '03e346c27b6b919f00581183e301b9c5c979e89ba43adb29aa301d0ce9e735a6',
    'v12/python/tools/integration_bundle.py': 'ee7a41f545c4cf8806af31d55e318f5a256efb2b525081b118d82ad4fb8c5c20',
    'v12/python/tests/tools/test_integration_bundle.py': '645b16f533530d108c0824d48267319b28d0bf7df001b0625c3be56523629c26',
    'v12/python/tools/parallel_test.py': '1ae0956fda4bfdb8242c8f5e0a57e7c7dd3833904042dfc7734fc0acfecc16f4'}
for name, wanted in expected.items():
    data = (REPO/name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == wanted
    target = HERE/'candidate'/name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(data)
for episode in ['review-112857', 'review-112989']:
    previous = HERE.parent/episode
    baseline = json.loads((previous/'probe.json').read_text())['candidate']
    for name, wanted in baseline.items():
        assert hashlib.sha256((previous/'candidate'/name).read_bytes()).hexdigest() == wanted

def methods(text):
    return {c.name+'.'+f.name: ast.dump(f, include_attributes=False) for c in ast.parse(text).body if isinstance(c, ast.ClassDef) for f in c.body if isinstance(f, ast.FunctionDef) and f.name.startswith('test_')}
testpath = 'v12/python/tests/tools/test_integration_bundle.py'
before = methods((HERE.parent/'review-112989/candidate'/testpath).read_text())
after = methods((REPO/testpath).read_text())
test_delta = dict(before=len(before), after=len(after), removed=sorted(before.keys()-after.keys()), added=sorted(after.keys()-before.keys()), changed=sorted(k for k in before.keys() & after.keys() if before[k]!=after[k]))
assert test_delta['removed'] == [] and len(test_delta['changed']) == 11 and len(test_delta['added']) == 11

# Every child reaches cwd by the supplied descriptor, not a repository path.
# Commands read existing committed objects only. No repository fixture is made.
directory = os.open(REPO, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
calls = []
def run(argv, *, directory):
    assert argv[0:2] == ['git', '--no-optional-locks'] or tuple(argv[0:2]) == ('git', '--no-optional-locks')
    assert '-C' not in argv and str(REPO) not in argv
    env = {'PATH': '/usr/bin:/bin', 'GIT_OPTIONAL_LOCKS': '0', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'}
    result = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            preexec_fn=lambda: os.fchdir(directory), pass_fds=(directory,), env=env, timeout=20)
    calls.append(dict(argv=list(argv), returncode=result.returncode, stdout_bytes=len(result.stdout), stderr_bytes=len(result.stderr)))
    assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')
    return {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
try:
    revision = run(['git', '--no-optional-locks', 'rev-parse', '--verify', 'HEAD'], directory=directory)['stdout'].strip().decode('ascii')
    tree = producer._one_line(run(producer.tree_vector(revision), directory=directory)['stdout'], 'review tree')
    side = producer._entry(run, directory, tree, 'AGENTS.md', 'reviewed committed policy')
    assert side is not None
    content = producer._content(run, directory, side, producer.MAX_BLOB_BYTES, 'reviewed committed policy')
    actual_object = hashlib.sha1(b'blob '+str(len(content)).encode('ascii')+b'\0'+content).hexdigest()
    assert actual_object == side['object']
    git_probe = dict(revision=revision, tree=tree, path='AGENTS.md', mode=side['mode'], object=side['object'], bytes=len(content), content_sha256=hashlib.sha256(content).hexdigest(), object_hash_verified=True, cwd='child fchdir on inherited directory descriptor', calls=calls,
                     limits='Existing committed object and all four vectors only; not full real-owner bundle composition or production-runner acceptance.')
finally:
    os.close(directory)

report = dict(claim=113125, candidate=expected, historical_candidate_snapshots='all match', test_delta=test_delta, real_git_vector_probe=git_probe)
with (HERE/'audit.json').open('x') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(json.dumps(report, indent=2))
