import json
import shutil
from pathlib import Path
import unittest
from tests.manager import test_checkpoint_profiles as git_tests
from tests.manager.test_review_cycles import AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint as Case
from baton_v12.worker_manager import review_cycles as cycles
from baton_v12.worker_manager.store import manager_signature
from baton_v12.contracts import ContractRefusal

results={}
case=git_tests.RestoringOneCheckoutToItsRetainedCheckpoint()
case.setUp()
try:
    case.dirty()
    original=Path(case.repository)
    foreign=original.with_name('foreign')
    moved=original.with_name('moved')
    shutil.copytree(original,foreign)
    (foreign/'kept.txt').write_text('foreign scratch\n')
    real=case.runner
    def replacing(argv):
        if argv[3]=='reset':
            original.rename(moved)
            original.symlink_to(foreign,target_is_directory=True)
        return real(argv)
    case.profile=git_tests.GitCheckpointProfile(replacing)
    answer=case.profile.restore_checkpoint(case.repository,case.evidence)
    results['path']={'accepted':answer==case.evidence,
        'foreign_preserved':(foreign/'kept.txt').read_text()=='foreign scratch\n',
        'original_restored':(moved/'kept.txt').read_text()=='the corrected candidate\n'}
finally:
    case.tearDown()

case=Case()
case.setUp()
try:
    case.abandoned()
    answer=case.restore()
    op=answer['operation_id'];record=case.store.operation_record(op)
    result=json.loads(record['result']);signature=json.loads(record['signature'])
    result['runtime_id']='foreign-runtime';signature['operands']['runtime_id']='foreign-runtime'
    case.store._connection.execute('UPDATE operations SET result=?,signature=? WHERE operation_id=?',
        (json.dumps(result),manager_signature(signature['kind'],signature['operands']),op))
    try:
        cycles.abandoned_correction_of(case.store,attempt_id=case.abandoned_attempt,generation=2)
        results['foreign_runtime']='accepted'
    except ContractRefusal as ex:
        results['foreign_runtime']=[ex.category,ex.code]
finally:
    case.tearDown()

case=Case()
case.setUp()
try:
    case.abandoned()
    case.profile.restore_refusal=ContractRefusal('refused','precondition','interrupted')
    try:
        case.restore()
    except ContractRefusal:
        pass
    case.profile.restore_refusal=None
    row=case.store._connection.execute('SELECT operation_id FROM operations WHERE kind=?',
        (cycles.RESTORE_INTENT_KIND,)).fetchone()
    record=case.store.operation_record(row['operation_id'])
    signed=json.loads(record['signature'])
    case.store._connection.execute('UPDATE operations SET signature=? WHERE operation_id=?',
        (manager_signature('foreign-kind',signed['operands']),row['operation_id']))
    before=len(case.profile.restore_calls)
    try:
        answer=case.restore();outcome=answer['state']
    except ContractRefusal as ex:
        outcome=[ex.category,ex.code]
    results['foreign_intent_signature']={'outcome':outcome,'effects':len(case.profile.restore_calls)-before}
finally:
    case.tearDown()

namespace=dict(git_tests.__dict__)
exec(Path(__file__).with_name('proposed_test.py').read_text(),namespace)
Proposed=type('Proposed',(git_tests.RestoringOneCheckoutToItsRetainedCheckpoint,),
    {'test_nothing_outside_the_nominated_checkout_is_named':namespace['test_nothing_outside_the_nominated_checkout_is_named']})
suite=unittest.TestSuite([Proposed('test_nothing_outside_the_nominated_checkout_is_named'),
    Case('test_two_overlapping_connections_produce_exactly_one_effect'),
    Case('test_an_admission_during_the_restore_stops_the_completion'),
    Case('test_an_unfinished_retry_re_proves_its_provenance_first'),
    Case('test_the_reader_still_follows_its_owners_after_a_later_round')])
control=unittest.TextTestRunner().run(suite)
results['controls_pass']=control.wasSuccessful()
Path(__file__).with_suffix('.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
raise SystemExit(0 if control.wasSuccessful() else 1)
