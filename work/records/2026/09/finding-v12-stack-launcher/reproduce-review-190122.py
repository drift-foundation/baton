"""Bounded review reproductions with public v12 APIs and fixture stores only."""
import hashlib
import io
import json
import os
from pathlib import Path
import time

os.environ["BATON_V12_STACK_TEST_ROOT"] = "/tmp"
from tools import bootstrap, stage_execution
from tests.tools.test_bootstrap import (
    AnInstanceWithNoCapacityREFUSES_WORK_IT_CANNOT_SERVE as EmptyCase,
    TheINSTALLED_INSTANCE_SERVES_THE_SAME_WAY as InstalledCase,
    guide_example,
)
from tests.manager.test_offers import NOW
from tests.job_manager.test_scheduling import pool, principals
from baton_v12.job_manager import manager, scheduler
from baton_v12.worker_manager import outstanding_offers

start = time.monotonic()
record = Path(__file__).parent
repository = record.parents[4]
evidence = {"cases": {}, "boundary": "real serve loop; fixture offer APIs with strict fake Authority; installation uses explicitly simulated runtime"}

for kind in ("control-offer", "active-pool"):
    fixture = EmptyCase()
    fixture.setUp()
    operations = None
    try:
        prepared = fixture.composed(kind)
        operations = stage_execution.operations_from(prepared["configuration"],
                                                     fixture.jobs, fixture.control)
        slept = []
        def sleep(interval):
            slept.append(interval)
            if kind == "control-offer":
                fixture.seed_offer()
            else:
                document = pool()
                scheduler.activate_pool(fixture.jobs, document, principals(document))
        # State arrives after initial recovery, during the real serving loop.
        answer = manager.serve(fixture.jobs, operations, clock=lambda: NOW,
                               sleep=sleep, should_continue=lambda: not slept,
                               interval=1)
        evidence["cases"][kind] = {
            "serve_returned_normally": True, "sleep_calls": slept,
            "last_report": answer,
            "unconfigured_work_after_tick": stage_execution.unconfigured_work(
                fixture.jobs, fixture.control),
            "offer_states": {one["offer_id"]: one["state"]
                             for one in outstanding_offers(fixture.control)},
            "active_generation": scheduler.active_generation(fixture.jobs),
        }
    finally:
        if operations is not None:
            operations.release()
        fixture.doCleanups()

fixture = InstalledCase()
fixture.setUp()
try:
    destination, _ = fixture.install()
    configuration = bootstrap.layout(destination)["configuration"]
    before = json.loads(Path(configuration).read_bytes())
    inputs = Path(fixture.root) / "review-updated-inputs.json"
    inputs.write_text(json.dumps(dict(guide_example(), state_root=destination)))
    said = io.StringIO()
    code = bootstrap.main(["--inputs", str(inputs)], stream=said)
    after = json.loads(Path(configuration).read_bytes())
    evidence["cases"]["documented-reconfiguration"] = {
        "returncode": code,
        "configuration_removed_members": {key: before[key] for key in before if key not in after},
        "configuration_added_members": {key: after[key] for key in after if key not in before},
        "configuration_changed_members": {key: [before[key], after[key]] for key in before if key in after and before[key] != after[key]},
        "boundary": "no-Job repeat of guide input after simulated-runtime destination install, no repositories",
    }
finally:
    fixture.doCleanups()

author = json.loads((record / "EVIDENCE-190047.json").read_text())
evidence["candidate_hashes"] = {
    name: {"expected": wanted, "actual": hashlib.sha256((repository / name).read_bytes()).hexdigest()}
    for name, wanted in author["changed_this_claim"].items()
}
evidence["seconds"] = time.monotonic() - start
evidence["earlier_reproducer_attempt"] = {"result": "reviewer helper KeyError using instance.layout configuration key; corrected to bootstrap.layout", "tool_wall_seconds": 0.060025017, "fixture_cleanup": "finally blocks ran"}
(record / "REVIEW-EVIDENCE-190122.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps(evidence, indent=2))
