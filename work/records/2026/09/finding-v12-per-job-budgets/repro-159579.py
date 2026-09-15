"""Real host adoption expectations and independently changed harness digest."""
import copy
import json
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
from tools import stage_execution
from baton_v12.integration import reconciliation

results = []
foreign = 'sha256:' + 'f' * 64
validate = reconciliation._failure

def validating(given, held, actor, **kwargs):
    expected = kwargs.get('expected')
    assert expected and expected['seconds'] == 77, expected
    assert 'test_digest' not in expected, expected
    refusals = []
    for member, value in [('seconds', 78), ('seconds', 999999),
                          ('command', ['foreign-command']),
                          ('test_identity', 'foreign-task')]:
        altered = copy.deepcopy(given)
        altered[member] = value
        try:
            validate(altered, held, actor, **kwargs)
        except Exception as exc:
            assert 'this deployment configured' in str(exc), str(exc)
            refusals.append({'member': member, 'value': value})
        else:
            raise AssertionError((member, value, 'accepted'))
    accepted = validate(given, held, actor, **kwargs)
    assert accepted['test_digest'] == foreign
    results.append({'phase': given['phase'], 'actual_owner_expectations': expected,
                    'refused_substitutions': refusals,
                    'accepted_foreign_digest': accepted['test_digest']})
    return accepted

case = tests.TheComposedHostVerificationUsesTheJobsCeiling()
try:
    case.setUp()
    case._watching(failing=True)
    observe = stage_execution._CausalObserver.observe
    answers = []
    def observing(owner, basis):
        answer = observe(owner, basis)
        if reconciliation.is_failed_observation(answer['observations']):
            answer = copy.deepcopy(answer)
            assert answer['observations']['test_digest'] != foreign
            answer['observations']['test_digest'] = foreign
            answers.append(answer)
        return answer
    with patch.object(stage_execution._CausalObserver, 'observe', observing), patch.object(reconciliation, '_failure', validating):
        held = case.case.integrating(result_judgment_workers=case.case.judgment_workers())
        case.case.drive_job(held.job, held.composed, 'job-a', 'integration', 'completed', ticks=4)
        for _ in range(4):
            case.case.tick(held)
    assert len(answers) == 1
    deployment = case.case.deployment_of(held.composed)
    row = reconciliation.result_of(deployment.integration, answers[0]['result_id'])
    assert row['state'] == 'blocked'
    assert row['causal_observations']['test_digest'] == foreign
    results.append({'case': 'foreign-harness-durably-retained', 'state': row['state'],
                    'actual_seconds': [one[1] for one in case.seen]})
finally:
    case.doCleanups()

case = tests.TheComposedHostVerificationUsesTheJobsCeiling()
try:
    case.setUp()
    verify = stage_execution._ImportedVerifier.verify_imported
    def verifying(owner, basis):
        answer = verify(owner, basis)
        if reconciliation.is_failed_observation(answer):
            answer = copy.deepcopy(answer)
            assert answer['test_digest'] != foreign
            answer['test_digest'] = foreign
        return answer
    with patch.object(stage_execution._ImportedVerifier, 'verify_imported', verifying), patch.object(reconciliation, '_failure', validating):
        case._post_import_failure(failing=True)
    results.append({'case': 'foreign-harness-post-import-adopted',
                    'actual_seconds': [one[1] for one in case.seen]})
finally:
    case.doCleanups()

unit = tests.AFailureAnswerIsBoundToTheResultItIsAbout()
unit.setUp()
prefix = {'command': ['python3', 'harness.py'], 'test_identity': 'task-1',
          'input_commit': unit.HELD['prepared']['head'], 'input_tree': unit.HELD['prepared']['tree'],
          'test_digest': 'sha256:' + '9' * 64, 'environment': reconciliation.EXECUTION_ENVIRONMENT,
          'status': 0, 'output': 'completed', 'execution': 'baton.observer', 'harness_added': False}
arguments = dict(phase='base', input_commit=unit.HELD['source_base'], input_tree='a' * 40,
                 completed={'combined': prefix}, not_run=['isolated'])
assert unit.trusted(**arguments)['phase'] == 'base'
for member, value in [('input_commit', 'f' * 40), ('input_tree', 'f' * 40),
                      ('environment', 'foreign-environment')]:
    changed = copy.deepcopy(arguments)
    changed['completed']['combined'][member] = value
    try:
        unit.trusted(**changed)
    except Exception as exc:
        results.append({'prefix_refused': member, 'cause': str(exc)})
    else:
        raise AssertionError((member, 'accepted'))
print(json.dumps(results, indent=2))
