"""Independent metadata/custody verification; never execute provider code."""
from pathlib import Path
import hashlib, json, os, stat, time
ROOT = Path('/home/sl/src/baton')
PROOF = ROOT / 'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
OUT = Path(__file__).resolve().parent
start = time.monotonic()
def bounded(path, limit):
    before = path.lstat()
    assert stat.S_ISREG(before.st_mode) and before.st_size <= limit, str(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        assert (before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino)
        assert stat.S_ISREG(opened.st_mode) and opened.st_size <= limit
        data = stream.read(limit + 1)
        assert len(data) == opened.st_size and len(data) <= limit
    return data, oct(stat.S_IMODE(opened.st_mode))
def digest(data):
    return hashlib.sha256(data).hexdigest()
def manifest(path, expected):
    data, _ = bounded(path, 1048576)
    assert digest(data) == expected
    files = json.loads(data)['files']
    for name, row in files.items():
        content, mode = bounded(ROOT / name, row['bytes'])
        assert digest(content) == row['sha256'].removeprefix('sha256:')
        assert len(content) == row['bytes'] and mode == row['mode'], name
    return len(files)
counts = {'proposal': manifest(PROOF / 'evidence/diagnostic-148768/proposal-manifest.json', 'a223215b85a844aa6c94e28a6cb18bc840894fd7c769d24b0ef81a24a53cdb78'), 'accepted_runner': manifest(PROOF / 'prepared-147109/candidate-manifest.json', '94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2')}
data, mode = bounded(Path('/tmp/w71879-148686-provider-package.json'), 65536)
assert mode == '0o644' and len(data) == 1476
assert digest(data) == '204e690591b935992fff95f6d2af6aeac86be074719da7900f1c4e4056f37efe'
copy, _ = bounded(PROOF / 'evidence/diagnostic-148768/provider-package.json', 65536)
assert data == copy
def pairs(rows):
    result = {}
    for key, value in rows:
        assert key not in result, key
        result[key] = value
    return result
def reject_constant(value):
    raise ValueError(value)
metadata = json.loads(data.decode('utf-8'), object_pairs_hook=pairs, parse_constant=reject_constant)
assert metadata['name'] == '@anthropic-ai/claude-code' and metadata['version'] == '2.1.247'
assert metadata['bin']['claude'] == 'bin/claude.exe'
assert metadata['scripts']['postinstall'] == 'node install.cjs'
assert 'cli-wrapper.cjs' in metadata['files']
destinations = ['/tmp/w71879-148768-provider-install.cjs', '/tmp/w71879-148768-provider-cli-wrapper.cjs', '/tmp/w71879-148768-provider-claude.exe']
for name in destinations:
    assert not os.path.lexists(name), name
result = {'claim': 148792, 'counts': counts, 'metadata_sha256': digest(data), 'metadata_bytes': len(data), 'metadata_mode': mode, 'metadata': metadata, 'destinations_absent': destinations, 'seconds': time.monotonic() - start, 'scope': 'Static metadata and custody only; no provider execution, copy, credentials, streams or model call. Container posture independently inspected through Docker.'}
(OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
