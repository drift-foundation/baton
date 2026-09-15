"""Public-owner snapshots at the candidate's actual interruption points."""
import pathlib, unittest, json
from baton_v12.job_manager.integration_capacity import integration_capacity_of, preparation_intent_of
from baton_v12.worker_manager import attempt_runtime_of, frozen_output_of
from baton_v12.worker_manager.intake import intake_receipt_of
repo=pathlib.Path('/home/sl/src/baton')
path=repo/'v12/python/tests/tools/test_managed_preparation.py'
source=path.read_text()
source=source.replace('cut_reached.append(cut)', 'cut_reached.append(cut)\n                        snapshot(cut, held, preparation, args, kwargs)')
def snapshot(cut, held, preparation, args, kwargs):
    orchestration=kwargs.get('orchestration_id')
    if orchestration is None:
        orchestration=next((a['orchestration_id'] for a in args if isinstance(a,dict) and 'orchestration_id' in a),None)
    if orchestration is None:
        orchestration=preparation.started[-1]['intent']['orchestration_id']
    intent=preparation_intent_of(held.job, orchestration)
    capacity=integration_capacity_of(held.job, orchestration)
    result={'cut':cut,'intent':intent is not None,'capacity':capacity is not None}
    if intent:
        result['child_creation']=held.composed.deployment.authority.work_creation(intent['execution_work_id']) is not None
        member=next(m for m in intent['plan'] if m['phase']=='prepare')
        attempt=member['execution_attempt_id']
        runtime=attempt_runtime_of(held.control,attempt)
        result['runtime']={k:runtime[k] for k in ('runtime_id','execution_runtime','cleanup') if k in runtime} if runtime else None
        result['frozen']=frozen_output_of(held.control,attempt) is not None
        result['intake']=intake_receipt_of(held.control,attempt) is not None
        if cut in ('launch','dispatch','conclude'):
            result['exchange']=args[0].observe(args[1])['exchange']
    print('POSITION '+json.dumps(result,sort_keys=True),flush=True)
namespace={'__name__':'position_probe','__file__':str(path),'snapshot':snapshot}
exec(compile(source,str(path),'exec'),namespace)
case=namespace['OneManagedPreparationCompletes']
names=['test_committed_intent_resumes_its_own_child_work_creation','test_created_child_work_resumes_before_capacity_registration','test_start_intent_resumes_when_the_adapter_never_answers','test_the_worker_answer_resumes_before_output_is_frozen','test_frozen_output_resumes_through_intake_and_attachment']
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(case(n) for n in names))
raise SystemExit(not result.wasSuccessful())
