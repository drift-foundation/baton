"""One new cutpoint question: can the real Authority replay a release tail?

Budget: one disposable joined attempt, seconds. Inject failure only at release;
inspect public state and replay through both public driver entry points.
"""
import json
import sys
from pathlib import Path
from unittest import mock

root = Path.cwd()
here = Path(__file__).resolve().parent
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import driver, entries_of, lease_of
from tests.tools.test_integration_worker import TheWholeIntegrationRunsThroughThisPort, ATTEMPT

case = TheWholeIntegrationRunsThroughThisPort("run")
result = {}
def attempt(action):
    try:
        return {"outcome": action()["outcome"]}
    except ContractRefusal as error:
        return {"category": error.category, "code": error.code, "message": error.message}

try:
    case.setUp()
    port, started = case.started()
    result["worker_exit"] = case.worker_turn()
    case.running = False
    port.refresh(ATTEMPT)
    fault = ContractRefusal("refused", "precondition", "review injected release interruption")
    with mock.patch.object(driver.execution, "release_lease", side_effect=fault):
        result["first_completion"] = attempt(case.keep_going)
    def state():
        rows = entries_of(case.world.coordinator, case.world.target)
        return {"entry": next(row["state"] for row in rows if row["entry_id"] == started["entry"]), "lease": lease_of(case.world.coordinator, started["assignment"]["lease_id"])["state"]}
    result["before_replay"] = state()
    result["continue_replay"] = attempt(case.keep_going)
    result["restart_admission"] = attempt(lambda: case.admit(case.port()))
    result["after_replays"] = state()
finally:
    case.doCleanups()
(here / "release-tail.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
