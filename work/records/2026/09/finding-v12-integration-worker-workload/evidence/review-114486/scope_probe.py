"""Inspect the consumer's unscheduled-test boundary, using a derived bundle."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
sys.path[:0] = [str(REPO / 'v12/python'), str(REPO / 'v12/python/src')]
from tests.manager import test_integration_worker as fixture

case = fixture.WorldCase('run')
case.setUp()
try:
    case.bundle(operation='add')
    # Intentionally derived: this probes the consumer's policy, not producer
    # provenance or acceptance of this invented test change.
    row, _ = case.row('tests/test_unscheduled_review_114486.py', operation='edit')
    blobs = {}
    originals = {'base': b'def test_invariant():\n    assert False\n',
                 'candidate': b'def test_invariant():\n    assert True\n'}
    for side, payload in originals.items():
        digest = hashlib.sha256(payload).hexdigest()
        row[side].update(blob=digest, bytes=len(payload))
        blobs[digest] = payload
    root = case.derived(paths=[row], blobs=blobs)
    taken = fixture.contract.read_bundle(root)
    target = case.target(repository=False, entries=[(row['path'], originals['base'], 0o644)])
    status = case.entry(bundle=root, target=target)
    prompt = case.commands[0]['argv'][-1] if case.commands else None
    (HERE / 'scope-prompt.txt').write_text(prompt or 'NO PROVIDER\n')
    output = {'derived_bundle': True, 'entry_status': status,
              'test_scope': taken['evidence']['job.json']['test_scope'],
              'authority_rows': taken['evidence'][fixture.contract.AUTHORITY_DOCUMENT]['paths'],
              'provider_turns': len(case.commands),
              'actual_test': Path(target, row['path']).read_text(),
              'observed': case.observed(),
              'limit': 'Provider fixture executes the import and does not semantically evaluate review text; this exposes missing consumer instructions/guard and does not prove a real model would comply or producer would originate this altered evidence.'}
    (HERE / 'scope-probe.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))
finally:
    case.doCleanups()
