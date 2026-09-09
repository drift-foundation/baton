"""Budget2s: prove same-sweep outcomes and inspect the actual attempt claims."""
import hashlib
import json
import pathlib
import stat
import time

from baton_v12.worker_manager import claimed_offers_for
from tests.tools.test_stage_execution import TwoIndependentlyBoundWorkersShareOneSweep

started = time.monotonic()
fixture = TwoIndependentlyBoundWorkersShareOneSweep()
result = {}
try:
    fixture.setUp()
    held = fixture.serving_pair()
    reports = fixture.ticks(held)
    result['claim_ticks'] = [[{'stage': act['stage_id'], 'outcome': act['outcome']} for act in report['acts'] if act.get('act') == 'claim'] for report in reports]
    result['attempts'] = []
    for row in held.job._connection.execute('SELECT stage_id, attempt_id FROM episodes ORDER BY stage_id'):
        result['attempts'].append({'stage': row['stage_id'], 'actual_attempt_claims': len(claimed_offers_for(held.control, row['attempt_id']))})
    result['participant_selector_claims'] = len(claimed_offers_for(held.control, 'baton.claude'))
    result['states'] = fixture.states(held)
finally:
    fixture.doCleanups()
result['elapsed_seconds'] = time.monotonic() - started
root = pathlib.Path('/home/sl/src/baton/v12/python')
expected = json.loads(pathlib.Path(__file__).with_name('adapter-125239.json').read_text())['paths']
result['candidate'] = {}
for name, recorded in expected.items():
    path = root / name
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    result['candidate'][name] = {'sha256': sha, 'mode': oct(stat.S_IMODE(path.stat().st_mode)), 'matches': sha == recorded['sha256']}
print(json.dumps(result, indent=2))
