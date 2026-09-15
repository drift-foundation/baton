"""Adversarial host-answer binding checks through real disposable owners."""
import copy,json
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
from tools import stage_execution
from baton_v12.integration import reconciliation,target_of

results=[]
for corrupt in (False,True):
    case=tests.TheComposedHostVerificationUsesTheJobsCeiling()
    try:
        case.setUp();case._watching(failing=True)
        observe=stage_execution._CausalObserver.observe;answers=[]
        def observing(owner,basis):
            answer=observe(owner,basis)
            if corrupt and reconciliation.is_failed_observation(answer['observations']):
                answer=copy.deepcopy(answer)
                answer['observations'].update(seconds=999999)
            answers.append(copy.deepcopy(answer));return answer
        with patch.object(stage_execution._CausalObserver,'observe',observing):
            held=case.case.integrating(result_judgment_workers=case.case.judgment_workers())
            case.case.drive_job(held.job,held.composed,'job-a','integration','completed',ticks=4)
            for _ in range(4):case.case.tick(held)
        assert len(answers)==1,answers
        deployment=case.case.deployment_of(held.composed)
        row=reconciliation.result_of(deployment.integration,answers[0]['result_id'])
        failure=row['causal_observations']
        assert row['state']=='blocked',row['state']
        if corrupt:
            assert failure['seconds']==999999,failure
        else:
            assert failure['input_tree']==row['prepared']['tree']!=failure['input_commit'],failure
        results.append({'case':'corrupt-causal-accepted' if corrupt else 'actual-causal-tree-corrected','state':row['state'],'prepared':row['prepared'],'failure':failure,'actual_subprocess_seconds':[one[1] for one in case.seen]})
    finally:case.doCleanups()

case=tests.TheComposedHostVerificationUsesTheJobsCeiling()
try:
    case.setUp();verify=stage_execution._ImportedVerifier.verify_imported;adopt=reconciliation.adopt_failed_post_import;adopted=[]
    def verifying(owner,basis):
        answer=verify(owner,basis)
        if reconciliation.is_failed_observation(answer):
            answer.update(seconds=999999)
        return answer
    def adopting(answer,actor,basis):
        result=adopt(answer,actor,basis);adopted.append(copy.deepcopy(result));return result
    with patch.object(stage_execution._ImportedVerifier,'verify_imported',verifying),patch.object(reconciliation,'adopt_failed_post_import',adopting):
        held,deployment,result_id,_=case._post_import_failure(failing=True)
    assert len(adopted)==1 and adopted[0]['seconds']==999999,adopted
    results.append({'case':'corrupt-post-import-accepted','adopted_failure':adopted[0],'actual_subprocess_seconds':[one[1] for one in case.seen],'failed_host_verification_reader':reconciliation.failed_host_verification(deployment.integration,result_id)})
finally:case.doCleanups()
# Independently isolate the remaining fields against the actual held causal result.
for member, value in [('seconds', 78), ('seconds', 999999),
                      ('command', ['foreign-command']),
                      ('test_identity', 'foreign-task'),
                      ('test_digest', 'sha256:' + 'f' * 64)]:
    given = copy.deepcopy(failure)
    given['seconds'] = 77
    given[member] = value
    accepted = reconciliation._failure(given, row, given['execution'],
        phases=reconciliation.CAUSAL_PHASES, what='independent failure')
    assert accepted[member] == value
    results.append({'case': 'single-member-causal-accepted', 'member': member, 'value': value})
# The completed prefix is validated structurally but not against the held result.
unit = tests.AFailureAnswerIsBoundToTheResultItIsAbout()
unit.setUp()
prefix = {'command': ['python3', 'harness.py'], 'test_identity': 'task-1',
    'input_commit': unit.HELD['prepared']['head'], 'input_tree': unit.HELD['prepared']['tree'],
    'test_digest': 'sha256:' + '9' * 64, 'environment': reconciliation.EXECUTION_ENVIRONMENT,
    'status': 0, 'output': 'completed', 'execution': 'baton.observer', 'harness_added': False}
for member, value in [('input_commit', 'f' * 40), ('input_tree', 'f' * 40),
                      ('environment', 'foreign-environment')]:
    completed = dict(prefix, **{member: value})
    accepted = unit.accepted(phase='base', input_commit=unit.HELD['source_base'],
        input_tree='a' * 40, completed={'combined': completed}, not_run=['isolated'])
    assert accepted['completed']['combined'][member] == value
    results.append({'case': 'single-member-prefix-accepted', 'member': member, 'value': value})
print(json.dumps(results,indent=2,default=str))
