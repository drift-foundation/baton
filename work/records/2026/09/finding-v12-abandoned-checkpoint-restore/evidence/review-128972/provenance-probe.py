import json
from pathlib import Path
from tests.manager.test_review_cycles import AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint as Case
from baton_v12.worker_manager import review_cycles as cycles
from baton_v12.contracts import ContractRefusal

case = Case()
case.setUp()
try:
    captured = []
    original = case.verdict
    def remember(*args):
        answer = original(*args)
        captured.append(answer)
        return answer
    case.verdict = remember
    case.abandoned()
    verdict_id = captured[0]['verdict_id']
    case.store._connection.execute(
        "UPDATE checkpoint_verdicts SET reviewer_principal = 'foreign-principal' WHERE verdict_id = ?",
        (verdict_id,))
    try:
        cycles.verdict_of(case.store, verdict_id)
        owner = 'accepted'
    except ContractRefusal as failure:
        owner = {'category': failure.category, 'code': failure.code}
    answer = case.restore()
    result = {'verdict_owner': owner, 'restore_accepted': answer['state'],
              'profile_calls': len(case.profile.restore_calls)}
    Path(__file__).with_suffix('.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
finally:
    case.tearDown()
