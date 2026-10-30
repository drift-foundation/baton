#!/usr/bin/python3 -I
"""Fixed managed entry; root-protected inventory is checked before any import."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

# -I ignores PYTHONDONTWRITEBYTECODE; keep installed inventory immutable.
sys.dont_write_bytecode = True
ROOT = Path('/opt/baton-next-run')


def protected(path):
    for item in [*reversed(path.parents), path]:
        st = item.lstat()
        if st.st_uid != 0 or st.st_mode & 0o022 or stat.S_ISLNK(st.st_mode):
            raise ValueError('unsafe installed custody')
    return path


def main():
    if os.geteuid() != 0 or Path(__file__).resolve() != ROOT / 'entry.py':
        raise ValueError('installed privileged entry required')
    protected(Path(__file__))
    config = json.loads(protected(ROOT / 'installation.json').read_bytes())
    ready = json.loads(protected(ROOT / 'READY').read_bytes())
    if ready != {'installation_sha256': hashlib.sha256((ROOT / 'installation.json').read_bytes()).hexdigest()}:
        raise ValueError('unpublished installation')
    if int(os.environ.get('SUDO_UID', '-1')) != config['caller_uid']:
        raise ValueError('unselected caller')
    for rel, expected in config['files'].items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts:
            raise ValueError('invalid inventory')
        if hashlib.sha256(protected(ROOT / rel).read_bytes()).hexdigest() != expected:
            raise ValueError('changed installed bytes')
    # Refuse unlisted Python modules as well as changed listed files.
    actual = set()
    for path in (ROOT / 'code').rglob('*'):
        protected(path)
        if path.is_file(): actual.add(str(path.relative_to(ROOT)))
        elif not path.is_dir(): raise ValueError('special installed node')
    expected = {p for p in config['files'] if p.startswith('code/')}
    if actual != expected:
        raise ValueError('unlisted installed code')
    sys.path[:0] = [str(ROOT / 'code/src'), str(ROOT / 'code')]
    from tools.next_run_managed import main as dispatch
    return dispatch()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as failure:
        print('managed next-run refused: ' + type(failure).__name__ + ': ' + str(failure), file=sys.stderr)
        raise SystemExit(2)
