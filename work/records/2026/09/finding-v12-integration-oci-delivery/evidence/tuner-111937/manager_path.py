"""Actual manager start/reconciliation over OCI; recorded engine, public stores."""
import json
import hashlib
import os
from pathlib import Path

from baton_v12.integration import activate_target, enqueue, grant_lease, block_target
from baton_v12.integration import runtime, oci_delivery
from baton_v12.worker_manager import attempts, launch, workspaces
from baton_v12.worker_manager.oci import OciAdapter, LABEL_PREFIX
from baton_v12.worker_manager.source_boundary import nominate_source
from tests.integration.fixtures import CoordinatorCase, TARGET, target, eligibility
from tests.integration.test_runtime import profile
from tests.manager.test_attempts import TheRuntimeIsStartedOnceAndReconciled as ManagerCase, PROFILE, ADAPTER, WHO

HERE = Path(__file__).resolve().parent
results = {}


def exercise(mode):
    c = CoordinatorCase()
    m = ManagerCase("test_a_start_over_an_authorized_root_proceeds")
    c.setUp()
    m.setUp()
    calls = []
    state = {"exists": False, "running": True, "labels": {}, "mounts": []}
    try:
        inputs, given, assignment = m.delivered()
        coordinator = c.store()
        activate_target(coordinator, target())
        enqueue(coordinator, canonical_target_id=TARGET, entry_id="entry-1", eligibility=eligibility())
        grant = grant_lease(coordinator, canonical_target_id=TARGET, entry_id="entry-1", lease_id="lease-1", integrator_participant=WHO, attempt_id="attempt-1")
        selected = profile(integrator_participant=WHO)
        document = runtime.compose_assignment(coordinator, m.store, profile=selected, canonical_target_id=TARGET, entry_id="entry-1", lease_id="lease-1", fence=grant["lease"]["fence"], attempt_id="attempt-1")
        home = Path(c.root) / "delivery"
        home.mkdir()
        delivery = runtime.materialize_delivery(str(home), attempt_id="attempt-1", workspace_group=m.group)
        runtime.publish_assignment(delivery, document)
        canonical = Path(c.root) / "canonical"
        canonical.mkdir()
        os.chown(canonical, -1, m.group.gid)
        os.chmod(canonical, 0o2770)
        nominated = oci_delivery.integration_target(TARGET, nominate_source(str(canonical)))
        boundary = oci_delivery.compose_mount_boundary(coordinator, m.store, profile=selected, delivery=delivery, assignment=document, target=nominated, workspace_group=m.group)
        workspace = Path(c.root) / "workspace"
        workspace.mkdir()
        os.chown(workspace, -1, m.group.gid)
        os.chmod(workspace, 0o2770)
        launch_home = Path(c.root) / "launch"
        launch_home.mkdir()
        launched = launch.materialize(str(launch_home), attempt_id="attempt-1", session="session-1", contract="integration manager path", role="integration")
        image = given["worker_image_digest"]

        def engine(argv, **kw):
            calls.append(list(argv))
            verb = argv[1]
            if verb == "ps":
                rows = [{"ID": "runtime-1", "Image": image, "Labels": state["labels"]}] if state["exists"] else []
                return {"status": 0, "stdout": "\n".join(json.dumps(row) for row in rows), "stderr": ""}
            if verb == "run":
                state["exists"] = True
                for i, word in enumerate(argv):
                    if word == "--label":
                        k, v = argv[i + 1].split("=", 1)
                        state["labels"][k] = v
                    elif word == "--mount":
                        one = dict(part.split("=", 1) for part in argv[i + 1].split(","))
                        state["mounts"].append({"Source": one["source"], "Destination": one["target"], "RW": one["readonly"] == "false"})
                return {"status": 0, "stdout": "runtime-1", "stderr": ""}
            if verb == "inspect":
                mounts = None if mode == "unreadable" else state["mounts"]
                return {"status": 0, "stdout": json.dumps({"Id": "runtime-1", "State": {"Running": state["running"]}, "Mounts": mounts}), "stderr": ""}
            if verb == "stop":
                state["running"] = False
                return {"status": 0, "stdout": "runtime-1", "stderr": ""}
            raise AssertionError(argv)

        operands = dict(identity={"image_digest": image, "profile_digest": PROFILE, "adapter_digest": ADAPTER, "policy_digest": "sha256:" + "2" * 64}, assignment_roots={"inputs": inputs, "workspace": str(workspace)}, posture="execution", mounts=({"source": inputs, "target": "/input", "writable": False}, {"source": str(workspace), "target": "/output", "writable": True}), integration_delivery=boundary, launch_delivery=launched, workspace_group=m.group)
        adapter = OciAdapter("docker", engine, **operands)
        started = attempts.request_runtime_start(m.store, adapter, attempt_id="attempt-1", inputs=inputs)
        answer = {"start": started, "state_after_start": attempts.attempt_runtime_of(m.store, "attempt-1")}
        if mode == "normal":
            block_target(coordinator, canonical_target_id=TARGET, entry_id="entry-1", lease_id="lease-1", fence=grant["lease"]["fence"], reason="runtime-interrupted", detail={"attempt_id": "attempt-1", "observed": "blocked for recovery probe"})
            recovered = oci_delivery.adopt_mount_boundary(m.store, delivery=delivery, target=nominated, workspace_group=m.group)
            adapter = OciAdapter("docker", engine, **dict(operands, integration_delivery=recovered))
            answer["reconcile_after_block"] = attempts.reconcile_runtime(m.store, adapter, attempt_id="attempt-1")
            answer["stop_after_block"] = adapter.stop({"runtime_id": "runtime-1", "operation_id": "stop-probe"})
            answer["reconcile_after_stop"] = attempts.reconcile_runtime(m.store, adapter, attempt_id="attempt-1")
        elif mode == "missing_later":
            state["mounts"] = []
            answer["reconcile_missing_mounts"] = attempts.reconcile_runtime(m.store, adapter, attempt_id="attempt-1")
        answer["state_at_end"] = attempts.attempt_runtime_of(m.store, "attempt-1")
        answer["engine_operations"] = [a[1] for a in calls]
        answer["run_calls"] = sum(a[1] == "run" for a in calls)
        return answer
    except Exception as exc:
        return {"exception": type(exc).__name__, "message": str(exc), "engine_operations": [a[1] for a in calls]}
    finally:
        m.tearDown()
        m.doCleanups()
        c.tearDown()
        c.doCleanups()


for mode in ("normal", "unreadable", "missing_later"):
    results[mode] = exercise(mode)
destination = HERE / "manager-results.json"
if destination.exists():
    previous = destination.read_bytes()
    (HERE / ("manager-prior-" + hashlib.sha256(previous).hexdigest()[:12] + ".json")).write_bytes(previous)
destination.write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
