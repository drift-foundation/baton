"""Actual base/isolated no-status faults through composed result custody."""
import copy
import json
import os
import subprocess
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
from tools import stage_execution
from baton_v12.integration import reconciliation

results = []
for phase, failing_call in [('base', 2), ('isolated', 3)]:
    for reason in ('timeout', 'start-failed'):
        case = tests.TheComposedHostVerificationUsesTheJobsCeiling()
        try:
            case.setUp()
            argv = list(case.required_argv())
            home = os.path.realpath(case.case.deployment_of(case.case._composed).integration_root)
            actual_run = subprocess.run
            actual_observe = stage_execution._CausalObserver.observe
            calls, answers = [], []
            def run(command, **options):
                where = options.get('cwd')
                if list(command) == argv and where and os.path.realpath(where).startswith(home):
                    calls.append({'argv': list(command), 'seconds': options.get('timeout')})
                    if len(calls) == failing_call:
                        if reason == 'timeout':
                            raise subprocess.TimeoutExpired(command, options['timeout'])
                        raise FileNotFoundError('injected host command start failure')
                return actual_run(command, **options)
            def observe(owner, basis):
                answer = actual_observe(owner, basis)
                answers.append(copy.deepcopy(answer))
                return answer
            with patch.object(subprocess, 'run', run), patch.object(stage_execution._CausalObserver, 'observe', observe):
                held = case.case.integrating(result_judgment_workers=case.case.judgment_workers())
                case.case.drive_job(held.job, held.composed, 'job-a', 'integration', 'completed', ticks=4)
                for _ in range(4):
                    case.case.tick(held)
            assert len(answers) == 1, answers
            deployment = case.case.deployment_of(held.composed)
            row = reconciliation.result_of(deployment.integration, answers[0]['result_id'])
            failure = row['causal_observations']
            assert row['state'] == 'blocked', row['state']
            assert failure['phase'] == phase and failure['reason'] == reason, failure
            assert len(calls) == failing_call and all(one['seconds'] == 77 for one in calls), calls
            order = list(reconciliation.CAUSAL_PHASES)
            assert sorted(failure['completed']) == sorted(order[:order.index(phase)])
            assert failure['not_run'] == order[order.index(phase) + 1:]
            results.append({'phase': phase, 'reason': reason, 'calls': calls,
                            'state': row['state'], 'failure': failure})
        finally:
            case.doCleanups()
print(json.dumps(results, indent=2))
