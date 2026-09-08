"""Offline W110934 research; disposable stores, public APIs, no engine."""
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / "v12/python/src"), str(ROOT / "v12/python")]
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import runtime, block_target
from baton_v12.worker_manager import oci
from tests.integration.test_runtime import RuntimeCase
from tests.integration.fixtures import TARGET

case = RuntimeCase()
case.setUp()
report = {}
try:
    assignment = case.compose()
    delivered = runtime.materialize_delivery(case.root, attempt_id="attempt-1", workspace_group=case.group)
    runtime.publish_assignment(delivered, assignment)
    roots = {name: str(Path(case.root) / name) for name in ("inputs", "workspace")}
    for path in roots.values():
        Path(path).mkdir()
    target = Path(case.root) / "canonical"
    target.mkdir()
    labels = {"runtime_attempt_id": "attempt-1", "authority_uuid": "2b077949c86e8bef24304f59c28ec398",
              "work_id": "2b077949-W4", "participant": "baton.merge", "generation": 1,
              "principal": "principal:probe", "effective_scope": "scope:probe",
              "profile_digest": "sha256:" + "b" * 64, "policy_digest": "sha256:" + "d" * 64,
              "adapter_digest": "sha256:" + "c" * 64}
    refusals = {}
    for name, source, landing, writable in (
        ("assignment", delivered.assignment_root, runtime.ASSIGNMENT_TARGET, False),
        ("result", delivered.result_root, runtime.RESULT_TARGET, True),
        ("target", str(target), "/target", True)):
        try:
            oci.run_vector("docker", image_digest="sha256:" + "a" * 64,
                labels=labels, assignment_roots=roots, posture="execution", workspace_group=case.group,
                name="attempt-1", mounts=({"source": source, "target": landing, "writable": writable},))
        except ContractRefusal as refusal:
            refusals[name] = dict(category=refusal.category, code=refusal.code)
        else:
            raise AssertionError(name)
    assert set(refusals) == {"assignment", "result", "target"}
    old_digest = runtime.assignment_digest(assignment)
    block_target(case.coordinator, canonical_target_id=TARGET, entry_id="entry-1",
                 lease_id="lease-1", fence=case.fence, reason="integrity",
                 detail={"observed": "offline start-boundary injection"})
    replay = runtime.publish_assignment(delivered, assignment)
    assert replay["published"] is False
    assert runtime.assignment_digest(assignment) == old_digest
    try:
        case.compose()
    except ContractRefusal as refusal:
        blocked = dict(category=refusal.category, code=refusal.code)
    else:
        raise AssertionError("blocked grant still composed")
    report.update(ordinary_mount_refusals=refusals, blocked_target_recompose=blocked,
                  stale_assignment_publication_replay=replay["published"],
                  stale_assignment_digest_unchanged=True,
                  vector_parameters=list(inspect.signature(oci.run_vector).parameters),
                  adapter_parameters=list(inspect.signature(oci.OciAdapter).parameters))
finally:
    case.doCleanups()
paths = (
    "v12/python/src/baton_v12/worker_manager/oci.py",
    "v12/python/src/baton_v12/worker_manager/attempts.py",
    "v12/python/src/baton_v12/worker_manager/source_boundary.py",
    "v12/python/src/baton_v12/integration/runtime.py",
    "v12/python/src/baton_v12/integration/queue.py",
    "v12/python/src/baton_v12/integration/execution.py",
    "v12/python/tests/manager/test_dependencies.py",
    "v12/python/tests/integration/test_runtime.py",
    "v12/python/tests/integration/fixtures.py",
)
report["source_hashes"] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
report["limits"] = "No engine/provider/real target. Publication replay is deliberately not grant validation; this demonstrates why a delivery or digest alone cannot authorize a mount."
with Path(__file__).with_name("baseline.json").open("x") as output:
    json.dump(report, output, indent=2)
    output.write("\n")
print(json.dumps(report, indent=2))
