"""Final-proof ancestry probe; only this fixture's disposable directory moves."""
import json
import os
from pathlib import Path
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import oci_delivery
from baton_v12.worker_manager.source_boundary import nominate_source
from tests.manager.test_oci_integration import LABELS, TheFinalProofIsAskedImmediatelyBeforeTheEngine as Fixture

f = Fixture("test_the_unchanged_case_reaches_the_run_with_the_three_binds")
f.setUp()
calls = []
seen = []
try:
    parent = Path(f.root) / "target-parent"
    parent.mkdir()
    target = parent / "target"
    target.mkdir()
    f.canonical = str(target)
    f.provisioned()
    f.target = oci_delivery.integration_target(f.target.canonical_target_id, nominate_source(f.canonical))
    def engine(argv, **kw):
        calls.append(list(argv))
        if argv[1] == "ps":
            if not parent.is_symlink():
                parent.rename(parent.with_name("target-parent-moved"))
                parent.symlink_to(parent.with_name("target-parent-moved"), target_is_directory=True)
            return {"status": 0, "stdout": "", "stderr": ""}
        if argv[1] == "run":
            seen.extend(f.mounts_of(argv))
            return {"status": 0, "stdout": "runtime-1", "stderr": ""}
        if argv[1] == "inspect":
            return {"status": 0, "stdout": json.dumps({"Id": "runtime-1", "State": {"Running": True}, "Mounts": [{"Source": s, "Destination": t, "RW": w} for s, t, w in seen]}), "stderr": ""}
        raise AssertionError(argv)
    adapter = f.adapter(engine)
    try:
        answer = {"accepted": True, "answer": adapter.start({"labels": LABELS, "operation_id": "start-1"})}
    except ContractRefusal as exc:
        answer = {"accepted": False, "reason": exc.message}
    answer.update(engine_operations=[a[1] for a in calls], run_calls=sum(a[1] == "run" for a in calls), target_mounts=[m for m in seen if m[1] == "/target"], nominated_path=f.canonical, resolved_path=os.path.realpath(f.canonical))
    Path(__file__).with_name("ancestry-results.json").write_text(json.dumps(answer, indent=2) + "\n")
    print(json.dumps(answer, indent=2))
finally:
    f.tearDown()
    f.doCleanups()
