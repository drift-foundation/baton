"""Compare the actual capacity boundary with no-status and integer failures.

Only configured host subprocess outcomes are injected. Real coordination,
admission, result custody and scheduler owners run. No capacity is released by
this probe and no runtime quiescence is invented.
"""
import json
import os
import subprocess

from baton_v12.integration import reconciliation, queue
from baton_v12.job_manager import scheduler
from tests.job_manager import fixtures
from tests.tools.test_execution_limits import TheComposedHostVerificationUsesTheJobsCeiling as Case
from tools import stage_execution

answers = []
for mode in ('timeout', 'integer-failure'):
    case = Case('test_three_jobs_bind_three_ceilings_and_three_tasks')
    case.setUp()
    try:
        if mode == 'integer-failure':
            original_watch = case._watching
            def watch(**options):
                options['failing'] = False
                original_watch(**options)
                watched = subprocess.run
                accepted = [list(one) for one in options['argvs']]
                home = os.path.realpath(options['home'])
                def integer(argv, **named):
                    where = named.get('cwd')
                    if list(argv) in accepted and where and os.path.realpath(where).startswith(home + os.sep):
                        case.seen.append((list(argv), named.get('timeout')))
                        return subprocess.CompletedProcess(argv, 1, '', 'deterministic host integer failure')
                    return watched(argv, **named)
                subprocess.run = integer
                case.addCleanup(setattr, subprocess, 'run', watched)
            case._watching = watch
        result_ids = set()
        original_prepare = reconciliation.prepare_result
        def prepare(*args, **kwargs):
            answer = original_prepare(*args, **kwargs)
            result_ids.add(answer['result_id'])
            return answer
        reconciliation.prepare_result = prepare
        case.addCleanup(setattr, reconciliation, 'prepare_result', original_prepare)
        held, deployment, blocked = case._two_failed_results()
        public_results = [reconciliation.result_of(deployment.integration, one) for one in result_ids]
        print(json.dumps({'mode': mode, 'results': public_results}, default=str), flush=True)
        blocked = {one['job_id']: one for one in public_results if one['state'] in ('blocked', 'held')}
        assert sorted(blocked) == ['job-b'], blocked
        first = blocked['job-b']
        custody = reconciliation.result_of(deployment.integration, first['result_id'])
        allocation = scheduler.allocation_of(held.job, case.case.attempted(held.job, 'job-b/integration')['attempt_id'])
        before_counts = (len(case.seen), case.materialized)
        recovered = held.composed.recover(now=fixtures.NOW)
        report = case.case.tick(held)
        deferred = [one for one in report['acts'] if one.get('stage_id') == 'job-c/integration']
        assert deferred and all(one['outcome'] == 'deferred' and 'capacity is reserved or recovery-required' in one['detail']['message'] for one in deferred), deferred
        assert recovered == {'abandoned': [], 'recoverable': []}, recovered
        assert before_counts == (len(case.seen), case.materialized)
        assert custody == reconciliation.result_of(deployment.integration, first['result_id'])
        memo = stage_execution._host_retention(deployment)
        assert len(memo) == (1 if mode == 'timeout' else 0), memo
        target = queue.target_of(deployment.integration, custody['canonical_target_id'])
        answers.append({'mode': mode, 'result_id': first['result_id'], 'job_id': first['job_id'], 'causal_observations': first['causal_observations'], 'states': {job: case.case.states_for(held.job, held.composed, job)['integration'] for job in ('job-a', 'job-b', 'job-c')}, 'allocation': allocation, 'recovered': recovered, 'deferred': deferred, 'commands_and_materializations': before_counts, 'memo_entries': len(memo), 'target_state': target['state'], 'custody_unchanged': True})
    finally:
        case.doCleanups()
print(json.dumps(answers, indent=2, default=str))
