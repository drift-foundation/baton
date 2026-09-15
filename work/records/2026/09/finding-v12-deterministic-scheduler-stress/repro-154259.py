"""Review actual export and labelled synthetic receipt/oracle mutations."""
import copy,json
from types import SimpleNamespace
from tests.tools import scheduler_trace as st
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions
outer=TheComposedOwnersSupplyAuthorizedTransitions()
outer.setUp()
original=outer.authorized
captured={}
def capture(deployment, trace, proposal_id, **kw):
    captured['proposal_id']=proposal_id
    captured['receipts']=copy.deepcopy(deployment.authority.receipts(proposal_id))
    return original(deployment,trace,proposal_id,**kw)
outer.authorized=capture
try:
    outer.test_real_authorization_receipts_bind_actor_scope_and_subject()
    answers={'actual_receipts':captured['receipts'],'cases':{}}
    for mode in ('original','rejected_review','review_after_integration'):
        rows=copy.deepcopy(captured['receipts'])
        if mode=='rejected_review':
            for row in rows:
                if row['kind']=='review':row['disposition']='changes-requested'
        if mode=='review_after_integration':
            for row in rows:
                if row['kind']=='review':row['recorded_at']='2026-09-02T00:00:02.000Z'
                elif row['kind']=='integration':row['recorded_at']='2026-09-02T00:00:01.000Z'
            rows.sort(key=lambda r:(r['recorded_at'],r['kind']))
        trace=st.Trace(st.Scenario(name=mode,jobs=[],workers=[]))
        deployment=SimpleNamespace(authority=SimpleNamespace(receipts=lambda proposal_id:rows))
        original(deployment,trace,captured['proposal_id'])
        artifact=trace.artifact()
        answers['cases'][mode]={'records':artifact['records'],'violations':st.validate(artifact)}
    print(json.dumps(answers,indent=2))
finally:
    outer.doCleanups()
