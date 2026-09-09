import json
from pathlib import Path
import unittest
from tests.manager.test_review_cycles import AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint as Case
from tests.manager.test_checkpoint_profiles import RestoringOneCheckoutToItsRetainedCheckpoint as ProfileCase
from baton_v12.worker_manager import review_cycles as cycles
from baton_v12.worker_manager.store import manager_signature
from baton_v12.contracts import ContractRefusal

results = {}
for mutation in ('foreign-signature-kind', 'foreign-runtime-resigned', 'foreign-schema-resigned', 'null-assignment-resigned', 'foreign-row-kind'):
    case = Case()
    case.setUp()
    try:
        held = case.interrupted_intent()
        value = json.loads(held['result'])
        kind = cycles.RESTORE_INTENT_KIND
        signature_kind = kind
        if mutation == 'foreign-signature-kind':
            signature_kind = 'foreign-kind'
        elif mutation == 'foreign-runtime-resigned':
            value['runtime_id'] = 'foreign-runtime'
        elif mutation == 'foreign-schema-resigned':
            value['schema'] = 'foreign-schema'
        elif mutation == 'null-assignment-resigned':
            value['assignment'] = None
        else:
            kind = 'foreign-kind'
        case.store._connection.execute(
            'UPDATE operations SET kind=?,signature=?,result=? WHERE operation_id=?',
            (kind, manager_signature(signature_kind, value), json.dumps(value), held['operation_id']))
        before = len(case.profile.restore_calls)
        try:
            answer = case.restore()
            outcome = answer['state']
        except ContractRefusal as ex:
            outcome = [ex.category, ex.code]
        completion = cycles.abandoned_correction_of(case.store, attempt_id=case.abandoned_attempt, generation=2)
        results[mutation] = {'outcome': outcome, 'effects': len(case.profile.restore_calls)-before, 'completion': completion}
        assert outcome == ['integrity', 'schema'], results[mutation]
        assert results[mutation]['effects'] == 0 and completion is None
    finally:
        case.tearDown()

suite = unittest.TestSuite([
    Case('test_an_interrupted_restore_finishes_under_the_same_exclusion'),
    Case('test_a_transient_profile_failure_stays_retryable'),
    ProfileCase('test_nothing_outside_the_nominated_checkout_is_named'),
])
control = unittest.TextTestRunner(verbosity=2).run(suite)
results['controls_pass'] = control.wasSuccessful()
Path(__file__).with_suffix('.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results, indent=2))
raise SystemExit(0 if control.wasSuccessful() else 1)
