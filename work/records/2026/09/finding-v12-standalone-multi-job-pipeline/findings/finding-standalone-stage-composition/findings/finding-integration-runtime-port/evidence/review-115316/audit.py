"""Retain candidate evidence and probe the marker consumer, without a runtime.

Question: do the public reconciliation document shapes invalidate the marker?
Scope/budget: two injected owner answers through real refresh, plus no-marker
status; seconds, no suite, store, engine, credentials or target writes.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

root = Path.cwd()
here = Path(__file__).resolve().parent
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import documents
from tools import integration_worker as module

names = ["tools/integration_worker.py", "tests/tools/test_integration_worker.py", "tools/parallel_test.py", "src/baton_v12/integration/driver.py", "src/baton_v12/integration/__init__.py", "tests/integration/test_driver.py"]
candidate = {}
for name in names:
    relative = "v12/python/" + name
    data = (root / relative).read_bytes()
    destination = here / "candidate" / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    candidate[relative] = hashlib.sha256(data).hexdigest()
gate = Path("/tmp/w110774-gate2.txt").read_bytes()
(here / "gate.txt").write_bytes(gate)

assignment = {"attempt_id": "attempt-1", "canonical_target_id": "target-1"}
answers = {
    "decision_uncertain": documents.runtime_uncertain(attempt_id="attempt-1", decision="uncertain", why="fixture observation unavailable"),
    "attached_uncertain": documents.runtime_attached(attempt_id="attempt-1", decision="attached", runtime_id="runtime-1", observed="uncertain", why="fixture observation unavailable"),
}
probes = {}
for name, answer in answers.items():
    port = object.__new__(module.IntegrationRuntimePort)
    port.manager = object()
    port._live = {"attempt-1": {"assignment": dict(assignment), "delivery_root": "/not-opened"}}
    with mock.patch.object(port, "_observing_adapter", return_value=object()), mock.patch.object(module, "reconcile_runtime", return_value=answer):
        returned = port.refresh("attempt-1")
    probes[name] = {"owner_answer": returned, "marker_retained": port.may_continue(assignment)}

port = object.__new__(module.IntegrationRuntimePort)
port._live = {}
try:
    port.observed("attempt-1", assignment)
except ContractRefusal as error:
    probes["observation_after_restart_or_forget"] = {"category": error.category, "code": error.code, "message": error.message}
result = {"claim": 115316, "at": datetime.now(timezone.utc).isoformat(), "candidate_sha256": candidate, "gate_sha256": hashlib.sha256(gate).hexdigest(), "gate_tail": gate.decode().splitlines()[-4:], "probes": probes, "limits": "Injected reconciliation answers prove consumer branch behavior only; no real manager/runtime recovery or whole-start proof."}
(here / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
