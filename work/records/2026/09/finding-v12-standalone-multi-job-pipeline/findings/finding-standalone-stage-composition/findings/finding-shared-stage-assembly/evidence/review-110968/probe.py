"""Independent correction probes. Run from v12/python with PYTHONPATH=src:. ."""
import hashlib
import json
from pathlib import Path
import sys
import unittest.mock

from baton_v12.authority import Refusal
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import scheduler
from baton_v12.worker_manager import configured_workspace_group
from tests.job_manager import fixtures
from tests.tools.test_single_worker import Engine
from tests.tools.test_stage_execution import ServingCase
from tools import stage_execution

HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().parents[1]
PATHS = (
    "v12/python/tools/stage_execution.py",
    "v12/python/tools/single_worker.py",
    "v12/python/tests/tools/test_stage_execution.py",
    "v12/python/tests/tools/test_single_worker.py",
    "v12/python/tools/parallel_test.py",
)
manifest = {}
for name in PATHS:
    raw = (ROOT / name).read_bytes()
    target = HERE / "candidate" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == raw, "candidate changed since capture"
    else:
        with target.open("xb") as output:
            output.write(raw)
    manifest[name] = hashlib.sha256(raw).hexdigest()
results = []

def state(job, control, integration_path):
    try:
        group = configured_workspace_group(control).gid
    except ContractRefusal:
        group = None
    return {"group": group, "pool": scheduler.active_generation(job),
            "integration_exists": Path(integration_path).exists()}

for kind in ("no-grant", "malformed-actor", "pool-generation", "valid", "policy-too-wide"):
    case = ServingCase()
    try:
        case.setUp()
        job, control = case.stores("independent-" + kind)
        given = case.composed_document()
        if kind == "no-grant":
            given["receipt_participants"]["approval"] = "baton.not-configured"
        elif kind == "malformed-actor":
            given["receipt_participants"]["approval"] = "not-an-address"
        elif kind == "pool-generation":
            given["pool_generation"] = 4
        elif kind == "policy-too-wide":
            given["policy_generation"] = 9007199254740992
        before = state(job, control, case.integration_store)
        record = {"case": kind, "before": before}
        try:
            composed = stage_execution.operations_from(given, job, control,
                engine_run=Engine(), credential_provider=lambda *_: case.secret,
                clock=lambda: fixtures.NOW, checkout=case.checkout)
            case.addCleanup(composed.close)
            record["constructed"] = True
            if kind == "valid":
                record["grants"] = {name: composed.authority.holds_capability(
                    composed.sessions[name].participant, capability, scope=case.scope)
                    for name, capability in stage_execution.RECEIPT_CAPABILITIES.items()}
                assert all(record["grants"].values())
            if kind == "policy-too-wide":
                try:
                    composed.sessions["approval"].approve({"proposal_id": "absent-proposal",
                        "approval_id": "probe-approval", "operation_id": "probe-approval",
                        "disposition": "approved", "policy_generation": given["policy_generation"]})
                except Refusal as refused:
                    record["authority_refusal"] = {"type": type(refused).__name__, "message": str(refused)}
                    assert "interoperable range" in str(refused)
                else:
                    raise AssertionError("Authority accepted an out-of-range generation")
        except ContractRefusal as refused:
            record.update(constructed=False, refusal={"category": refused.category,
                          "code": refused.code, "message": str(refused)})
        record["after"] = state(job, control, case.integration_store)
        if kind in ("no-grant", "malformed-actor", "pool-generation"):
            assert record["constructed"] is False and record["before"] == record["after"]
        results.append(record)
    finally:
        case.doCleanups()

report = {"claim_seq": 110968, "files": manifest, "probes": results,
          "limitations": "Local fixture Authority and stores, deterministic engine, no daemon/provider or canonical target. Existing reported suites were not rerun."}
rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
with (HERE / (sys.argv[1] if len(sys.argv) > 1 else "probe-output.json")).open("x") as output:
    output.write(rendered)
print(rendered, end="")
