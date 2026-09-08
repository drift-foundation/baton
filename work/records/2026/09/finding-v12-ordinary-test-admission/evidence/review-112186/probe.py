"""Receipt-boundary probes using retained manifests and recorded external seams.

These are substitution probes, not a real worker/custody acceptance proof.
No production/test source or authoritative coordination store is changed.
"""
import copy
import json
from pathlib import Path
from unittest import mock
from baton_v12.integration import driver
from baton_v12.contracts import ContractRefusal
from tests.integration.test_driver import TheAdmissionNeedsActualOrdinaryTestEvidence as Case, ReceiptSession

def probe(mode):
    f = Case('test_the_producers_own_observation_is_resolved_from_custody')
    try:
        f.setUp()
        if mode == 'foreign_generation':
            f.proposal['assignment_ref']['generation'] += 1
        elif mode == 'foreign_participant':
            f.proposal['assignment_ref']['participant'] = 'baton.other'
        elif mode == 'foreign_work':
            f.proposal['assignment_ref']['work_ref']['work_id'] = '01234567-W999'
        elif mode == 'foreign_base':
            f.proposal['target'] = 'e' * 40
        elif mode in ('failed', 'unrun'):
            f.observed = {'status': 1 if mode == 'failed' else None}
            f.retain()
        sessions = [ReceiptSession('baton.verify', 'verify'), ReceiptSession('baton.review', 'review'), ReceiptSession('baton.approve', 'approve')]
        with mock.patch.object(driver, 'integration_checkpoint', return_value=copy.deepcopy(f.accepted)), \
                mock.patch.object(driver, 'checkpoint_of', return_value={'writer_id': 'writer-1'}), \
                mock.patch.object(driver, 'writer_of', return_value={'runtime_attempt_id': 'attempt-1'}), \
                mock.patch.object(driver, 'frozen_output_of', return_value={'result_id': f.result['result_id'], 'disposition': 'completed', 'manifest_digest': f.result_digest}), \
                mock.patch.object(driver, '_assignment', return_value=f.assignment):
            try:
                answer = driver._accepted_receipts(f.store, f.authority, *sessions, line_id='line-1', proposal_id='proposal-1', policy_generation=3, required_tests=f.required)
                outcome = {'accepted': True, 'receipts': answer[2]}
            except ContractRefusal as exc:
                outcome = {'accepted': False, 'reason': str(exc)}
        return dict(outcome, actual_assignment=f.assignment, proposal_assignment=f.proposal['assignment_ref'], proposal_target=f.proposal['target'], observed_base=f.claim['base'], calls={name: session.calls for name, session in zip(('verify', 'review', 'approve'), sessions)})
    finally:
        f.doCleanups()

results = {mode: probe(mode) for mode in ('unchanged', 'foreign_generation', 'foreign_participant', 'foreign_work', 'foreign_base', 'failed', 'unrun')}
Path(__file__).with_name('probe.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({mode: {'accepted': x['accepted'], 'calls': {name: len(calls) for name, calls in x['calls'].items()}} for mode, x in results.items()}, indent=2))
