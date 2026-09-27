"""Trace exact adoption admissions in a disposable representative test, no source edit."""
import json,traceback,unittest
from unittest.mock import patch
from baton_v12.worker_manager import workspaces
from tests.tools.test_stage_execution import AAcceptedPRSeedsTheSuccessorOnTheSameStores as Case
trace=[]
def wrapping(name):
    original=getattr(workspaces,name)
    def observed(*args,**kwargs):
        result=original(*args,**kwargs)
        trace.append(dict(call=name,assignment=args[1],operand=args[2],answer=result,stack=[f"{f.filename}:{f.lineno}:{f.name}" for f in traceback.extract_stack(limit=9)[:-1]]))
        return result
    return observed
with patch.object(workspaces,"_admitted_adoption",wrapping("_admitted_adoption")), patch.object(workspaces,"_settled_adoption",wrapping("_settled_adoption")):
    result=unittest.TextTestRunner().run(unittest.TestSuite([Case("test_the_accepted_candidate_seeds_job_b_on_the_same_stores")]))
print(json.dumps(trace,indent=2,default=str))
raise SystemExit(not result.wasSuccessful())
