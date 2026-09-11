import json
from pathlib import Path
from tests.job_manager.test_recovery import OneAbandonedCorrectionEpisodeIsReplaced as Case
from baton_v12.job_manager import episodes
from baton_v12.job_manager.store import job_signature
from baton_v12.contracts import ContractRefusal

results = {}
for scenario in ('foreign-job-and-episode', 'missing-historical-ending', 'foreign-correction-signature'):
    case = Case()
    case.setUp()
    try:
        case.abandoned()
        if scenario == 'foreign-correction-signature':
            operation_id = episodes.correction_operation_id('job-a', case.checkpoint_id)
            record = case.jobs.operation_record(operation_id)
            operands = json.loads(record['signature'])['operands']
            case.jobs._connection.execute(
                'UPDATE operations SET signature=? WHERE operation_id=?',
                (job_signature('foreign-kind', operands), operation_id))
        else:
            first = case.restart()
            if scenario == 'foreign-job-and-episode':
                altered = dict(first, job_id='foreign-job', episode=999)
                case.jobs._connection.execute(
                    'UPDATE operations SET result=? WHERE operation_id=?',
                    (json.dumps(altered), first['operation_id']))
            else:
                case.jobs._connection.execute(
                    'UPDATE episodes SET ended_state=NULL,ended_revision=NULL,ended_at=NULL '
                    'WHERE stage_id=? AND episode=?',
                    (first['stage_id'], first['episode']))
        try:
            results[scenario] = {'returned': case.restart()}
        except ContractRefusal as ex:
            results[scenario] = {'refusal': [ex.category, ex.code]}
    finally:
        case.doCleanups()

Path(__file__).with_suffix('.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results, indent=2))
