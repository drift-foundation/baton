"""W110774 boundary baseline; run with python3 -B from the repository root."""
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "v12/python/src"))
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, oci, workspaces
from baton_v12.integration import runtime

PATHS = (
    "v12/python/src/baton_v12/integration/runtime.py",
    "v12/python/src/baton_v12/integration/execution.py",
    "v12/python/src/baton_v12/integration/driver.py",
    "v12/python/src/baton_v12/worker_manager/oci.py",
    "v12/python/src/baton_v12/job_manager/delegation.py",
    "v12/python/tools/stage_execution.py",
    "v12/python/tools/single_worker.py",
    "v12/worker/claude_agent.py",
    "v12/worker/dogfood_entry.py",
    "v12/worker/baton_worker.py",
    "v12/worker/Dockerfile.claude",
)
report = {"work": "W110774", "claim_seq": 110914,
          "files": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                    for name in PATHS},
          "run_vector_parameters": list(inspect.signature(oci.run_vector).parameters)}
labels = {"runtime_attempt_id": "integration-probe", "authority_uuid": "2b077949c86e8bef24304f59c28ec398",
          "work_id": "2b077949-W4", "participant": "baton.merge", "generation": 1,
          "principal": "principal:probe", "effective_scope": "scope:probe",
          "profile_digest": "sha256:" + "b" * 64,
          "policy_digest": "sha256:" + "d" * 64,
          "adapter_digest": "sha256:" + "c" * 64}
with tempfile.TemporaryDirectory(prefix="w110774-research-") as home:
    store = ControlStore.open(str(Path(home) / "control.sqlite3"), incarnation="probe",
                              clock=lambda: "2026-09-07T14:40:00.000Z")
    try:
        group_id = next((gid for gid in [os.getgid(), *os.getgroups()] if gid > 0), None)
        if group_id is None:
            raise RuntimeError("No non-root supplementary/workspace group available")
        workspaces.configure_workspace_group(store, group_id)
        group = workspaces.configured_workspace_group(store)
        places = {name: str(Path(home) / name) for name in ("inputs", "workspace", "target", "result")}
        for place in places.values():
            Path(place).mkdir()
        outcomes = {}
        for name in ("target", "result"):
            try:
                oci.run_vector("docker", image_digest="sha256:" + "a" * 64,
                    labels=labels, assignment_roots={key: places[key] for key in ("inputs", "workspace")},
                    posture="execution", workspace_group=group, name="integration-probe",
                    mounts=({"source": places[name], "target": "/target" if name == "target" else runtime.RESULT_TARGET,
                             "writable": True},))
            except ContractRefusal as refused:
                outcomes[name] = {"category": refused.category, "code": refused.code,
                                  "message": str(refused).replace(home, "<temporary-root>")}
            else:
                raise AssertionError("ordinary roots unexpectedly admitted separate " + name)
        try:
            runtime.prior_runtime_witness(store, "integration-probe")
        except ContractRefusal as refused:
            report["unprepared_attempt"] = {"category": refused.category, "code": refused.code,
                                            "message": str(refused)}
        else:
            raise AssertionError("missing attempt was accepted")
        report["ordinary_mount_refusals"] = outcomes
    finally:
        store.close()
report["limitations"] = "No engine, provider or real target used. Mount refusals establish the ordinary boundary, not the impossibility of a separately reviewed integration extension."
rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
with Path(__file__).with_name("baseline.json").open("x") as output:
    output.write(rendered)
print(rendered, end="")
