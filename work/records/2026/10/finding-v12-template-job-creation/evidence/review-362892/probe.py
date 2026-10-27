"""Independent deterministic counterexamples. Run on candidate overlay, PYTHONPATH=src:."""
import json
from tests.job_manager.test_creation import CreationCase, FakeBinding, JOB
from tests.job_manager.fixtures import submission, job
from baton_v12.job_manager import submit
from baton_v12.job_manager.creation import created_job_of
from baton_v12.contracts import ContractRefusal
results=[]
def run(name, action):
    case=CreationCase(); case.setUp()
    try: results.append({'case':name, **action(case)})
    finally: case.doCleanups()
def replay(c):
    c.created(); c.derivation.answer['input_digest']='sha256:'+'9'*64
    try: c.created(); return {'replayed':True}
    except ContractRefusal as e: return {'replayed':False,'code':e.code,'message':e.message}
def theft(c):
    class Stop(Exception): pass
    class Interrupted(FakeBinding):
        def create_binding(self,*args,**kwargs):
            super().create_binding(*args,**kwargs)
            raise Stop()
    c.binding=Interrupted()
    try: c.created()
    except Stop: pass
    before=created_job_of(c.jobs,JOB)
    foreign=submit(c.jobs,submission('foreign-submission',jobs=[job(JOB)]))
    try: c.created(); outcome='completed'
    except ContractRefusal as e: outcome=e.message
    return {'reserved_state':before['state'],'foreign_submission_accepted':foreign,'original_resume':outcome}
run('completed replay after deployment input changes',replay)
run('ordinary submit steals interrupted creation Job identity',theft)
print(json.dumps(results,indent=2))
