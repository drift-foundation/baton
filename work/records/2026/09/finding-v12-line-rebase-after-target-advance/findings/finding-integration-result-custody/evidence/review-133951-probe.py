"""Focused review of candidate133842; disposable v12 fixtures only."""
import copy
import json
from tests.integration.test_reconciliation import ResultCase, SOURCE_OWNERS
from baton_v12.integration import reconciliation as r
from baton_v12.contracts import ContractRefusal

answers = {}

def refused(action):
    try:
        value = action()
    except Exception as exc:
        return {"exception": type(exc).__name__, "category": getattr(exc, "category", None),
                "code": getattr(exc, "code", None), "message": str(exc)}
    raise AssertionError(f"expected refusal, got {value!r}")

def run(name, action):
    c = ResultCase()
    try:
        c.setUp()
        answers[name] = action(c)
    finally:
        c.doCleanups()

def corrections_and_terminal(c):
    held = c.prepare()
    obs = c.observations(held)
    authorized = c.authorize(held, observations=obs)
    assert c.prepare() == authorized
    assert c.authorize(held, observations=obs) == authorized
    raw = c.row(held['result_id'], 'prepared')
    altered = json.loads(raw)
    altered.update(head='f' * 40, tree='e' * 40)
    c.edit(held['result_id'], 'prepared', json.dumps(altered))
    prepared_refusal = refused(lambda: r.result_of(c.store, held['result_id']))
    c.edit(held['result_id'], 'prepared', raw)
    published = c.publish(authorized)
    assert c.prepare() == published
    assert c.authorize(held, observations=obs) == published
    raw_evidence = c.row(held['result_id'], 'evidence')
    c.edit(held['result_id'], 'evidence', '{}')
    evidence_refusal = refused(lambda: c.import_account(held))
    c.edit(held['result_id'], 'evidence', raw_evidence)
    receipts = c.authority.receipts(published['derived_proposal_id'])
    actual_owners = {kind: c.authority.session(actor) for kind, actor in SOURCE_OWNERS.items()}
    actual_session_refusal = refused(lambda: c.authorize(held, owners=actual_owners, observations=obs))
    # Simulate corrupted persisted input. Do not change any live database.
    # A typed reader must establish linkage independently of insert-time FK checks.
    c.store._connection.execute('PRAGMA foreign_keys = OFF')
    c.store._connection.execute("UPDATE integration_results SET state='imported', entry_id='entry-never-created' WHERE result_id=?", (held['result_id'],))
    terminal = r.result_of(c.store, held['result_id'])
    assert terminal['state'] == 'imported'
    assert c.store._connection.execute("SELECT COUNT(*) FROM entries WHERE entry_id='entry-never-created'").fetchone()[0] == 0
    return {'exact_retry_controls': 'four passed', 'prepared_tamper_refusal': prepared_refusal,
            'evidence_tamper_refusal': evidence_refusal, 'derived_authority_receipts': receipts,
            'real_evidence_session_refusal': actual_session_refusal,
            'accepted_terminal_state': terminal['state'], 'accepted_terminal_entry': terminal['entry_id']}

def old_assignment_prepare(c):
    c.session.pass_work({'expect': c.assignment, 'operation_id': 'review-release-before-prepare', 'to_route': 'impl'})
    assert c.authority.assignment_of(c.assignment['work_ref']['work_id']) is None
    held = c.prepare()
    assert held['state'] == 'prepared'
    result = {'live_assignment': None, 'prepared_assignment': held['integration_assignment'],
              'state': held['state'], 'prepared_reference': held['prepared']['reference']}
    authorized = c.authorize(held)
    result['real_publisher_final_refusal'] = refused(lambda: c.publish(authorized))
    return result

def old_assignment_and_policy_import(c):
    published = c.through_publication()
    before_generation = c.authority.policy_generation()
    c.authority.set_policy('review-policy-revision', 'advanced-after-result-authorization')
    after_generation = c.authority.policy_generation()
    assert after_generation > before_generation
    policy_account = c.import_account(published)
    c.session.pass_work({'expect': c.assignment, 'operation_id': 'review-release-after-publication', 'to_route': 'impl'})
    assert c.authority.assignment_of(c.assignment['work_ref']['work_id']) is None
    stale_account = c.import_account(published)
    return {'policy_generations': [before_generation, after_generation],
            'account_after_policy_advance': policy_account['result_id'],
            'live_assignment': None, 'account_after_release': stale_account['result_id'],
            'retained_assignment': stale_account['integration_assignment']}

def failed_causal_observation(c):
    first = c.prepare()
    first_obs = c.observations(first)
    c.authorize(first, observations=first_obs)
    c.advance('scale.py', 'SCALE = 2\n')
    second = c.prepare()
    second_obs = c.observations(second)
    assert first['content_digest'] != second['content_digest']
    assert first_obs['combined']['status'] == 0 and second_obs['combined']['status'] != 0
    failure = refused(lambda: c.authorize(second, observations=second_obs))
    after = r.result_of(c.store, second['result_id'])
    assert after['causal_observations'] is None and after['state'] == 'prepared'
    rewritten = copy.deepcopy(second_obs)
    rewritten['combined'].update(status=0, output='caller changed failure to success')
    accepted = c.authorize(second, observations=rewritten)
    assert accepted['state'] == 'authorized'
    return {'different_content_digests': [first['content_digest'], second['content_digest']],
            'actual_combined_failure': second_obs['combined'], 'failure_refusal': failure,
            'custody_after_failure': {'state': after['state'], 'observations': after['causal_observations']},
            'caller_relabel_accepted': accepted['state'],
            'verification_question': c.owners['verification'].asked[-1]}

def storage_identity(c):
    claimed_place = dict(c.place(c.workspace), inode=c.place(c.workspace)['inode'] + 1)
    held = c.prepare(workspace=claimed_place)
    assert held['workspace'] != c.place(c.workspace)
    published = c.publish(c.authorize(held))
    account = c.import_account(published)
    return {'recorded_workspace': held['workspace'], 'actual_workspace': c.place(c.workspace),
            'import_account_result': account['result_id']}

run('earlier_corrections_and_unproved_terminal', corrections_and_terminal)
run('prepare_under_released_assignment', old_assignment_prepare)
run('import_after_policy_and_assignment_advance', old_assignment_and_policy_import)
run('failed_observation_not_retained', failed_causal_observation)
run('workspace_identity_not_checked', storage_identity)
print(json.dumps(answers, indent=2))
