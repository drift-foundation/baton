"""Uncovered final-state edges: restored deletion and nonregular replacement.

Two bounded one-off real-process probes, not a repeat of the author's suite.
"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
sys.path[:0] = [str(REPO / 'v12/python'), str(REPO / 'v12/python/src')]
from tests.manager import test_integration_worker as fixture

def probe(kind):
    case = fixture.WorldCase('run')
    case.setUp()
    try:
        operation = 'delete' if kind == 'restored-deletion' else 'add'
        case.bundle(operation=operation)
        reviewed = case.reviewed()
        entries = [(reviewed, case.ORIGINAL, 0o644)] if operation == 'delete' else []
        target = Path(case.target(entries=entries, repository=False))
        if operation == 'delete':
            script = f'from pathlib import Path\nPath({reviewed!r}).write_bytes({case.ORIGINAL!r})\n'
        else:
            script = f'from pathlib import Path\np=Path({reviewed!r})\np.unlink()\np.symlink_to("harness.py")\n'
        (target / 'harness.py').write_text(script)
        status = case.entry(target=str(target))
        observed = case.observed()
        path = target / reviewed
        return {'case': kind, 'entry_status': status, 'provider_turns': len(case.commands), 'exists': path.exists(), 'symlink': path.is_symlink(), 'observed': observed}
    finally:
        case.doCleanups()

result = {'boundary': 'real entry, provider process, completed verification process, public result parser; plain target and injected revision; no engine or live model', 'cases': [probe(k) for k in ('restored-deletion', 'symlink-replacement')]}
result['parent_hashes_after'] = {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest() for p in ('v12/worker/integration_workload.py', 'v12/worker/integration_entry.py', 'v12/python/tests/manager/test_integration_worker.py')}
(HERE / 'probe.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
