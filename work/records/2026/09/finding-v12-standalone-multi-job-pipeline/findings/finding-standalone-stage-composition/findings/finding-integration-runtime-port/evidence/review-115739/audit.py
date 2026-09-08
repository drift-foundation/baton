"""Final delta audit and the two previous reproductions, no suite.

Budget: one disposable composed start, under ten seconds; synthetic credentials
and deterministic engine. Preserve final candidate, test and provider hashes.
"""
import ast
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

root = Path.cwd()
here = Path(__file__).resolve().parent
old = here.parent / "review-115669/candidate"
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager.attempts import attempt_runtime_of
from tests.tools.test_integration_worker import TheWholeIntegrationRunsThroughThisPort, ATTEMPT
from tools import integration_worker

candidate = {}
for relative in ["tools/integration_worker.py", "tests/tools/test_integration_worker.py", "tools/parallel_test.py", "src/baton_v12/integration/driver.py", "src/baton_v12/integration/__init__.py", "tests/integration/test_driver.py"]:
    name = "v12/python/" + relative
    data = (root / name).read_bytes()
    target = here / "candidate" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    candidate[name] = hashlib.sha256(data).hexdigest()
gate = Path("/tmp/w110774-gate6.txt").read_bytes()
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

tests = {}
for name in ("v12/python/tests/tools/test_integration_worker.py", "v12/python/tests/integration/test_driver.py"):
    before, after = methods(old / name), methods(root / name)
    tests[name] = {"before": len(before), "after": len(after), "removed": sorted(before.keys() - after.keys()), "added": sorted(after.keys() - before.keys()), "changed": sorted(key for key in before.keys() & after.keys() if before[key] != after[key])}
baseline = json.loads((here.parent / "research-115095/audit.json").read_text())
providers = {}
for name, row in baseline["provider_paths"].items():
    if name == "v12/python/tools/parallel_test.py":
        continue
    providers[name] = hashlib.sha256((root / name).read_bytes()).hexdigest() == row["sha256"]

def attempt(action):
    try:
        action()
        return {"succeeded": True}
    except Exception as error:
        return {"succeeded": False, "exception": type(error).__name__, "message": str(error)}

case = TheWholeIntegrationRunsThroughThisPort("run")
probes = {}
try:
    case.setUp()
    port, answer = case.started()
    before = case.credential_home.read_state(ATTEMPT)
    minted = len(case.minted)
    home_type = type(case.credential_home)
    real_discard = home_type.discard_orphan
    with mock.patch.object(home_type, "discard_orphan", autospec=True, side_effect=real_discard) as discarded:
        probes["same_process_running_reprepare"] = attempt(lambda: port.prepare(case.stage(), None))
        probes["fresh_process_running_reprepare"] = attempt(lambda: case.port().prepare(case.stage(), None))
        probes["discard_calls"] = discarded.call_count
    probes["additional_provider_calls"] = len(case.minted) - minted
    probes["credential_record_preserved"] = case.credential_home.read_state(ATTEMPT) == before
    probes["runtime"] = attempt_runtime_of(case.world.manager, ATTEMPT)["execution_runtime"]
    with mock.patch.object(integration_worker.runtime, "prior_runtime_witness", side_effect=ContractRefusal("refused", "precondition", "review witness read unavailable")):
        probes["witness_failure"] = attempt(lambda: port.refresh(ATTEMPT))
    probes["marker_after_failure"] = port.may_continue(answer["assignment"])
finally:
    case.doCleanups()

result = {"claim": 115739, "at": datetime.now(timezone.utc).isoformat(), "candidate": candidate, "tests": tests, "accepted_providers_match_excluding_shared_registry": providers, "gate_sha256": hashlib.sha256(gate).hexdigest(), "gate_tail": gate.decode().splitlines()[-4:], "probes": probes, "limits": "No suite or live deployment; unchanged whole-path and release-tail evidence is reused from earlier reviews."}
(here / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
