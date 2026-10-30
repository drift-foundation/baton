"""Focused supplemental probe; imports the same pinned candidate overlay."""
import json
import time
from pathlib import Path
import probe
from tests.job_manager.test_fresh_attempt import FakeExclusion, ceased
start=time.monotonic()
case=probe.FreshAttemptCase()
case.setUp()
try:
    case.prior()
    value=case.admitted(exclusion=FakeExclusion(answer=ceased(token=None)))
    answer={"job_id":value["job_id"], "exclusion":value["exclusion"], "seconds":time.monotonic()-start}
    (Path(__file__).parent/'UNKNOWN-RESOURCE.json').write_text(json.dumps(answer,indent=2)+'\n')
    print(json.dumps(answer,indent=2))
finally:
    case.doCleanups()
