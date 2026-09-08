"""Historical cleanup proof through actual public custody; private fixture damage."""
import copy
import json
from pathlib import Path
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import integration_checkpoint
from tests.job_manager.test_review_driver import TheWorkerCompletionTraversesPublicCustody as Case

def probe(mode):
    f = Case('test_actual_completion_reaches_first_verdict_and_public_custody')
    try:
        f.setUp()
        held = f.produced()
        ended = f.end(held)
        assert ended['outcome'] == 'accepted'
        op = held['adapter'].destroyed_with[0]['operation']['operation_id']
        original = json.loads(f.control.operation_record(op)['result'])
        changed = copy.deepcopy(original)
        if mode == 'empty_custody':
            changed['directory_custody'] = {}
        elif mode == 'scalar_custody':
            changed['directory_custody'] = 'not-a-receipt'
        elif mode == 'missing_workspace_custody':
            changed['directory_custody'].pop('workspace')
        elif mode == 'foreign_custody':
            changed['directory_custody']['workspace']['attempt_id'] = 'another-attempt'
        if mode != 'unchanged':
            f.control._connection.execute('UPDATE operations SET result = ? WHERE operation_id = ?', (json.dumps(changed), op))
        with f.no_more_external_acts(held):
            try:
                eligible = integration_checkpoint(f.control, ended['line_id'])
                accepted = True
                reason = None
            except ContractRefusal as exc:
                eligible, accepted, reason = None, False, str(exc)
            replay = f.end(held)
        return {'eligibility_accepted': accepted, 'reason': reason, 'replay_outcome': replay['outcome'],
                'replay_cleaned_up': replay['cleaned_up'], 'replay_equal': replay == ended,
                'original_custody': original['directory_custody'], 'tested_custody': changed['directory_custody'],
                'destroy_calls': len(held['adapter'].destroyed_with), 'worker_turns': f.worker_turns}
    finally:
        f.doCleanups()

results = {mode: probe(mode) for mode in ('unchanged', 'empty_custody', 'scalar_custody', 'missing_workspace_custody', 'foreign_custody')}
Path(__file__).with_name('probe.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({k: {name: v[name] for name in ('eligibility_accepted', 'replay_outcome', 'replay_cleaned_up', 'replay_equal')} for k,v in results.items()}, indent=2))
