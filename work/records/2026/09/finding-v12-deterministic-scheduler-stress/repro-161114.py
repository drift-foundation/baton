"""Independent current-candidate two-order review; actual owners, simulated providers."""
import json
from pathlib import Path
from tests.tools import test_scheduler_trace as T
from tools import stage_execution
record=Path(__file__).resolve().parent
for method,label in [("test_the_opened_edge_and_one_integrator_serialize_four_jobs","a_before_c"),("test_the_alternate_schedule_reaches_the_same_completions","c_before_a")]:
    case=T.TheComposedOwnersSupplyAuthorizedTransitions(method)
    case.setUp()
    saved={};answers=[]
    original=case.b_and_terminal
    owner_observe=stage_execution._CausalObserver.observe
    def capture(owner,basis):
        answer=owner_observe(owner,basis)
        answers.append(answer)
        return answer
    def retained(held,trace):
        result=original(held,trace)
        saved.update(trace=trace,states={job:case.case.states_for(held.job,held.composed,job) for job in case.FOUR})
        return result
    case.b_and_terminal=retained
    stage_execution._CausalObserver.observe=capture
    try:
        getattr(case,method)()
        artifact=saved['trace'].artifact(T.SOURCES)
        violations=T.scheduler_trace.validate(artifact)
        assert violations==[],violations
        census=case.completion_census(artifact)
        terminals={k:v for k,v in census.items() if k.endswith('/integration')}
        assert len(terminals)==4 and all(v==1 for v in terminals.values()),terminals
        assert sum(k.endswith('/implementation') or k.endswith('/review') for k in census)==8,census
        (record/f'review-161114-{label}.json').write_text(json.dumps(artifact,indent=2,default=str)+'\n')
        (record/f'review-161114-{label}-causal.json').write_text(json.dumps(answers,indent=2,default=str)+'\n')
        print(json.dumps({'order':label,'records':len(artifact['records']),'terminals':terminals,'states':saved['states'],'violations':violations,'causal_answers':len(answers)},default=str))
    finally:
        stage_execution._CausalObserver.observe=owner_observe
        case.doCleanups()
