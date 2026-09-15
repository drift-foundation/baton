"""Check the revised regression and bind observed provider calls to attempts."""
import json
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
import claude_agent
case=tests.AReopenedServingKeepsBothJobsLaunchesUntouched('test_a_reopened_serving_adopts_the_same_two_deliveries')
calls=[]
original=claude_agent.ClaudeAgent._provider
def provider(agent,*args,**kwargs):
    context=agent._seen['job_execution']
    calls.append({'job_id':context['job_id'],'attempt_id':context['attempt_id'],'bound':agent._bound(agent._seen,'provider_turn',claude_agent.PROVIDER_SECONDS)})
    return original(agent,*args,**kwargs)
try:
    case.setUp()
    with patch.object(claude_agent.ClaudeAgent,'_provider',provider):
        case.test_a_reopened_serving_adopts_the_same_two_deliveries()
    assert [(one['job_id'],one['bound']) for one in calls]==[('job-a',31),('job-b',67)],calls
    assert len({one['attempt_id'] for one in calls})==2,calls
    print(json.dumps({'author_reopen_and_continuation_assertions':'passed','provider_calls_including_sweeps':calls},indent=2))
finally:
    case.doCleanups()
