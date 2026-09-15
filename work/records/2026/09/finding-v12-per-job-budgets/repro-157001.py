"""Retained production probe plus closed nested configuration observations."""
import json
import pathlib
import runpy

prior = runpy.run_path(str(pathlib.Path(__file__).with_name('repro-156931.py')))
assert all(not item['accepted'] for item in prior['observed']), prior['observed']

malformed = prior['malformed']
observations = [
    malformed('missing boundary origin', lambda d: d['job_execution']['execution_limits']['boundaries']['provider_turn'].pop('origin')),
    malformed('unknown boundary member', lambda d: d['job_execution']['execution_limits']['boundaries']['provider_turn'].update(unknown=True)),
    malformed('boolean requested bound', lambda d: d['job_execution']['execution_limits']['requested'].update(provider_turn_seconds=True)),
    malformed('unknown requested member', lambda d: d['job_execution']['execution_limits']['requested'].update(unknown=9)),
]
print(json.dumps({'nested_configuration_observations': observations}, indent=2))
