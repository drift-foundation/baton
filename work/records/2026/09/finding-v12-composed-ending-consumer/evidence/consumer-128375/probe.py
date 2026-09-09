import json
from pathlib import Path
from tests.tools.test_stage_execution import OrdinaryTerminalLifecycle

method = "test_fresh_process_observes_owned_completion_after_serving_closes"
case = OrdinaryTerminalLifecycle(method)
try:
    case.setUp()
    getattr(case, method)()
    Path(__file__).with_name("readonly.json").write_text(json.dumps(case.readonly_evidence, indent=2) + "\n")
    print(json.dumps({"method": method, "state": case.readonly_evidence["observation"]["state"],
                      "handles": case.readonly_evidence["handles"], "checks": case.readonly_evidence["checks"]}, indent=2))
finally:
    case.doCleanups()
