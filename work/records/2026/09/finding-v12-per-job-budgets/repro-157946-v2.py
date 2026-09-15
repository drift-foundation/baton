"""Run the revised author reopen regression, then continue both actual turns."""
import collections,json
from types import SimpleNamespace
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
from baton_v12.job_manager import episodes_of,stages_of,sweep
from tests.job_manager import fixtures
import claude_agent

case=tests.AReopenedServingKeepsBothJobsLaunchesUntouched('test_a_reopened_serving_adopts_the_same_two_deliveries')
compositions=[];provider_calls=[]
try:
    case.setUp()
    serving=case.case.serving_two
    def composing(**members):
        held=serving(**members);compositions.append(held);return held
    case.case.serving_two=composing
    mounts={};contexts={}
    launch_bytes=case._launch_bytes
    def retaining(stage):
        attempt=stage['attempt_id']
        if attempt not in mounts:
            mounts[attempt]=case.case.mounted_at(compositions[0][2],attempt)
            contexts[attempt]=case.case.job_execution_for('implementation',attempt)
        return launch_bytes(stage)
    case._launch_bytes=retaining
    case.test_a_reopened_serving_adopts_the_same_two_deliveries()
    assert len(compositions)==2,len(compositions)
    job,control,composed=compositions[-1]
    held=SimpleNamespace(job=job,control=control,composed=composed)
    attempts={name:episodes_of(job,next(row for row in stages_of(job,name) if row['kind']=='implementation')['stage_id'])[-1]['attempt_id'] for name in ('job-a','job-b')}
    original=claude_agent.ClaudeAgent._provider
    def provider(agent,*args,**kwargs):
        context=agent._seen['job_execution']
        provider_calls.append({'job_id':context['job_id'],'attempt_id':context['attempt_id'],'bound':agent._bound(agent._seen,'provider_turn',claude_agent.PROVIDER_SECONDS)})
        return original(agent,*args,**kwargs)
    case.case.job_execution_for=lambda role,attempt: contexts[attempt]
    with patch.object(claude_agent.ClaudeAgent,'_provider',provider):
        for name,attempt in attempts.items():
            assert case.case.turn(control,'implementation',attempt,mounts[attempt],edits={'harness.py':"print('configured reopen continuation')\n"})==0
            case.case.drive_job(job,composed,name,'implementation','completed')
        for _ in range(3):
            sweep(job,composed,now=fixtures.NOW)
    counts=collections.Counter(one['attempt_id'] for one in provider_calls)
    assert counts==collections.Counter(attempts.values()),provider_calls
    for one in provider_calls:
        assert one['bound']==(31 if one['job_id']=='job-a' else 67),one
    states={name:case.case.states_for(job,composed,name)['implementation'] for name in attempts}
    assert set(states.values())=={'completed'},states
    starts={name:len(case.starts_naming(attempt)) for name,attempt in attempts.items()}
    assert set(starts.values())=={1},starts
    print(json.dumps({'author_reopen_assertions':'passed','provider_calls':provider_calls,'implementation_states':states,'per_attempt_engine_starts':starts,'extra_replay_sweeps':3},indent=2))
finally:
    case.doCleanups()
