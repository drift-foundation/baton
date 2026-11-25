import json, sys, copy
R = '/var/tmp/baton-k-review-386107'
sys.path[:0] = [R + '/repo/v12/worker', R + '/repo/v12/python/src/baton_v12', R + '/repo/v12/python', R + '/repo/v12/python/src']
import codex_agent
from baton_v12 import provider_policy as policy
from baton_v12.provider_policy import attribution
from tests.manager import codex_fixtures as fixture
F = R + '/repo/v12/python/tests/manager/fixtures/codex-0.169.0/'
raw = open(F + 'turn-success.sanitized.jsonl', 'rb').read()
events = [json.loads(l) for l in raw.splitlines()]
enc = lambda ev: ('\n'.join(json.dumps(e, separators=(',', ':'), ensure_ascii=False) for e in ev) + '\n').encode()
agent = codex_agent.CodexAgent.__new__(codex_agent.CodexAgent)
term = lambda b, status=0, partial=False: agent.provider_terminal(status, b, partial=partial)['ok']
out = {'fixture_ok': term(raw), 'reencoded_ok': term(enc(events))}
def mut(f):
    e = copy.deepcopy(events); f(e); return enc(e)
out['status_1'] = term(raw, 1); out['status_True'] = term(raw, True); out['partial'] = term(raw, 0, True)
out['no_final_newline'] = term(raw[:-1]); out['truncated'] = term(raw[:-40])
out['failed_command_exit_1'] = term(mut(lambda e: e[4]['item'].update(exit_code=1)))
out['failed_status'] = term(mut(lambda e: e[4]['item'].update(status='failed', exit_code=1)))
out['file_change_item'] = term(mut(lambda e: e.insert(5, {'type': 'item.completed', 'item': {'id': 'x', 'type': 'file_change', 'changes': [], 'status': 'completed'}})))
out['reasoning_item'] = term(mut(lambda e: e.insert(2, {'type': 'item.completed', 'item': {'id': 'r', 'type': 'reasoning', 'text': 't'}})))
out['error_event'] = term(mut(lambda e: e.insert(5, {'type': 'error', 'message': 'm'})))
out['turn_failed_end'] = term(mut(lambda e: e.__setitem__(6, {'type': 'turn.failed', 'error': {'message': 'm'}})))
out['extra_member_model'] = term(mut(lambda e: e[6].update(model='gpt-6-astra')))
out['turn_context_in_stdout'] = term(mut(lambda e: e.insert(2, json.load(open(F + 'turn-context.projection.json')))))
out['two_turn_completed'] = term(mut(lambda e: e.append(copy.deepcopy(e[6]))))
out['ends_on_command'] = term(mut(lambda e: e.pop(5)))
out['text_with_U2028'] = term(mut(lambda e: e[5]['item'].update(text='line one line two')))
out['text_with_U0085'] = term(mut(lambda e: e[2]['item'].update(text='a\u0085b')))
out['output_with_formfeed_escaped'] = term(mut(lambda e: e[4]['item'].update(aggregated_output='a\fb')))
out['terminal_text_inside_output'] = term(mut(lambda e: e[4]['item'].update(aggregated_output='{"type":"turn.completed"}\n')))
# Attribution under a synthetic Codex delivery.
with fixture.simulated(policy):
    d = fixture.delivered(policy)
    ctx = open(F + 'turn-context.projection.json', 'rb').read()
    claude_shape = b'{"type":"result","subtype":"success","is_error":false,"modelUsage":{"fixture-reported":{}},"model":"fixture-reported"}'
    with_model = mut(lambda e: e[6].update(model='fixture-reported'))
    for name, b in (('fixture', raw), ('turn_context', ctx), ('claude_shaped', claude_shape), ('stdout_plus_context', raw + ctx), ('model_member_in_terminal', with_model)):
        r = attribution.record(d, phase='implementation', evidenced_build='0.169.0', raw=b)
        out['attr_' + name] = [r['outcome'], r['contributors'], r['contributor_sources']]
    out['participation_sources'] = d['contract']['adapter']['participation_sources']
    forged = dict(attribution.record(d, phase='implementation', evidenced_build='0.169.0', raw=raw), outcome='matched', contributors=['fixture-reported'], contributor_sources={'fixture-reported': ['turn_context.model']})
    try: attribution.validate(forged, d, phase='implementation', raw=raw); out['forged_matched_record'] = 'ACCEPTED'
    except policy.PolicyRefusal as e: out['forged_matched_record'] = 'refused: ' + str(e)
out['production_codex'] = ['codex' in policy.REALIZATIONS, 'codex' in policy.MANAGED, [k for k in policy.PARTICIPATION if k[0] == 'codex']]
json.dump(out, open(R + '/probe.json', 'w'), indent=1); print(json.dumps(out, indent=1))
