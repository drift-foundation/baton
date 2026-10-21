"""Operator-only credential custody step; no printing of registry/source contents.
Run only after selected provisioning, from a root-owned verified copy.
"""
import json, os, stat
from pathlib import Path

def read_private(path, uid, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        s = os.fstat(fd)
        if not stat.S_ISREG(s.st_mode) or s.st_uid != uid or s.st_mode & 0o077 or s.st_nlink != 1 or s.st_size > limit:
            raise RuntimeError('private input metadata refused')
        value = os.read(fd, limit + 1)
        if len(value) > limit:
            raise RuntimeError('input exceeds bound')
        return value
    finally:
        os.close(fd)

def publish(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    try:
        os.fchown(fd, 61234, 61234)
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(value)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)

def main():
    if os.geteuid() != 0:
        raise RuntimeError('operator root required')
    root = Path('/etc/baton-managed-entry')
    if root.exists():
        raise RuntimeError('credential destination must be absent')
    def pairs(items):
        out = {}
        for k,v in items:
            if k in out: raise RuntimeError('duplicate registry key')
            out[k] = v
        return out
    registry = json.loads(read_private('/home/sl/.baton/credential-sources.json', 1000, 65536), object_pairs_hook=pairs)
    if set(registry) != {'schema','sources'} or registry['schema'] != 'baton.user-credential-sources/1':
        raise RuntimeError('registry schema refused')
    selected = [s for s in registry['sources'] if s.get('provider') == 'operator-file' and s.get('reference') == 'w202663-development']
    if len(selected) != 1 or set(selected[0]) != {'provider','reference','path'}:
        raise RuntimeError('credential selection must be unique')
    source = Path(selected[0]['path'])
    if not source.is_absolute() or '..' in source.parts:
        raise RuntimeError('credential path refused')
    for ancestor in source.parents:
        if ancestor.is_symlink(): raise RuntimeError('credential ancestor symlink refused')
    # Copy opaque bytes only. Never decode, log, hash or emit the bearer.
    bearer = read_private(source, 1000, 4096)
    root.mkdir(mode=0o711)
    os.chown(root, 0, 0)
    target = root / 'w339626-credential'
    publish(target, bearer)
    held = {'schema':'baton.user-credential-sources/1','sources':[{'provider':'operator-file','reference':'w202663-development','path':str(target)}]}
    publish(root / 'w339626-credential-sources.json', (json.dumps(held)+'\n').encode())
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)
    print('credential custody provisioned; no bearer emitted')

if __name__ == '__main__':
    try: main()
    except Exception:
        raise SystemExit('credential provisioning refused; preserve partial output; no automatic retry')
