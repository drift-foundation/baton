"""Retained-binding corruption probes over disposable manager-owned evidence."""
import json
import os
from pathlib import Path
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import oci_delivery
from tests.manager.test_oci_integration import TheFinalProofIsAskedImmediatelyBeforeTheEngine as Fixture
from tests.integration.test_runtime import _group_of

results = {}
for mode in ("unchanged", "foreign_assignment_root", "wrong_assignment_access", "duplicate_target"):
    f = Fixture("test_the_unchanged_case_reaches_the_run_with_the_three_binds")
    f.setUp()
    try:
        f.boundary()
        place = Path(f.delivery.root) / oci_delivery.BINDING_DOCUMENT
        held = json.loads(place.read_text())
        if mode == "foreign_assignment_root":
            foreign = Path(f.root) / "foreign-assignment"
            foreign.mkdir()
            stat = foreign.stat()
            held["sources"][0].update(host_source=str(foreign), device=stat.st_dev, inode=stat.st_ino)
        elif mode == "wrong_assignment_access":
            held["sources"][0]["writable"] = True
        elif mode == "duplicate_target":
            held["sources"][0] = dict(held["sources"][2])
        if mode != "unchanged":
            place.chmod(0o644)
            place.write_text(json.dumps(held, sort_keys=True, separators=(",", ":")))
            place.chmod(0o444)
        f.block()
        try:
            recovered = oci_delivery.adopt_mount_boundary(f.manager, delivery=f.delivery, target=f.target, workspace_group=_group_of(f))
            mounts = oci_delivery.boundary_mounts(recovered)
            reported = [{"source": s, "target": t, "writable": w} for s, t, w in mounts]
            adapter = f.adapter(f.engine([], binds=[{"Source": s, "Destination": t, "RW": w} for s, t, w in mounts]), integration_delivery=recovered)
            results[mode] = {"accepted": True, "mounts": mounts, "disagreement_with_corrupt_binding": oci_delivery.observed_disagreement(recovered, reported), "ordinary_observation": adapter.observe("runtime-1"), "actual_assignment_root": f.delivery.assignment_root}
        except ContractRefusal as exc:
            results[mode] = {"accepted": False, "reason": exc.message}
    finally:
        f.tearDown()
        f.doCleanups()
Path(__file__).with_name("recovery-shape-results.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
