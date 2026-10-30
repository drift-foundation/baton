"""Read-only verification of retained candidate and base bytes."""
from pathlib import Path
import hashlib
import json
root = Path(__file__).resolve().parent
manifest = json.loads((root / 'CANDIDATE.json').read_text())
for entry in manifest['paths']:
    for directory, member in (('candidate', 'candidate_sha256'), ('before', 'base_sha256')):
        expected = entry[member]
        path = root / directory / entry['path']
        if expected is None:
            assert not path.exists(), str(path)
        else:
            assert path.is_file() and not path.is_symlink(), str(path)
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, str(path)
print('verified', len(manifest['paths']), 'candidate paths and retained bases')
