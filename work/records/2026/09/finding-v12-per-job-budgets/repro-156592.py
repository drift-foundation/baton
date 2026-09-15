"""Independent type-sensitive carrier checks; fake data, no provider."""
import json
import os
import tempfile
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import execution_limits as limits
from baton_v12.worker_manager import launch
from tests.manager.test_execution_limits import job_execution

answers = []
def author(label, configuration):
    context = job_execution(execution_limits=configuration,
                            execution_limits_digest=launch._digest(configuration))
    try:
        document = launch.launch_document(session='s', contract='c', role='r',
                                          job_execution=context)
    except ContractRefusal as refused:
        answers.append({'case': label, 'accepted': False, 'message': str(refused)})
    else:
        answers.append({'case': label, 'accepted': True,
                        'configuration': document['job_execution']['execution_limits']})

author('empty_configuration_control', {})
for label, requested, field, value in (
        ('effective_float', {'provider_turn_seconds': 60}, 'seconds', 60.0),
        ('effective_boolean', {'provider_turn_seconds': 1}, 'seconds', True),
        ('default_float', {}, 'default_seconds', 3600.0)):
    configuration = limits.resolved(requested, limits.CURRENT_GENERATION)
    configuration['boundaries']['provider_turn'][field] = value
    author(label, configuration)

with tempfile.TemporaryDirectory(prefix='w156162-review-156592-') as root:
    storage = os.path.join(root, 'launch')
    for operation in (launch.materialize, launch.adopt):
        try:
            operation(storage, attempt_id='attempt-1', session='s', contract='c',
                      role='r', job_execution=job_execution(attempt_id='other'))
        except ContractRefusal:
            answers.append({'case': operation.__name__ + '_foreign_attempt',
                            'refused': True, 'storage_exists': os.path.exists(storage)})
        else:
            raise AssertionError('foreign attempt unexpectedly accepted')
print(json.dumps(answers, indent=2))
