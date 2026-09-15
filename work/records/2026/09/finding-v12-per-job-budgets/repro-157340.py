"""Independent deterministic correction checks; no provider child or sleeps."""
import json
import os
import subprocess
from tests.tools import test_execution_limits as cases
from baton_v12.job_manager import submission
from baton_v12.worker_manager import attempt_runtime_of
import claude_agent
import integration_contract
import integration_entry

case = cases.TheDirectIntegrationCarriesItsJobsOwnCeiling()
try:
    case.setUp()
    foreign = case._foreign_job()
    try:
        case._started(job_id=foreign)
    except Exception as failed:
        assert foreign in str(failed) and 'job-a' in str(failed), str(failed)
        state = attempt_runtime_of(case.fixture.world.manager, case.attempt)
        assert state['execution_runtime'] == 'not-started', state
        print(json.dumps({'foreign_refusal': str(failed), 'runtime': state['execution_runtime']}), flush=True)
    else:
        raise AssertionError('foreign Job admitted')
finally:
    case.doCleanups()

case = cases.TheDirectIntegrationCarriesItsJobsOwnCeiling()
try:
    case.setUp()
    _, answer = case._started()
    assert answer['outcome'] == 'running'
    doc = case._materialized()
    bundle = os.path.join(case.fixture.root, 'bundles', case.attempt)
    taken = integration_contract.read_bundle(bundle)
    assert doc['job_execution']['job_id'] == taken['evidence']['authority.json']['scope']['job_id'] == 'job-a'
    captured = []
    def runner(argv, **options):
        captured.append(options['timeout'])
        raise subprocess.TimeoutExpired(argv, options['timeout'])
    agent = claude_agent.ClaudeAgent(run=runner)
    agent._scratch = lambda: '/unused-scratch'
    agent._child_environments = lambda scratch: {'provider': {}}
    agent._revalidated_environment = lambda scratch, env: env
    launch_place = os.path.join(case.fixture.place('worker'), 'launch.json')
    with open(launch_place, 'w') as stream:
        json.dump(doc, stream)
    os.chmod(launch_place, 0o444)
    delivery = case.fixture.delivery()
    rc = integration_entry.main(agent=agent, launch_place=launch_place,
        assignment_root=delivery.assignment_root, result_root=delivery.result_root,
        bundle_root=bundle, target_root=case.fixture.target_place,
        scratch=case.fixture.place('probe-scratch'),
        revision=lambda place: taken['envelope']['eligibility']['expected_target_revision'])
    result = case._result()
    assert rc == 0 and captured == [60], (rc, captured, result)
    assert result['outcome'] == 'held' and result['detail']['reason'] == 'provider-failed', result
    assert agent._seen is None
    print(json.dumps({'entry_exit': rc, 'provider_timeouts': captured, 'result': result}), flush=True)
    # Same adapter, alternating valid deliveries and omission. Failure handling
    # restores prior context rather than retaining this integration's settings.
    sentinel = cases.delivery(provider_turn_seconds=77)
    agent._seen = sentinel
    for seen, expected in [(cases.delivery(provider_turn_seconds=17), 17), (None, 3600), (doc, 60), (cases.delivery(), 3600)]:
        outcome = agent.invoke_provider(prompt='deterministic probe', room=case.fixture.target_place, seen=seen)
        assert not outcome['ok'] and outcome['failure_reason'] == claude_agent.PROVIDER_TIMED_OUT, outcome
        assert captured[-1] == expected, captured
        assert agent._seen is sentinel
    print(json.dumps({'interleaved_provider_timeouts': captured, 'prior_context_restored': True}), flush=True)
    try:
        submission.boundary_seconds(case.fixture.world.jobs, 'job-never-admitted', 'host_verification')
    except Exception as failed:
        assert 'job-never-admitted' in str(failed), str(failed)
        print(json.dumps({'unknown_job_refusal': str(failed)}), flush=True)
    else:
        raise AssertionError('unknown Job defaulted')
finally:
    case.doCleanups()
