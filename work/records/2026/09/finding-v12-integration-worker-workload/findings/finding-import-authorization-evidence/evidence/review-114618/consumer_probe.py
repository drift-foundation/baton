"""Check provider admission for the four reported parent incompatibilities."""
import copy
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[8]
sys.path[:0] = [str(REPO / 'v12/python'), str(REPO / 'v12/python/src')]
from tests.manager import test_integration_worker as fixture


def run_case(mode):
    case = fixture.WorldCase('run')
    case.setUp()
    try:
        case.bundle(operation='add')
        evidence = copy.deepcopy(fixture.contract.read_bundle(case.published['root'])['evidence'])
        if mode == 'disposition':
            evidence['review.json']['disposition'] = 'changes-requested'
        elif mode == 'missing_documents':
            evidence['authority.json']['review']['documents'] = []
        elif mode == 'scope':
            evidence['authority.json']['scope']['scope_digest'] = 'sha256:' + '9' * 64
        elif mode == 'verdict':
            evidence['review.json']['verdict_id'] = 'verdict-somebody-elses'
        root = case.derived(documents=evidence)
        status = case.entry(bundle=root, target=case.target(repository=False))
        return {'case': mode, 'entry_status': status, 'provider_turns': len(case.commands), 'observed': case.observed()}
    finally:
        case.doCleanups()


out = {'boundary': 'Real producer/entry/parser, derived malformed evidence, plain disposable target and revision seam; no Git, engine or provider process',
       'cases': [run_case(m) for m in ('disposition', 'missing_documents', 'scope', 'verdict')]}
(HERE / 'consumer-probe.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
