import sys, json, tempfile, os
sys.path.insert(0, "/home/sl/src/baton/v12/worker")
import reconciliation_task as task
from baton_v12.integration import managed_execution as managed
from baton_v12.job_manager import execution_limits
lim = execution_limits.resolved(None, execution_limits.CURRENT_GENERATION)
held = json.loads(json.dumps(managed.preparation_request(
    orchestration_id="o1", canonical_target_id="t1", job_id="job-a",
    line_id="line-b", source_proposal_id="p1",
    source={"base":"a"*40,"candidate":"c"*40,"target_revision":"d"*40},
    authority={"path_set_digest":"sha256:"+"1"*64,"test_scope_digest":"sha256:"+"2"*64},
    harness_digest="sha256:"+"h"*64, profile_digest="sha256:"+"p"*64,
    input_digest="sha256:"+"i"*64, execution_limits=lim,
    commands=["combined","base","isolated"])))
name = sorted(held["execution_limits"]["boundaries"])[0]
def both(label, doc):
    try: managed.adopt_preparation_request(doc); m="ACCEPTS"
    except Exception: m="refuses"
    root = tempfile.mkdtemp()
    json.dump(doc, open(os.path.join(root, task.REQUEST_NAME), "w"))
    try: task.read_request(root); w="ACCEPTS"
    except task.PreparationRefusal: w="refuses"
    print(f"  {label:34} manager={m:8} worker={w:8} {'AGREE' if m==w else '>>> DISAGREE'}")
L=held["execution_limits"]
both("units->minutes", dict(held, execution_limits=dict(L, units="minutes")))
both("generation->999", dict(held, execution_limits=dict(L, compatibility_generation=999)))
b=dict(L["boundaries"]); b[name]=dict(b[name], seconds=b[name]["seconds"]+1)
both("one resolved seconds +1", dict(held, execution_limits=dict(L, boundaries=b)))
both("the unmodified real document", held)
