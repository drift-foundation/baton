"""Fresh setup-only policy pin contrast; no running deployment is changed."""
import json
from tests.tools import test_scheduler_trace as cases
from baton_v12.authority import Authority

class FreshPolicy(cases.TheComposedOwnersSupplyAuthorizedTransitions):
    def four_works(self):
        super().four_works()
        authority=Authority.open_readonly(self.case.authority_path,expected_authority_uuid=self.case.config['authority_uuid'])
        try:
            self.case.fixture_policy=authority.policy_generation()
        finally:
            authority.dispose()

case=FreshPolicy('test_three_jobs_code_and_are_reviewed_and_the_edge_then_opens')
try:
    case.setUp()
    held=case.four_job_deployment(own_workers=True,ticks=7)
    trace=case.blank()
    for job in ('job-a','job-c','job-d'):
        attempt=case.attempt_of(held,job+'/implementation')
        assert case.case.turn(held.control,'implementation',attempt,case.case.mounted_at(held.composed,attempt),edits={'harness.py':f"print('the {job} producer answered')\n"})==0
        case.observing(held,trace,job,'implementation','completed',job_ids=case.FOUR,ticks=8)
    for job in ('job-a','job-c','job-d'):
        case.observing(held,trace,job,'review','waiting',job_ids=case.FOUR,ticks=14)
        case.case.review_turn(held,job,case.attempt_of(held,job+'/review'),'accepted')
        case.observing(held,trace,job,'review','completed',job_ids=case.FOUR,ticks=18)
    states={job:case.case.states_for(held.job,held.composed,job) for job in case.FOUR}
    assert states['job-b']['implementation']!='blocked',states
    print(json.dumps({'configured_policy':case.case.fixture_policy,'current_policy':case.case.deployment_of(held.composed).authority.policy_generation(),'states':states,'observed_ticks':trace._tick},indent=2),flush=True)
finally:
    case.doCleanups()
