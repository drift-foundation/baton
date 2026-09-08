"""Bounded review: candidate/test audit plus one disposable composed attempt.

Question: what do missing credentials, adapter-construction failure and actual
post-completion replay do? Budget: one fixture/worker turn, under 15 seconds;
no daemon/network/live provider, no suite, no repository implementation edits.
"""
import ast
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path.cwd()
here = Path(__file__).resolve().parent
old = here.parent / "review-115316/candidate"
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from baton_v12.contracts import ContractRefusal
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
gate = Path("/tmp/w110774-gate3.txt").read_bytes()
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

test_audit = {}
for name in ("v12/python/tests/tools/test_integration_worker.py", "v12/python/tests/integration/test_driver.py"):
    before, after = methods(old / name), methods(root / name)
    test_audit[name] = {"before": len(before), "after": len(after), "removed_or_renamed": sorted(before.keys() - after.keys()), "added_or_renamed": sorted(after.keys() - before.keys()), "changed_existing_method_AST": sorted(key for key in before.keys() & after.keys() if before[key] != after[key])}

probes = {}
fixture = TheWholeIntegrationRunsThroughThisPort("run")
try:
    fixture.setUp()
    port, answer = fixture.started()
    run = [one for one in fixture.engine_calls if one[1] == "run"]
    probes["missing_credentials"] = {"configured_delivery": port.credential_delivery, "configured_home": port.credential_home, "engine_start_count": len(run), "credential_mount_present": any("/run/baton/credentials" in arg for command in run for arg in command), "admission_outcome": answer["outcome"]}
    displaced = fixture.target_place + "-displaced"
    os.rename(fixture.target_place, displaced)
    try:
        port.refresh(ATTEMPT)
    except Exception as error:
        probes["refresh_adapter_construction_failure"] = {"exception": type(error).__name__, "message": str(error), "marker_retained": port.may_continue(answer["assignment"])}
    finally:
        os.rename(displaced, fixture.target_place)
    probes["worker_exit"] = fixture.worker_turn()
    fixture.running = False
    port.refresh(ATTEMPT)
    first = fixture.keep_going()
    probes["first_continuation"] = first["outcome"]
    try:
        again = fixture.keep_going()
        probes["post_completion_replay"] = {"outcome": again["outcome"]}
    except ContractRefusal as error:
        probes["post_completion_replay"] = {"category": error.category, "code": error.code, "message": error.message}
finally:
    fixture.doCleanups()

result = {"claim": 115440, "at": datetime.now(timezone.utc).isoformat(), "candidate": candidate, "test_audit": test_audit, "gate_sha256": hashlib.sha256(gate).hexdigest(), "gate_tail": gate.decode().splitlines()[-4:], "probes": probes, "limits": "Deterministic engine and provider child process; disposable plain-directory target and supplied revision seam; no live credential/provider/image/engine proof."}
(here / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
