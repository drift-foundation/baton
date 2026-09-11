from pathlib import Path
import json, time, unittest
from tests.tools.test_stage_execution import OrdinaryTerminalLifecycle, UnfinishedWorkIsFencedBeforeAnythingRepeatsIt
out=Path(__file__).parent
case=OrdinaryTerminalLifecycle("test_the_recovered_job_finishes_and_its_manifest_reopens")
result=unittest.TestResult()
start=time.monotonic()
case.run(result)
wall=time.monotonic()-start
report={"question":"Does the same recovered Job reach terminal integration and reopen corrected retained custody?", "cap_seconds":10,"wall_seconds":wall,"tests_run":result.testsRun,"errors":result.errors,"failures":result.failures,"joined":getattr(case,"joined",None)}
(out/"verification.json").write_text(json.dumps(report,indent=2,default=str)+"\n")
print(json.dumps(report,indent=2,default=str))
raise SystemExit(0 if result.wasSuccessful() else 1)
