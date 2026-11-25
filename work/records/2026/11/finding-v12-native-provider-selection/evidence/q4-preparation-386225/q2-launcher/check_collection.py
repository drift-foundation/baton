"""Synthetic byte-verifier checks; not native output or an exact-build turn fixture."""
import tempfile,json,shutil
from pathlib import Path
from collect import collect
with tempfile.TemporaryDirectory(prefix='baton-q2-collection-',dir='/var/tmp') as directory:
    root=Path(directory);source=root/'native/fixture';candidate=root/'native/workspaces/a/workspace/candidate'
    source.mkdir(parents=True);candidate.mkdir(parents=True)
    (source/'message.txt').write_bytes(b'before\n');(candidate/'message.txt').write_bytes(b'after\n')
    assert collect(root,'a')['edit_verified']
    (candidate/'unexpected.txt').write_bytes(b'extra\n');assert not collect(root,'a')['edit_verified']
    (candidate/'unexpected.txt').unlink();(candidate/'message.txt').write_bytes(b'wrong\n');assert not collect(root,'a')['edit_verified']
    (candidate/'message.txt').unlink();(candidate/'message.txt').symlink_to(source/'message.txt')
    try:collect(root,'a')
    except AssertionError:pass
    else:raise AssertionError('linked candidate not refused')
print(json.dumps(dict(simulation=True,checks=4,passed=4,engine_operations=0,provider_calls=0)))
