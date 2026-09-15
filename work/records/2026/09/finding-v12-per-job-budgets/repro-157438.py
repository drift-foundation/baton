"""Configured derived judgments over real composed owners and fake providers.

Only initial public submission operands are changed. Existing lifecycle
assertions and production ownership/launch/result paths are exercised intact.
"""
import copy,json
from tests.tools import test_stage_execution as fixtures
from baton_v12.job_manager import documents

class Configured(fixtures.TwoBoundJobsTraverseServingAndCorrection):
    def both_jobs(self):
        document=copy.deepcopy(super().both_jobs())
        document['schema']=documents.SUBMISSION_SCHEMA
        for job in document['jobs']:
            job['execution_limits']={'provider_turn_seconds':67 if job['job_id']=='job-b' else 31,
                                     'verification_command_seconds':43 if job['job_id']=='job-b' else 29}
        return document

    def pending_judgments(self):
        held,deployment,result_id,result=super().pending_judgments()
        observed=[]
        for (_,kind),execution in deployment.judges.items():
            worker=execution.operations._worker
            adopted=worker._adopted(execution.intent)
            document=adopted.document
            context=document['job_execution']
            assert document['schema']=='baton.worker-launch/3', document
            assert context['job_id']==execution.intent['job_id']==result['job_id']=='job-b'
            assert context['attempt_id']==execution.intent['attempt_id']
            assert context['runtime_input_digest']==execution.input['input_digest']==execution.given['input_manifest']['manifest_digest']
            assert context['runtime_policy_digest']==execution.input['policy_digest']
            assert context['runtime_input_digest']!=context['job_input_digest']
            bounds=context['execution_limits']['boundaries']
            assert bounds['provider_turn']['seconds']==67
            assert all(bounds[name]['seconds']==43 for name in ('ordinary_verification','integration_verification','host_verification'))
            observed.append({'kind':kind,'job_id':context['job_id'],'attempt_id':context['attempt_id'],
                'runtime_input_digest':context['runtime_input_digest'],'job_input_digest':context['job_input_digest'],
                'boundaries':bounds})
        assert len(observed)==3
        print(json.dumps({'configured_derived_launches':observed},indent=2),flush=True)
        return held,deployment,result_id,result

case=Configured('test_real_B_consumer_judges_frozen_reports_and_completes_both_jobs')
try:
    case.setUp()
    case.test_real_B_consumer_judges_frozen_reports_and_completes_both_jobs()
    print('Configured derived lifecycle: three judged results, both integrations complete, replay/cleanup assertions passed.',flush=True)
finally:
    case.doCleanups()
