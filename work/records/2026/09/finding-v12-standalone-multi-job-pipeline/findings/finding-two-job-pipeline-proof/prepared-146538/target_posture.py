"""Read-only W71879 fresh-target preflight; never changes access or Git state.

The production integration root check and worker whole-path check remain
authoritative. This preparation check catches their known filesystem operands
before provisioning/submission. Its uid/gid parameters support local fixtures;
the command and deployment use the fixed 65532/1001 defaults.
"""

import argparse
import json
import os
from pathlib import Path
import stat

WORKER_UID = 65532
WORKSPACE_GID = 1001
EXISTING = ('demo/greeting.py', 'tests/test_greeting.py', 'demo/units.py')
ADDITIONS = ('tests/test_hours.py', 'check_hours.py')


class TargetPostureError(RuntimeError):
    pass


def manager_git_environment(target):
    """Trust this operator-provisioned target only, in child Git processes.

Its owner is the fixed worker uid, while the host manager keeps its own uid.
No global Git configuration is written, and no wildcard trust is added.
"""
    env = os.environ.copy()
    env.update({'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'safe.directory',
                'GIT_CONFIG_VALUE_0': str(target)})
    return env


def check_target(target, *, worker_uid=WORKER_UID, workspace_gid=WORKSPACE_GID):
    target = Path(target)
    if not target.is_absolute() or str(target.resolve()) != str(target):
        raise TargetPostureError('target must be an absolute canonical path without symlinks')
    observations = {}

    def inspect(path, *, directory=False, mutable=False, exact_mode=None):
        try:
            held = path.lstat()
        except OSError as failure:
            raise TargetPostureError(f'{path}: cannot inspect target posture: {failure}') from failure
        mode = stat.S_IMODE(held.st_mode)
        expected_type = stat.S_ISDIR if directory else stat.S_ISREG
        if not expected_type(held.st_mode):
            raise TargetPostureError(f'{path}: expected a regular {"directory" if directory else "file"}; links/special files refuse')
        if held.st_gid != workspace_gid:
            raise TargetPostureError(f'{path}: gid {held.st_gid}, expected workspace gid {workspace_gid}')
        if held.st_uid != worker_uid:
            raise TargetPostureError(f'{path}: uid {held.st_uid}, expected fixed worker uid {worker_uid}')
        required = 0o2770 if directory else 0o660 if mutable else 0o440
        if mode & required != required:
            raise TargetPostureError(f'{path}: mode {oct(mode)} lacks required {oct(required)} access/inheritance')
        if exact_mode is not None and mode != exact_mode:
            raise TargetPostureError(f'{path}: mode {oct(mode)}, expected worker Git-mode representation {oct(exact_mode)}')
        observations[str(path.relative_to(target))] = {'uid': held.st_uid, 'gid': held.st_gid, 'mode': oct(mode)}

    inspect(target, directory=True)
    git = target / '.git'
    inspect(git, directory=True)
    # A fresh ordinary clone is the only prepared form. A .git indirection or
    # metadata symlink cannot redirect this check to another repository.
    def walk_error(failure):
        raise TargetPostureError(f'cannot enumerate Git metadata: {failure}') from failure

    for parent, dirs, files in os.walk(git, followlinks=False, onerror=walk_error):
        for name in sorted(dirs):
            inspect(Path(parent) / name, directory=True)
        for name in sorted(files):
            path = Path(parent) / name
            rel = path.relative_to(git)
            mutable = rel.parts[0] in ('refs', 'logs') or str(rel) in (
                'HEAD', 'config', 'index', 'packed-refs', 'FETCH_HEAD', 'ORIG_HEAD')
            inspect(path, mutable=mutable)
    for name in ('HEAD', 'config', 'index'):
        if not (git / name).is_file():
            raise TargetPostureError(f'{git / name}: required fresh-clone metadata is absent')
    for name in (*EXISTING, *ADDITIONS):
        path = target / name
        parent = target
        for part in Path(name).parts[:-1]:
            parent = parent / part
            inspect(parent, directory=True)
        if name in EXISTING:
            # _owner_writable plus the exact 100644 -> 0644 worker check.
            inspect(path, exact_mode=0o644)
        elif path.exists() or path.is_symlink():
            raise TargetPostureError(f'{path}: future task addition must be absent at the original baseline')
    return {'target': str(target), 'worker_uid': worker_uid,
            'workspace_gid': workspace_gid, 'posture': 'compatible',
            'paths': observations,
            'limits': 'Read-only mode/identity observations, not an ACL repair or a guarantee against later mutation; production checks still run.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', type=Path)
    args = parser.parse_args()
    print(json.dumps(check_target(args.target), indent=2, sort_keys=True))
