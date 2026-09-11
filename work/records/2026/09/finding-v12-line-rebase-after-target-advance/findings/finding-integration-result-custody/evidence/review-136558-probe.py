"""Independent P milestone probe; real Git/Authority, declared Manager/Job fixture."""
import json
import unittest

from baton_v12.contracts import ContractRefusal
from tests.integration.test_reconciliation import (
    OriginalSubmissionIsImmutable, CausalEvidenceSurvivesComposition,
    TheNominatedStorageIsProved,
)


def milestone():
    case = OriginalSubmissionIsImmutable('test_preparing_publishing_and_admitting_touch_no_producer_byte')
    case.setUp()
    try:
        # Unlike the component fixture, make the actual Authority cursor agree
        # with the dedicated target that already contains A's change.
        case.authority.set_policy('canonical_target', case.advanced)
        before = case.before()
        prepared = case.prepare()
        observed = case.observe_result(prepared)
        published = case.publish(observed)
        assert published['state'] == 'published'
        assert not case.authority.receipts(published['derived_proposal_id'])
        refusals = []
        for name, act in [('adopt_missing_receipts', case.adopt), ('import_published', case.import_account)]:
            try:
                act(published)
            except ContractRefusal as exc:
                refusals.append({'boundary': name, 'refusal': str(exc)})
            else:
                raise AssertionError(name + ' accepted an unapproved candidate')
        case.receipts(published)
        authorized = case.adopt(published)
        account = case.import_account(authorized)
        assert authorized['state'] == 'authorized'
        assert case.before() == before
        assert case.authority.canonical_target() == case.advanced
        assert account['source_proposal_id'] == before['proposal']['proposal_id']
        assert authorized['source_base'] == case.base
        assert authorized['target_revision'] == case.advanced
        content = case.materialize(case.workspace, authorized['prepared']['head'])
        with open(content + '/other.py') as stream:
            assert 'the first job answered' in stream.read()
        with open(content + '/feature.py') as stream:
            assert 'sum(values)' in stream.read()
        print(json.dumps({'furthest_transition': 'authorized import account with actual Authority cursor at A',
                          'states': [prepared['state'], observed['state'], published['state'], authorized['state']],
                          'account': account, 'observations': authorized['causal_observations'],
                          'derived_receipts': case.authority.receipts(authorized['derived_proposal_id']),
                          'source_receipts_unchanged': True, 'producer_unchanged': True,
                          'refusals': refusals}, indent=2))
    finally:
        case.doCleanups()


milestone()
suite = unittest.TestSuite([
    CausalEvidenceSurvivesComposition('test_a_COMBINED_FAILURE_IS_RETAINED_and_blocks'),
    TheNominatedStorageIsProved('test_the_producers_own_line_may_not_be_the_workspace'),
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
