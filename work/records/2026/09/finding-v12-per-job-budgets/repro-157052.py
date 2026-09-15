"""Retained reader regressions, metadata association, imported verifier seam."""
import json
import pathlib
import runpy
import subprocess
from types import SimpleNamespace

prior = runpy.run_path(str(pathlib.Path(__file__).with_name('repro-157001.py')))
assert all(not item['accepted'] for item in prior['observations'])
malformed = prior['malformed']
observations = [
    malformed('provider bound names verification setting', lambda d: d['job_execution']['execution_limits']['boundaries']['provider_turn'].update(setting='verification_command_seconds')),
    malformed('provider effective30 contradicts requested60', lambda d: d['job_execution']['execution_limits']['boundaries']['provider_turn'].update(seconds=30)),
    malformed('provider origin compatibility contradicts explicit request', lambda d: d['job_execution']['execution_limits']['boundaries']['provider_turn'].update(origin='compatibility')),
]
print(json.dumps({'association_observations': observations}, indent=2))

import integration_workload as workload
from tests.tools.test_execution_limits import delivery, baton_worker

results = []
for requested, expected in [({'verification_command_seconds': 120}, 120), ({}, 1800)]:
    doc = delivery(**requested)
    doc['role'] = 'integrator'
    doc = workload.checked_launch(baton_worker.launched(doc))
    seconds = workload.launch_verification_seconds(doc)
    for mode in ('success', 'timeout', 'start-error'):
        captured = []
        def runner(argv, **options):
            captured.append(options['timeout'])
            if mode == 'timeout':
                raise subprocess.TimeoutExpired(argv, options['timeout'])
            if mode == 'start-error':
                raise FileNotFoundError('injected')
            return SimpleNamespace(returncode=0)
        answer = workload.run_verification('/unused-target', ['fake-verification'], run=runner, seconds=seconds)
        assert captured == [expected], captured
        if mode == 'success':
            assert answer['status'] == 0, answer
        elif mode == 'timeout':
            assert answer['status'] is None and f'{expected}s' in answer['why'], answer
        else:
            assert answer['status'] is None and 'could not be started' in answer['why'], answer
        results.append({'requested': requested, 'mode': mode, 'timeout': captured, 'result': answer})
print(json.dumps({'imported_verification_runner_seam': results}, indent=2))
