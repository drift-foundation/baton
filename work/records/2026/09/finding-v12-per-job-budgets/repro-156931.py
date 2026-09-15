"""Independent worker-reader probes and real adapter runner seam, no provider.

Calls production _provider/_ran_provider and _verify/_ran. Only subprocess.run
and provider environment preparation are replaced. This is not whole-work()
composition, real credential preparation, or OS descendant termination evidence.
"""
import json
import os
import subprocess
from types import SimpleNamespace

from tests.tools.test_execution_limits import delivery, baton_worker, claude_agent, launch


def malformed(name, mutate):
    doc = delivery(provider_turn_seconds=60, verification_command_seconds=45)
    mutate(doc)
    context = doc['job_execution']
    context['execution_limits_digest'] = launch._digest(context['execution_limits'])
    try:
        baton_worker.launched(doc)
    except baton_worker.WorkerFault as error:
        return {'case': name, 'accepted': False, 'error': str(error)}
    agent = claude_agent.ClaudeAgent()
    return {'case': name, 'accepted': True,
            'provider_seconds': agent._bound(doc, 'provider_turn', 3600)}


observed = [
    malformed('unknown transport', lambda d: d.update(transport='unknown/channel')),
    malformed('missing provider boundary', lambda d: d['job_execution']['execution_limits']['boundaries'].pop('provider_turn')),
    malformed('non-text job identity', lambda d: d['job_execution'].update(job_id=False)),
    malformed('wrong units', lambda d: d['job_execution']['execution_limits'].update(units='minutes')),
]
print(json.dumps({'reader_observations': observed}, indent=2), flush=True)

captured = []
mode = 'success'


def runner(argv, **options):
    captured.append({'argv': argv, 'timeout': options['timeout'], 'mode': mode})
    if mode == 'timeout':
        raise subprocess.TimeoutExpired(argv, options['timeout'])
    if mode == 'start-error':
        raise FileNotFoundError('injected runner start failure')
    return SimpleNamespace(returncode=0)


agent = claude_agent.ClaudeAgent(run=runner)
agent._revalidated_environment = lambda scratch, env: env
task = {'verification': ['fake-verification']}
outcomes = []
for settings, expected in [({'provider_turn_seconds': 60, 'verification_command_seconds': 45}, (60, 45)),
                           ({'provider_turn_seconds': 17, 'verification_command_seconds': 23}, (17, 23)),
                           ({}, (3600, 900))]:
    agent._seen = baton_worker.launched(delivery(**settings))
    for mode in ('success', 'timeout', 'start-error'):
        before = len(captured)
        provider = agent._provider(task, '/unused-candidate', '/unused-scratch', {}, prompt='fixed fake prompt')
        verification = agent._verify(task, '/unused-candidate', {}, ())
        actual = tuple(item['timeout'] for item in captured[before:])
        assert actual == expected, (settings, mode, actual, expected)
        if mode == 'success':
            assert provider['ok'] and verification['status'] == 0
        elif mode == 'timeout':
            assert provider['failure_reason'] == claude_agent.PROVIDER_TIMED_OUT
            assert f'{expected[0]}s' in provider['why']
            assert verification['status'] is None
            assert f'did not finish within {expected[1]}s' in verification['text']
        else:
            assert provider['failure_reason'] == claude_agent.PROVIDER_START_ERROR
            assert verification['status'] is None and 'could not be started' in verification['text']
        outcomes.append({'settings': settings, 'mode': mode, 'timeouts': actual,
                         'provider': provider, 'verification': verification})
print(json.dumps({'production_runner_seam_outcomes': outcomes, 'captured_calls': len(captured)}, indent=2))
