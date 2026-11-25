"""Prepare only the selected fresh offline root; never invoke an engine."""
import json
import os
from pathlib import Path
import shutil
import sys
from render_offline import render


def setup(s):
    render(s)
    if not s.get('authorization'):
        raise ValueError('offline execution/root preparation not selected')
    if (s['uid'], s['gid']) != (os.getuid(), os.getgid()):
        raise ValueError('run setup as the selected non-root UID:GID')
    root = Path(s['execution_root'])
    if root != Path(os.path.realpath(root)):
        raise ValueError('symlink alias refused')
    for parent in (root, *root.parents):
        if os.path.lexists(parent / '.git') or ((parent / 'HEAD').exists() and (parent / 'objects').is_dir()):
            raise ValueError('run root must be outside every repository')
    root.mkdir(mode=0o700, exist_ok=False)
    for name in ('packet', 'home', 'workspace', 'private-output'):
        (root / name).mkdir(mode=0o700)
    for name in ('capture.py', 'offline_tier_probe.py'):
        shutil.copyfile(Path(__file__).parent / name, root / 'packet' / name)
        (root / 'packet' / name).chmod(0o600)
    return {'prepared': str(root), 'engine_executed': False, 'credentials_read': False}


if __name__ == '__main__':
    print(json.dumps(setup(json.loads(Path(sys.argv[1]).read_text())), indent=2))
