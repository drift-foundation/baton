"""Independent finite-control boundary probes; deterministic stores/fake owners."""
import json
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import cancellation, job_control
from tests.job_manager.test_job_control import ControlCase, at

c=ControlCase(); c.setUp()
try:
    c.submit(); held=c.running()
    # Runtime uncertainty itself projects exceptional; it is not cessation.
    c.acts.observed('job-a/implementation',claimed_by=True,runtime={'attempt_id':held['attempt_id'],'runtime_id':'runtime-1','execution_runtime':'uncertain','cleanup':'pending','assignment':None})
    before=c.projected()['stages'][0]['state']
    tick=c.tick(10000)
    print(json.dumps({'probe':'exceptional-live-runtime','before':before,'expiry':job_control.expiry_of(c.jobs,'job-a'),'stop_orders':c.acts.cancelled,'tick_expired':tick.get('expired'),'state':c.projected()['stages'][0]['state']},indent=2))
finally:
    c.tearDown(); c.doCleanups()
c=ControlCase(); c.setUp()
try:
    c.submit(); c.running()
    c.instants.append(at(5000))
    cancellation.request(c.jobs,job_id='job-a',reason='operator after missed stage deadline')
    c.tick(5000)
    print(json.dumps({'probe':'late-operator-request','expected_first_deadline':at(4800),'expiry':job_control.expiry_of(c.jobs,'job-a'),'report':c.projected()['cancellation']},indent=2))
finally:
    c.tearDown(); c.doCleanups()
c=ControlCase(); c.setUp()
try:
    c.submit()
    tick=c.tick(-100)
    evaluation=c.evaluation()
    print(json.dumps({'probe':'rollback-before-first-sweep','timing':evaluation['timing'],'job_elapsed':evaluation['job']['elapsed_seconds'],'acts':tick['acts'],'watermark':evaluation['watermark']},indent=2))
finally:
    c.tearDown(); c.doCleanups()
