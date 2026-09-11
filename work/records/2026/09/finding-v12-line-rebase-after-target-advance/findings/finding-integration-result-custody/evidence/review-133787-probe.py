"""Bounded independent counterexamples over disposable v12 fixture stores.

No live coordination database is accessed. Fixture cleanup owns its resources.
"""
import json
from pathlib import Path
from tests.integration.test_reconciliation import ResultCase, INTEGRATOR
from baton_v12.integration import reconciliation as r
from baton_v12.contracts import ContractRefusal

results = {}

def run(name, probe):
    case = ResultCase()
    try:
        case.setUp()
        results[name] = probe(case)
    finally:
        case.doCleanups()

def forged_owners(c):
    submission = dict(c.submission, source_proposal_id='never-published',
                      source_checkpoint_id='never-created', source_verdict_id='never-reviewed')
    held = c.prepare(submission=submission)
    evidence = {kind:c.evidence(kind, actor, held=held) for kind,actor in (
        ('verification','unconfigured.verifier'), ('review',INTEGRATOR),
        ('approval','unconfigured.approver'))}
    authorized = r.record_result_evidence(c.store, result_id=held['result_id'], **evidence)
    published = c.publish(authorized)
    account = r.resolve_import_account(c.store, c.profile, result_id=held['result_id'])
    assert published['state'] == 'published'
    assert account['source_proposal_id'] == 'never-published'
    return {'state':published['state'], 'source_proposal_id':account['source_proposal_id'],
            'invented_evidence':evidence, 'integration_assignment':c.assignment,
            'derived_proposal':c.authority.proposal(published['derived_proposal_id'])}

def bytes_collision(c):
    first = c.prepare()
    passed = c.observe(c.materialize(c.workspace, first['prepared']['head']))
    evidence = {kind:c.evidence(kind, actor, held=first) for kind,actor in (
        ('verification','baton.verifier'),('review','baton.reviewer'),('approval','baton.approver'))}
    r.record_result_evidence(c.store, result_id=first['result_id'], **evidence)
    c.advance('scale.py', 'SCALE = 2\n')
    second = c.prepare()
    failed = c.observe(c.materialize(c.workspace, second['prepared']['head']))
    assert first['prepared']['tree'] != second['prepared']['tree']
    assert first['content_digest'] == second['content_digest']
    assert passed['returncode'] == 0 and failed['returncode'] != 0
    authorized = r.record_result_evidence(c.store, result_id=second['result_id'], **evidence)
    assert authorized['state'] == 'authorized'
    return {'first_tree':first['prepared']['tree'], 'second_tree':second['prepared']['tree'],
            'same_content_digest':first['content_digest'], 'first_observation':passed,
            'second_observation':failed, 'reused_evidence':evidence, 'second_state':authorized['state']}

def journal_binding(c):
    held = c.authorize(c.prepare())
    result_id = held['result_id']
    raw = c.row(result_id,'prepared')
    edited = json.loads(raw)
    edited['head'] = 'f'*40
    edited['tree'] = 'e'*40
    c.edit(result_id,'prepared',json.dumps(edited))
    accepted_head = r.result_of(c.store,result_id)['prepared']['head']
    assert accepted_head == 'f'*40
    c.edit(result_id,'prepared',raw)
    published = c.publish(held)
    c.edit(result_id,'evidence','{}')
    account = r.resolve_import_account(c.store,c.profile,result_id=result_id)
    assert account['evidence'] == {}
    c.edit(result_id,'state','imported')
    invented_terminal = r.result_of(c.store,result_id)
    assert invented_terminal['state'] == 'imported' and invented_terminal['entry_id'] is None
    return {'authorized_reader_accepted_head':accepted_head,
            'published_import_account_evidence':account['evidence'],
            'invented_terminal_state':invented_terminal['state'],
            'invented_terminal_entry_id':invented_terminal['entry_id']}

def replay(c):
    held = c.prepare()
    assert c.prepare() == held
    c.authorize(held)
    answers = {}
    for label, call in [('prepare_after_authorize',c.prepare),
                        ('same_evidence_retry',lambda:c.authorize(held))]:
        try:
            call()
            answers[label] = {'unexpected_success':True}
        except ContractRefusal as exc:
            answers[label] = {'category':exc.category,'code':exc.code,'message':exc.message}
    assert all('message' in answer for answer in answers.values())
    return answers

run('unproved_sources_and_owner_evidence',forged_owners)
run('different_bytes_reuse_passed_evidence',bytes_collision)
run('later_state_journal_binding',journal_binding)
run('exact_retries_after_progress',replay)
print(json.dumps(results,indent=2))
