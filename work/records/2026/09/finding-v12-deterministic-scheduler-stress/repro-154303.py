"""Replay retained real receipts through current exporter, with labelled synthetic mutations."""
import copy,json
from pathlib import Path
from types import SimpleNamespace
from tests.tools import scheduler_trace as st
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions
outer=TheComposedOwnersSupplyAuthorizedTransitions()
raw=json.loads((Path(__file__).parent/'review-154259-repro.log').read_text())['actual_receipts']
proposal=raw[0]['proposal_id']
answers={}
for mode in ('original','rejected_review','late_review','foreign_scope','missing_decision_generation','wrong_decision_role'):
    rows=copy.deepcopy(raw)
    for row in rows:
        if row['kind']!='review':continue
        if mode=='rejected_review':row['disposition']='changes-requested'
        if mode=='late_review':row['recorded_at']='2026-09-12T17:30:00.000Z'
        if mode=='foreign_scope':row['decision']['effective_scope']='scope:elsewhere'
        if mode=='missing_decision_generation':row['decision']['policy_generation']=None
        if mode=='wrong_decision_role':row['decision']['role']='integrate'
    rows.sort(key=lambda r:(r['recorded_at'],r['kind']))
    trace=st.Trace(st.Scenario(name=mode,jobs=[],workers=[]))
    outer.authorized(SimpleNamespace(authority=SimpleNamespace(receipts=lambda _:rows)),trace,proposal)
    answers[mode]={'records':trace.records,'violations':st.validate(trace.artifact())}
print(json.dumps(answers,indent=2))
assert not answers['original']['violations']
assert any(v['code']=='nonaccepting-authorization' for v in answers['rejected_review']['violations'])
assert any(v['code']=='out-of-order' for v in answers['late_review']['violations'])
