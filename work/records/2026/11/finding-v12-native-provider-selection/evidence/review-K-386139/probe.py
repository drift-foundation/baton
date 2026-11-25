import json, sys, copy
R = sys.argv[1]
sys.path[:0] = [R + '/v12/worker', R + '/v12/python/src/baton_v12', R + '/v12/python', R + '/v12/python/src']
from baton_v12 import provider_policy as policy
from baton_v12.provider_policy import attribution as A
from tests.manager import codex_fixtures, provider_fixtures as fixture
out = {}
# Claude /1 byte shape, comparable between base and candidate trees.
given = fixture.delivery()
out['claude'] = {k: A.record(given, phase='review', evidenced_build='2.1.247', raw=fixture.terminal(*n)) for k, n in (('matched', ['fixture-reported', 'other']), ('conflicting', ['other']), ('missing', []))}
out['claude_diag'] = A.diagnostic(out['claude']['matched'])
if not hasattr(A, 'CONFIGURED_SCHEMA'):
    print(json.dumps(out, sort_keys=True)); sys.exit(0)
from baton_v12.provider_policy import codex
raw = open(R + '/v12/python/tests/manager/fixtures/codex-0.169.0/turn-success.sanitized.jsonl', 'rb').read()
ev = [json.loads(l) for l in raw.split(b'\n') if l]
enc = lambda e: ('\n'.join(json.dumps(x, ensure_ascii=False) for x in e) + '\n').encode()
def mut(f):
    e = copy.deepcopy(ev); f(e); return enc(e)
with codex_fixtures.simulated(policy):
    d, inv = codex_fixtures.configured(policy)
    rec = lambda **c: A.record(d, **{**dict(phase='implementation', evidenced_build='0.169.0', raw=raw, invocation=inv), **c})
    def val(claim, delivery=None, **c):
        try:
            v = A.validate(claim, delivery or d, **{**dict(phase='implementation', raw=raw, invocation_raw=json.dumps(inv).encode()), **c})
            return {'outcome': v['outcome'], 'acceptable': A.acceptable(v)}
        except policy.PolicyRefusal as f: return 'refused: ' + str(f)
    good = rec()
    brief = lambda v: {'outcome': v['outcome'], 'acceptable': A.acceptable(v), 'reroute': v['reroute_observation'], 'contributors': v['contributors'], 'participation': v['actual_participation']}
    out['good'] = brief(good); out['good_validated'] = val(good); out['good_diag'] = A.diagnostic(good)
    out['receipt_has_prompt_text'] = 'SYNTHETIC PRIVATE PROMPT' in json.dumps(inv) or 'SYNTHETIC PRIVATE PROMPT' in json.dumps(good)
    out['receipt_keys'] = sorted(inv); out['argv_prefix'] = inv['argv_prefix']; out['environment_policy_keys'] = sorted(inv['environment_policy'])
    # host-selected basis
    out['codex_claim_under_claude'] = val(good, given, phase='review', raw=fixture.terminal('fixture-reported'))
    out['claude_claim_under_codex'] = val(out['claude']['matched'])
    out['no_invocation_claim'] = val(rec(invocation=None), invocation_raw=None)
    out['claim_omits_invocation_but_good_outcome'] = val(dict(good, invocation=None))
    out['invented_contributor'] = val(dict(good, contributors=['fixture-reported']))
    out['participation_evidenced'] = val(dict(good, actual_participation='evidenced'))
    out['receipt_missing_on_host'] = val(good, invocation_raw=None)
    out['receipt_other_bytes_same_json'] = val(good, invocation_raw=json.dumps(inv, indent=1).encode())
    out['receipt_duplicate_member'] = val(good, invocation_raw=json.dumps(inv).encode()[:-1] + b',"status":0}')
    out['receipt_appended_twice'] = val(good, invocation_raw=json.dumps(inv).encode() * 2)
    out['build_claim_0.172'] = val(dict(good, evidenced_cli_build='0.172.0'))
    out['status_true'] = brief(rec(invocation=dict(inv, status=True)))
    out['phase_review'] = brief(A.record(d, phase='review', evidenced_build='0.169.0', raw=raw, invocation=dict(inv, phase='review')))
    # observation surface
    rr = {'type': 'item.completed', 'item': {'id': 'x', 'type': 'error', 'message': 'model rerouted: a -> b (HighRiskCyberActivity)'}}
    cases = {'reroute_mid': lambda e: e.insert(2, rr), 'reroute_after_last_message': lambda e: e.insert(len(e) - 1, rr),
             'reroute_other_reason': lambda e: e.insert(2, {'type': 'item.completed', 'item': dict(rr['item'], message='model rerouted: a -> b (Other)')}),
             'reroute_extra_member': lambda e: e.insert(2, {'type': 'item.completed', 'item': dict(rr['item'], extra=1)}),
             'config_warning_error_item': lambda e: e.insert(2, {'type': 'item.completed', 'item': dict(rr['item'], message='some warning')}),
             'top_level_error_event': lambda e: e.insert(2, {'type': 'error', 'message': 'm'}),
             'prose_mentions_reroute': lambda e: e[-2]['item'].update(text='model rerouted: a -> b (HighRiskCyberActivity)'),
             'tool_output_mentions_reroute': lambda e: [x['item'].update(aggregated_output=json.dumps(rr)) for x in e if x.get('item', {}).get('type') == 'command_execution'],
             'model_member_in_terminal': lambda e: e[-1].update(model='fixture-reported'),
             'u2028_in_text': lambda e: e[-2]['item'].update(text='a b\u0085c')}
    for k, f in cases.items(): out[k] = brief(rec(raw=mut(f)))
    out['crlf'] = brief(rec(raw=raw.replace(b'\n', b'\r\n')))
    out['no_final_newline'] = brief(rec(raw=raw[:-1])); out['partial'] = brief(rec(partial=True)); out['log_not_retained'] = brief(rec(log_retained=False))
    out['reroute_validated_on_host'] = val(rec(raw=mut(cases['reroute_mid'])), raw=mut(cases['reroute_mid']))
    out['accepted_claim_but_host_stream_rerouted'] = val(good, raw=mut(cases['reroute_mid']))
    # R1
    d2, inv2 = copy.deepcopy(d), copy.deepcopy(inv)
    d2['contract']['selection']['cli_build'] = d2['contract']['runtime_profile']['cli_build'] = '0.172.0'
    d2['profile_digest'] = policy.digest(d2['contract']['runtime_profile'])
    inv2['evidenced_cli_build'] = '0.172.0'; inv2['selection_digest'] = policy.digest(d2)
    out['R1_consistent_0.172'] = brief(A.record(d2, phase='implementation', evidenced_build='0.172.0', raw=raw, invocation=inv2))
    d3 = copy.deepcopy(d); d3['contract']['runtime_profile']['image_digest'] = 'synthetic:tag'; d3['profile_digest'] = policy.digest(d3['contract']['runtime_profile'])
    out['image_not_digest'] = brief(A.record(d3, phase='implementation', evidenced_build='0.169.0', raw=raw, invocation=dict(inv, selection_digest=policy.digest(d3))))
    out['receipt_from_other_attempt'] = brief(A.record(dict(d, attempt_id='other'), phase='implementation', evidenced_build='0.169.0', raw=raw, invocation=inv))
print(json.dumps(out, sort_keys=True, indent=1))
