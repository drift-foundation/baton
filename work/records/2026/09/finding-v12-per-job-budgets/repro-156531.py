"""Independent launch-authoring negatives; no provider or live store."""
import json
import tempfile
from baton_v12.worker_manager import launch
from tests.manager.test_execution_limits import job_execution

answers = []
for label, config in (
        ('empty_configuration', {}),
        ('unsupported_units_and_negative_seconds', {
            'units': 'minutes', 'scope': 'cumulative',
            'compatibility_generation': 999, 'requested': {},
            'boundaries': {'provider_turn': {'seconds': -1}}})):
    context = job_execution(execution_limits=config,
                            execution_limits_digest=launch._digest(config))
    held = launch.launch_document(session='s', contract='c', role='r',
                                  job_execution=context)
    answers.append({'case': label, 'accepted': True,
                    'configuration': held['job_execution']['execution_limits']})

with tempfile.TemporaryDirectory(prefix='w156162-review-156531-') as root:
    context = job_execution(attempt_id='attempt-other')
    made = launch.materialize(root, attempt_id='attempt-1', session='s',
                              contract='c', role='r', job_execution=context)
    adopted = launch.adopt(root, attempt_id='attempt-1', session='s',
                           contract='c', role='r', job_execution=context)
    answers.append({'case': 'contradictory_attempt_binding',
                    'delivery_attempt': made.attempt_id,
                    'context_attempt': made.document['job_execution']['attempt_id'],
                    'adopted': adopted is not None})
print(json.dumps(answers, indent=2))
