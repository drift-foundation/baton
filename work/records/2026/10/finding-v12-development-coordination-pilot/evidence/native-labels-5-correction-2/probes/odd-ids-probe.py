import json, sys
from tests.tools.test_connected_creation import CreateTimeWorkLabelsThroughTheRealCommand as Case
from baton_v12.authority import identity as grammar
out = []
for job_id in ['job-ü', 'job with space', 'job-' + 'x' * 300, 'j' * 160]:
    case = Case(); case.setUp()
    try:
        case.installed(jobs=[], line_declared_base='a' * 40, canonical_target_id='target-1')
        try:
            case.made(case.labelled('v12', job_id=job_id)); refusal = None
        except Exception as exc:
            refusal = type(exc).__name__ + ': ' + str(exc)[:160]
        rec = case.authority().work_creation(case.work)
        out.append({'job': job_id[:20], 'len': len(job_id), 'minted': rec is not None, 'op': rec and rec['operation_id'], 'fault': rec and grammar.opaque_id_fault(rec['operation_id']), 'refusal': refusal})
    finally:
        case.doCleanups()
# the ordinary fixture's bootstrap-made Work: its creation record
case = Case(); case.setUp()
try:
    case.installed()
    out.append({'bootstrap_record': case.authority().work_creation(case.work)})
    try:
        case.made(case.labelled('v12'))
    except Exception as exc:
        out.append({'bootstrap_refusal': str(exc)})
finally:
    case.doCleanups()
print(json.dumps(out, indent=1, ensure_ascii=False))
