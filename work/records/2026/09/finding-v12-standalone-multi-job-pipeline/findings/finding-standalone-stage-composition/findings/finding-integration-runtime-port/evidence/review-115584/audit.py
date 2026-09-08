"""Two bounded composed questions, under 15 seconds; no suite or live engine.

Verify the corrected release-tail/observation path, then ask whether a failed
credential preparation can reach positive quiescence through the public port.
All target and synthetic credential resources belong to fixture cleanup.
"""
import ast
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

root = Path.cwd()
here = Path(__file__).resolve().parent
old = here.parent / "review-115440/candidate"
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import driver, entries_of, lease_of
from baton_v12.worker_manager.attempts import attempt_runtime_of
from tests.tools.test_integration_worker import TheWholeIntegrationRunsThroughThisPort, ATTEMPT

names = ["tools/integration_worker.py", "tests/tools/test_integration_worker.py", "tools/parallel_test.py", "src/baton_v12/integration/driver.py", "src/baton_v12/integration/__init__.py", "tests/integration/test_driver.py"]
candidate = {}
for name in names:
    path = "v12/python/" + name
    data = (root / path).read_bytes()
    dest = here / "candidate" / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    candidate[path] = hashlib.sha256(data).hexdigest()
gate = Path("/tmp/w110774-gate4.txt").read_bytes()
(here / "gate.txt").write_bytes(gate)

def methods(path):
    result = {}
    for cls in ast.parse(path.read_text()).body:
        if isinstance(cls, ast.ClassDef):
            for node in cls.body:
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                        node.body.pop(0)
                    result[cls.name + "." + node.name] = ast.dump(node, include_attributes=False)
    return result

audits = {}
for name in ("v12/python/tests/tools/test_integration_worker.py", "v12/python/tests/integration/test_driver.py"):
    before, after = methods(old / name), methods(root / name)
    audits[name] = {"before": len(before), "after": len(after), "removed": sorted(before.keys() - after.keys()), "added": sorted(after.keys() - before.keys()), "changed": sorted(key for key in before.keys() & after.keys() if before[key] != after[key])}

def attempted(action):
    try:
        answer = action()
        return {"answer": answer}
    except Exception as error:
        return {"exception": type(error).__name__, "message": str(error)}

probes = {}
case = TheWholeIntegrationRunsThroughThisPort("run")
try:
    case.setUp()
    port, started = case.started()
    moved = case.target_place + "-moved"
    os.rename(case.target_place, moved)
    try:
        probes["failed_observation"] = attempted(lambda: port.refresh(ATTEMPT))
        probes["marker_after_failure"] = port.may_continue(started["assignment"])
    finally:
        os.rename(moved, case.target_place)
    probes["worker_exit"] = case.worker_turn()
    case.running = False
    port.refresh(ATTEMPT)
    with mock.patch.object(driver.execution, "release_lease", side_effect=ContractRefusal("refused", "precondition", "review release interruption")):
        probes["interrupted_completion"] = attempted(case.keep_going)
    probes["stranded_lease"] = lease_of(case.world.coordinator, started["assignment"]["lease_id"])["state"]
    probes["restart_tail_outcome"] = case.admit(case.port())["outcome"]
    probes["final_lease"] = lease_of(case.world.coordinator, started["assignment"]["lease_id"])["state"]
    probes["repeat_outcome"] = case.keep_going()["outcome"]
    probes["engine_starts"] = len([one for one in case.engine_calls if one[1] == "run"])
finally:
    case.doCleanups()

case = TheWholeIntegrationRunsThroughThisPort("run")
try:
    case.setUp()
    def unavailable(name, reference):
        raise ContractRefusal("policy", "denied", "review unavailable synthetic credential")
    port = case.port(credential_provider=unavailable)
    port.prepare(case.stage(), None)
    before = case.target_state()
    refused = attempted(lambda: case.admit(port))
    rows = entries_of(case.world.coordinator, case.world.target)
    initial = attempt_runtime_of(case.world.manager, ATTEMPT)["execution_runtime"]
    case.running = False
    refreshed = attempted(lambda: port.refresh(ATTEMPT))
    probes["credential_failure"] = {"admission": refused, "initial_runtime": initial, "entry_states": [row["state"] for row in rows], "refresh": refreshed, "final_runtime": attempt_runtime_of(case.world.manager, ATTEMPT)["execution_runtime"], "engine_starts": len([one for one in case.engine_calls if one[1] == "run"]), "target_unchanged": before == case.target_state()}
finally:
    case.doCleanups()

result = {"claim": 115584, "at": datetime.now(timezone.utc).isoformat(), "candidate": candidate, "test_audit": audits, "gate_sha256": hashlib.sha256(gate).hexdigest(), "gate_tail": gate.decode().splitlines()[-4:], "probes": probes}
(here / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
