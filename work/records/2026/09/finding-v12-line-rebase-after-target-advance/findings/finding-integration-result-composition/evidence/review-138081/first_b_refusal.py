"""Independent first deferred B tick; real test stores/Git, disclosed injected engine/provider."""
import json
from tests.tools import test_stage_execution as T
case=T.TwoBoundJobsTraverseServingAndCorrection("test_BOTH_JOBS_REACH_TERMINAL_ON_ONE_TARGET")
case.setUp()
try:
    held=case.integrating()
    case.drive_job(held.job,held.composed,"job-a","integration","completed",ticks=4)
    for n in range(4):
        report=case.tick(held)
        rows=[one for key in ("started","spoken","refused") for one in report.get(key,[]) if one.get("stage_id")=="job-b/integration"]
        if rows:
            print(json.dumps({"tick":n,"B":rows},indent=2))
            break
    else:
        raise AssertionError("No B execution event observed")
finally:
    case.doCleanups()
