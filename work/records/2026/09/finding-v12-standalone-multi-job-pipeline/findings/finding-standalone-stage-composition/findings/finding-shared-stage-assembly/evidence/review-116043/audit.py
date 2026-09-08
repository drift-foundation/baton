"""Bounded interface review, budget30s, no daemon/model or whole-suite run.

Questions: do real factory-held operands reach the new consumers, and can a
fresh port resume a published but never-started delivery through assembly?
"""
import ast
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import mock

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
DOSSIER = HERE.parents[1]
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import runtime
from baton_v12.worker_manager import configured_workspace_group
from tests.tools.test_stage_execution import ServingCase
from tests.tools.test_integration_worker import TheWholeIntegrationRunsThroughThisPort, ATTEMPT
from tools import stage_execution

names = ["tools/stage_execution.py", "tools/single_worker.py", "tools/parallel_test.py",
         "tests/tools/test_stage_execution.py", "tests/tools/test_single_worker.py"]
hashes = {}
for name in names:
    relative = "v12/python/" + name
    raw = (ROOT / relative).read_bytes()
    hashes[relative] = hashlib.sha256(raw).hexdigest()
    dest = HERE / "candidate" / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
(HERE / "PROGRESS-at-review.md").write_bytes((DOSSIER / "PROGRESS.md").read_bytes())
old = ast.parse((DOSSIER / "evidence/review-111157/candidate/v12/python/tests/tools/test_stage_execution.py").read_text())
new = ast.parse((ROOT / "v12/python/tests/tools/test_stage_execution.py").read_text())
classes = lambda tree: {n.name: ast.dump(n) for n in tree.body if isinstance(n, ast.ClassDef)}
before, after = classes(old), classes(new)
unchanged = all(after.get(k) == v for k, v in before.items())
assert unchanged
facts = {"candidate_hashes": hashes, "prior_classes_unchanged": len(before),
         "added_classes": sorted(after.keys() - before.keys())}

def outcome(call):
    try:
        result = call()
        return {"returned": str(result)}
    except ContractRefusal as error:
        return {"category": error.category, "code": error.code, "message": error.message}

case = ServingCase()
try:
    case.setUp()
    jobs, control, composed = case.serving()
    integration = composed.integrator
    held = next(w["deployment"] for w in composed.deployment.given["workers"] if w["role"] == "implementation")
    facts["factory_held_derived_members"] = sorted(set(held) - set(case.config))
    facts["factory_requirement"] = outcome(integration.required_tests)
    assert facts["factory_requirement"].get("category") == "integrity"
    group = configured_workspace_group(control)
    delivery = runtime.materialize_delivery(composed.deployment.integration_root,
        attempt_id="review-116043", workspace_group=group)
    facts["factory_group_type"] = type(composed.deployment.workspace_group).__name__
    facts["factory_delivery_read"] = outcome(lambda: integration._published({"attempt_id": "review-116043"}))
    assert facts["factory_delivery_read"].get("category") == "policy"
    facts["nominal_group_positive"] = runtime.adopt_delivery(composed.deployment.integration_root,
        attempt_id="review-116043", workspace_group=group).root == delivery.root
finally:
    case.doCleanups()

# Isolate later-tick dispatch from the two above blocking operand faults.
# Real retained account, driver, delivery, manager and fresh production port.
# One interruption before port.run leaves a durable assignment but no start.
case = TheWholeIntegrationRunsThroughThisPort()
try:
    case.setUp()
    old_port = case.port()
    old_port.prepare(case.stage(), None)
    with mock.patch.object(old_port, "run", side_effect=ContractRefusal("refused", "precondition", "review interruption before runtime start")):
        facts["interrupted_first_admission"] = outcome(lambda: case.admit(old_port))
    facts["before_retry_runtime"] = runtime.prior_runtime_witness(case.world.manager, ATTEMPT)["execution_runtime"]
    assert facts["before_retry_runtime"] == "not-started"
    fresh = case.port()
    world = case.world
    deployment = SimpleNamespace(
        given={"canonical_target_id": world.target, "policy_generation": world.authority.policy_generation()},
        control=world.manager, jobs=world.jobs, authority=world.authority_read,
        integration=world.coordinator, integration_profile=case.profile,
        integration_root=case.launch_root, workspace_group=case.owner.group,
        sessions={"verification":world.sessions["verify"], "review":world.sessions["review"],
                  "approval":world.sessions["approve"], "integrator":world.integrator},
        line=lambda: {"line_id": world.line_id}, published_proposal=lambda accepted: world.proposal_id)
    integration = stage_execution.Integration(deployment, fresh)
    with mock.patch.object(integration, "required_tests", return_value=world.required), \
         mock.patch.object(fresh, "prepare", wraps=fresh.prepare) as prepare:
        facts["fresh_unstarted_retry"] = outcome(lambda: integration.run(case.stage(), {"job_id":"job-1"}))
        facts["fresh_prepare_calls"] = prepare.call_count
    facts["runtime_after_retry"] = runtime.prior_runtime_witness(world.manager, ATTEMPT)["execution_runtime"]
    facts["engine_run_calls"] = sum(argv[1] == "run" for argv in case.engine_calls)
    assert facts["fresh_prepare_calls"] == 0
    assert "no credential delivery" in facts["fresh_unstarted_retry"].get("message", "")
    assert facts["engine_run_calls"] == 0
finally:
    case.doCleanups()

gate = Path("/tmp/w103083-gate.txt")
if gate.exists():
    raw = gate.read_bytes()
    (HERE / "gate.txt").write_bytes(raw)
    facts["gate_sha256"] = hashlib.sha256(raw).hexdigest()
    facts["gate_diagnostics"] = [line for line in raw.decode().splitlines() if line.startswith(("FAIL:","ERROR:","Ran ","FAILED"))]
else:
    facts["gate_operational_finding"] = "Reported /tmp/w103083-gate.txt is unavailable."
(HERE / "audit.json").write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n")
print(json.dumps({k:v for k,v in facts.items() if k not in ("candidate_hashes","gate_diagnostics")}, indent=2))
