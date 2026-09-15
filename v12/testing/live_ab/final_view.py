"""Verify the committed output without changing the target checkout or index."""
import hashlib
import os
from pathlib import Path
import stat
import subprocess


def git(target, *args, timeout):
    return subprocess.run(['git', '--no-optional-locks', '-c', 'safe.directory=' + str(target),
                           '-C', str(target), *args], check=True, capture_output=True,
                          timeout=timeout(), env=dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null',
                          GIT_CONFIG_SYSTEM='/dev/null')).stdout


def measure(view):
    result = {}
    for path in sorted(view.rglob('*')):
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise RuntimeError('final view contains a non-regular file')
        result[str(path.relative_to(view))] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                             'mode': stat.S_IMODE(mode)}
    return result


def committed_view(target, view, *, expected_commit, timeout):
    """Export exactly one known commit, including only supported regular files."""
    identity = git(target, 'show', '--no-patch', '--format=%H %T', 'refs/heads/main', timeout=timeout).decode().strip()
    commit, tree = identity.split()
    if commit != expected_commit:
        raise RuntimeError('committed target differs from the Authority canonical target')
    rows = git(target, 'ls-tree', '-r', '-z', '--full-tree', commit, timeout=timeout).split(b'\0')
    files = []
    for row in filter(None, rows):
        metadata, name = row.split(b'\t', 1)
        mode, kind, blob = metadata.decode().split()
        name = name.decode('utf-8')
        relative = Path(name)
        if mode not in ('100644', '100755') or kind != 'blob' or relative.is_absolute() or any(part in ('.', '..', '.git') for part in relative.parts):
            raise RuntimeError('unsupported committed final-view path')
        files.append((name, mode, blob))
    view.mkdir(exist_ok=False)
    blobs = {}
    for name, mode, blob in files:
        path = view / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(git(target, 'cat-file', 'blob', blob, timeout=timeout))
        path.chmod(0o755 if mode == '100755' else 0o644)
        blobs[name] = blob
    return {'commit': commit, 'tree': tree, 'path': str(view), 'git_blobs': blobs, 'manifest': measure(view)}


def verify_view(target, view, evidence, *, expected_commit, timeout, persist):
    result = committed_view(target, view, expected_commit=expected_commit, timeout=timeout)
    result['checks'] = []
    result['clean'] = False
    persist(evidence / 'final-view.json', result)
    commands = [(['python3', '-B', 'check_greeting.py'], 'final-greeting.log'),
                (['python3', '-B', 'check_hours.py'], 'final-hours.log'),
                (['python3', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], 'final-tests.log')]
    try:
        for argv, log in commands:
            done = subprocess.run(argv, cwd=view, capture_output=True, text=True, timeout=timeout(),
                                  env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            (evidence / log).write_text(done.stdout + done.stderr)
            result['checks'].append({'argv': argv, 'status': done.returncode, 'log': log})
            if done.returncode:
                raise RuntimeError('committed final-view verification failed: ' + log)
        if measure(view) != result['manifest']:
            raise RuntimeError('final verification changed the committed view')
        after = git(target, 'show', '--no-patch', '--format=%H %T', 'refs/heads/main', timeout=timeout).decode().strip()
        if after != result['commit'] + ' ' + result['tree']:
            raise RuntimeError('committed target moved during final verification')
        result['clean'] = True
        return result
    finally:
        persist(evidence / 'final-view.json', result)
