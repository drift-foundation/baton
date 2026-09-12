"""Independent custody check only; reads repository artifacts, never live stores."""
from pathlib import Path
import hashlib
import json
import os
import stat
import time

REPO = Path('/home/sl/src/baton')
HERE = Path(__file__).resolve().parent
PROOF = HERE.parent.parent

def read(path):
    path = Path(path)
    assert path.is_absolute() and '..' not in path.parts
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        item = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        with os.fdopen(item, 'rb') as stream:
            mode = os.fstat(stream.fileno()).st_mode
            assert stat.S_ISREG(mode)
            raw = stream.read(16 * 1024 * 1024 + 1)
            assert len(raw) <= 16 * 1024 * 1024
            return raw, oct(stat.S_IMODE(mode))
    finally:
        os.close(fd)

def sha(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()

started = time.monotonic()
manifests = {
    'accounting-150501': ('690fcb9a3a550508da903e85a49da68068f8b2be5641900098d040da4067472e', 75),
    'run9-freeze-150125': ('aa78787caaf0796d303c703bc745e758d46e67dde671a6668d6e95de3b9ac5a2', 198),
    'run9-budget-150384': ('ffdedc1de2a95502350f20147a6e3013627d0fe4a8b8da8dc69912637f915c19', 19),
}
counts = {}
for name, (expected, count) in manifests.items():
    raw, _ = read(PROOF / 'evidence' / name / 'candidate-manifest.json')
    assert sha(raw) == 'sha256:' + expected, name
    files = json.loads(raw)['files']
    assert len(files) == count
    for locator, binding in files.items():
        rel = Path(locator)
        assert not rel.is_absolute() and '..' not in rel.parts
        data, mode = read(REPO / rel)
        assert sha(data) == binding['sha256'] and len(data) == binding['bytes'], locator
        if 'mode' in binding:
            assert mode == binding['mode'], locator
    counts[name] = count
markers = {
    'selected-images.json': 'd0da4684accfa0cba16dc712d2456745de56ef3632f315a7c17a6649407a8f5f',
    'execution-review.json': 'a91d806c71c07e344698569dd44522f80775c888ac2d28606dc519ef448beeb9',
}
for name, expected in markers.items():
    assert sha(read(PROOF / 'prepared-150007' / name)[0]) == 'sha256:' + expected
    assert not os.path.lexists(PROOF / 'prepared-150501' / name)
source = json.loads(read(PROOF / 'evidence/accounting-150501/preservation.json')[0])['source_contracts']
for name, expected in source.items():
    assert sha(read(REPO / name)[0]) == expected, name
report = {'claim': 150586, 'manifest_files_verified': counts, 'old_markers_verified': 2,
          'partial_package_execution_markers_absent': True, 'source_contracts_verified': source,
          'seconds': time.monotonic() - started,
          'scope': 'Custody and static missing-contract triage only; no accounting acceptance or live execution.'}
(HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
cost = {'current_listed_seconds': report['seconds'], 'cumulative_listed_preparation_seconds': 50.928639052884776 + report['seconds'],
        'nine_failed_runtime_walls_seconds': 2002.0388815780316,
        'uncertainty': 'Untimed CLI/static review, earlier failed utility, host/operator, billing and rounding costs remain additional.'}
(HERE / 'spending.json').write_text(json.dumps(cost, indent=2) + '\n')
print(json.dumps({'verification': report, 'spending': cost}, indent=2))
