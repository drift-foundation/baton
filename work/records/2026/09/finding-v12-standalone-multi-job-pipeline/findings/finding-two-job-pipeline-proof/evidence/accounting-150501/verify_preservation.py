"""Read old accepted custody and source contracts; no live state or execution."""
import hashlib
import json
from pathlib import Path
import time
HERE = Path(__file__).resolve().parent
REC = HERE.parent.parent
REPO = next(p for p in REC.parents if (p / 'v12/python/src/baton_v12').is_dir())
started = time.monotonic()
counts = {}
for manifest in ('evidence/run9-freeze-150125/candidate-manifest.json', 'evidence/run9-budget-150384/candidate-manifest.json'):
    files = json.loads((REC / manifest).read_text())['files']
    for name, expected in files.items():
        raw = (REPO / name).read_bytes()
        assert 'sha256:' + hashlib.sha256(raw).hexdigest() == expected['sha256'], name
        assert len(raw) == expected['bytes'], name
    counts[manifest] = len(files)
for name, expected in (('selected-images.json', 'd0da4684accfa0cba16dc712d2456745de56ef3632f315a7c17a6649407a8f5f'), ('execution-review.json', 'a91d806c71c07e344698569dd44522f80775c888ac2d28606dc519ef448beeb9')):
    assert hashlib.sha256((REC / 'prepared-150007' / name).read_bytes()).hexdigest() == expected
    assert not (REC / 'prepared-150501' / name).exists()
contracts = {}
for name in ('v12/python/src/baton_v12/worker_manager/store.py', 'v12/python/src/baton_v12/worker_manager/workspaces.py', 'v12/python/src/baton_v12/worker_manager/exchange.py', 'v12/python/src/baton_v12/worker_manager/launch.py', 'v12/python/src/baton_v12/integration/store.py', 'v12/python/tools/stage_execution.py'):
    contracts[name] = 'sha256:' + hashlib.sha256((REPO / name).read_bytes()).hexdigest()
answer = {'unchanged_files': counts, 'old_markers_unchanged': 2, 'new_execution_markers_absent': True, 'source_contracts': contracts, 'seconds': time.monotonic() - started}
(HERE / 'preservation.json').write_text(json.dumps(answer, indent=2) + '\n')
print(json.dumps(answer, indent=2))
