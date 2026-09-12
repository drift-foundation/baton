"""Independent candidate/static custody verification, never provider execution."""
from pathlib import Path
import ast, hashlib, json, os, stat, time
ROOT = Path('/home/sl/src/baton')
PROOF = ROOT / 'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof'
EVIDENCE = PROOF / 'evidence/diagnostic-148870'
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
def sha(data):
    return hashlib.sha256(data).hexdigest()
def manifest(path, expected):
    data, _ = bounded(path, 1048576)
    assert sha(data) == expected
    files = json.loads(data)['files']
    for name, row in files.items():
        content, mode = bounded(ROOT / name, row['bytes'])
        assert sha(content) == row['sha256'].removeprefix('sha256:')
        assert len(content) == row['bytes'] and mode == row['mode'], name
    return files
candidate = manifest(EVIDENCE / 'candidate-manifest.json', '0c13a9034aef59636214749876bb83960c18a457dc79a992cf1c6b2c15d0028f')
prior = manifest(PROOF / 'prepared-147109/candidate-manifest.json', '94d8b8e83b5d11a25edc8b91ae54e9bef98bc7a718cd8d17616784a00ea22cb2')
inherited = json.loads((EVIDENCE / 'candidate-preservation.json').read_text())['successor_inherited_unchanged']
for name in inherited:
    assert (PROOF / 'prepared-147109' / name).read_bytes() == (PROOF / 'prepared-148870' / name).read_bytes(), name
for name, expected in [('claude_agent.py', '9a16f57c516660f2ccb2ad56fc404c91bc2c575bf3dd52970f64017b1ee29955'), ('test_claude_agent.py', 'a6c6e57ad38dd9c24c6ad864080ed02f0106ce27a509631b52436c1f9bbf5dd7')]:
    assert sha((EVIDENCE / (name + '.base')).read_bytes()) == expected
def definitions(path):
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_text()).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
base_tests = definitions(EVIDENCE / 'test_claude_agent.py.base')
new_tests = definitions(ROOT / 'v12/python/tests/manager/test_claude_agent.py')
for name, value in base_tests.items():
    assert new_tests[name] == value, name
provenance = json.loads((EVIDENCE / 'static-provenance.json').read_text())
native = None
for name in ('install.cjs', 'cli-wrapper.cjs', 'claude.exe'):
    row = provenance['files'][name]
    raw, mode = bounded(Path(row['path']), 256 * 1048576 if name == 'claude.exe' else 1048576)
    assert sha(raw) == row['sha256'] and len(raw) == row['bytes'] and mode == row['mode']
    if name == 'claude.exe':
        native = raw
    else:
        assert raw == (EVIDENCE / name).read_bytes()
assert native[:6] == b'\x7fELF\x02\x01' and int.from_bytes(native[18:20], 'little') == 62
for row in provenance['slices']:
    offset = row['binary_offset']
    part = native[offset:offset + row['bytes']]
    assert sha(part) == row['sha256'] and part == (EVIDENCE / row['file']).read_bytes(), row['file']
extra = []
for needle in (b'function xr(', b'reason:"api_error"', b'2.1.247'):
    offset = native.find(needle)
    assert offset >= 0, needle
    begin, end = max(0, offset - 350), offset + 1400
    part = native[begin:end]
    name = 'source-extra-' + str(len(extra)) + '.txt'
    (OUT / name).write_bytes(part)
    extra.append({'needle': needle.decode(), 'offset': begin, 'bytes': len(part), 'sha256': sha(part), 'file': name})
result = {'claim': 148964, 'candidate_files': len(candidate), 'prior_files': len(prior), 'unchanged_successor_files': len(inherited), 'unchanged_test_definitions': len(base_tests), 'native_sha256': provenance['files']['claude.exe']['sha256'], 'source_slices': len(provenance['slices']), 'extra_slices': extra, 'seconds': time.monotonic() - start, 'scope': 'Offline static custody only; no provider execution, credentials, streams, image build or model calls.'}
(OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
