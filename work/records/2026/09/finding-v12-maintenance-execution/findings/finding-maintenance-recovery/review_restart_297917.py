import collections,sys,unittest
from tests.tools.test_correction_restart import UsefulCorrection
errors=collections.Counter()
def trace(frame,event,arg):
    name=frame.f_code.co_filename
    if event=="call":
        return trace if "/baton_v12/job_manager/" in name or name.endswith(("stage_execution.py","integration_worker.py","single_worker.py")) else None
    if event=="exception" and arg[0].__name__=="ContractRefusal":
        errors[(name.rsplit("/",1)[-1],frame.f_code.co_name,frame.f_lineno,str(arg[1]))]+=1
    return trace
sys.settrace(trace)
result=unittest.TextTestRunner().run(unittest.TestSuite([UsefulCorrection("test_useful_correction_reaches_managed_target")]))
sys.settrace(None)
for key,count in errors.most_common(16): print("RAISED",count,key)
raise SystemExit(not result.wasSuccessful())
