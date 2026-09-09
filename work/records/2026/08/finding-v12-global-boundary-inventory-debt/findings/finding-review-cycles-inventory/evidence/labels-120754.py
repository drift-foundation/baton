import json,time
from pathlib import Path
from tests.manager import test_boundary_inventory as b
start=time.monotonic()
rows=[]
for site,table,column in (("checkpoint_of","line_checkpoints","fence"),("integration_checkpoint","integration_eligibility","verdict_id")):
    case=b.EveryProbeProvesItArrived();case.setUp()
    entry=("adopted","review_cycles.py:"+site,table+"."+column)
    try:
        try:case.spoiling_review_row(site,table,column)()
        except b.ContractRefusal as r:rows.append(dict(entry=entry,stimulus=case.SPOILED["json" if column=="fence" else "identity"],actual=[r.category,r.code,r.message],discovered=b.layer_labels(entry)))
    finally:case.doCleanups()
case=b.EveryProbeProvesItArrived();case.setUp()
try:
    case.review_cycle_world()
    case.corrupt("UPDATE line_checkpoints SET fence = ?",json.dumps({"intent":[],"fenced":{}}))
    try:b.review_cycles.checkpoint_of(case.store,"checkpoint-probe")
    except b.ContractRefusal as r:rows.append(dict(stimulus="JSON-valid fence with list intent",actual=[r.category,r.code,r.message]))
finally:case.doCleanups()
report=dict(rows=rows,seconds=time.monotonic()-start)
with Path(__file__).with_suffix(".json").open("x") as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
