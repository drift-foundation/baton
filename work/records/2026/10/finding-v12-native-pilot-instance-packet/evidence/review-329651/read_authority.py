"""Owner-side diagnostic readback only: no transitions, schema repair or launch."""
import json
from baton_v12.authority import Authority
root = '/home/sl/baton-instances/native-coordination-pilot-w321608-1'
a = Authority.open_readonly(root + '/db/authority.sqlite3', expected_authority_uuid='1cdb8d19feda47c0a209bd0669b16871')
try:
    people = ['baton.claude-pilot', 'baton.reviewer-pilot', 'baton.slaw', 'baton.verifier-pilot', 'baton.reviewer-receipt-pilot', 'baton.diagnostician-pilot']
    answer = {'work': a.project_work('1cdb8d19-W1'), 'dossier': a.dossier_of('1cdb8d19-W1'), 'policy_generation': a.policy_generation(), 'principals': {who: a.principal_of(who) for who in people}, 'capabilities': {who: {cap: a.holds_capability(who, cap, scope='scope:native-pilot-quickstart') for cap in ['verify', 'review', 'approve', 'integrate', 'close']} for who in people}}
    print(json.dumps(answer, indent=2))
finally:
    a.dispose()
