"""Independent W110934 boundary probes; disposable public-API fixtures, no daemon."""
import hashlib
import json
import os
from pathlib import Path
import re

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import oci_delivery, runtime
from tests.manager.test_oci_integration import (
    LABELS, TheFinalProofIsAskedImmediatelyBeforeTheEngine as Fixture)
from tests.integration.test_runtime import _group_of

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "v12/python").is_dir())
results = {}


def probe(name, action):
    fixture = Fixture("test_the_unchanged_case_reaches_the_run_with_the_three_binds")
    fixture.setUp()
    try:
        results[name] = action(fixture)
    except Exception as exc:
        results[name] = {"exception": type(exc).__name__, "message": str(exc)}
    finally:
        fixture.tearDown()
        fixture.doCleanups()


def starting(f, variant):
    calls = []
    def engine(argv, **options):
        calls.append(list(argv))
        if argv[1] == "ps":
            if variant == "late_result_mode":
                os.chmod(f.delivery.result_root, 0o777)
            return {"status": 0, "stdout": "", "stderr": ""}
        if argv[1] == "inspect":
            return {"status": 0, "stdout": json.dumps({
                "Id": "runtime-1", "State": {"Running": True}, "Mounts": []}), "stderr": ""}
        return {"status": 0, "stdout": "runtime-1", "stderr": ""}
    os.chmod(f.canonical, 0o755 if variant == "target_mode_755" else 0o2775)
    os.chown(f.canonical, -1, _group_of(f).gid)
    opts = {}
    if variant == "consent_posture":
        opts["posture"] = "consent"
        opts["workspace_group"] = None
    if variant == "workspace_equals_target":
        os.chmod(f.canonical, 0o2770)
        inputs = os.path.join(f.root, "overlap-inputs")
        os.makedirs(inputs)
        opts["assignment_roots"] = {"inputs": inputs, "workspace": f.canonical}
        opts["mounts"] = [{"source": f.canonical, "target": "/output", "writable": True}]
    adapter = f.adapter(engine, **opts)
    labels = dict(LABELS)
    if variant == "foreign_participant":
        labels["participant"] = "baton.foreign"
    try:
        answer = adapter.start({"labels": labels, "operation_id": "start-1"})
        outcome = {"accepted": True, "answer": answer}
    except ContractRefusal as exc:
        outcome = {"accepted": False, "reason": exc.message}
    outcome.update(engine_operations=[a[1] for a in calls],
                   run_calls=sum(a[1] == "run" for a in calls),
                   target_mode=oct(os.stat(f.canonical).st_mode & 0o7777),
                   result_mode=oct(os.stat(f.delivery.result_root).st_mode & 0o7777))
    if variant == "workspace_equals_target":
        outcome["target_binds"] = [m for a in calls if a[1] == "run"
                                   for m in f.mounts_of(a) if m[0] == f.canonical]
    if variant == "missing_observed_mounts":
        outcome["observation"] = adapter.observe("runtime-1")
        outcome["optional_helper"] = adapter.integration_mounts_agree("runtime-1")
    return outcome


for variant in ("consent_posture", "target_mode_755", "late_result_mode", "foreign_participant",
                "workspace_equals_target", "missing_observed_mounts"):
    probe(variant, lambda f, v=variant: starting(f, v))


def reconstruction(f, missing=False):
    first = f.boundary()
    companion = Path(f.delivery.root) / oci_delivery.BINDING_DOCUMENT
    original = companion.read_bytes()
    if missing:
        companion.rename(companion.with_suffix(".saved"))
    else:
        f.block()
    try:
        second = f.boundary()
        return {"reconstructed": True, "missing_binding_recreated": missing,
                "same_bytes": companion.read_bytes() == original}
    except ContractRefusal as exc:
        return {"reconstructed": False, "reason": exc.message,
                "old_boundary_still_available_only_in_old_process": first.attempt_id}


probe("reconstruct_after_block", reconstruction)
probe("reconstruct_missing_binding", lambda f: reconstruction(f, True))


def ancestor_shadow(f):
    b = f.boundary()
    mounts = [{"source": s, "target": t, "writable": w}
              for s, t, w in oci_delivery.boundary_mounts(b)]
    mounts.append({"source": "/foreign", "target": "/run/baton/integration", "writable": True})
    return {"disagreement": oci_delivery.observed_disagreement(b, mounts)}


probe("observed_ancestor_shadow", ancestor_shadow)


def mutable(f):
    b = f.boundary()
    b.sources[2]["writable"] = False
    b.assignment["integrator_participant"] = "baton.foreign"
    b.profile["integrator_participant"] = "baton.foreign"
    return {"nested_mutations_accepted": True,
            "mounts": oci_delivery.boundary_mounts(b),
            "participant": b.assignment["integrator_participant"]}


probe("nominal_boundary_is_shallow_frozen", mutable)


def writable_assignment(f):
    place = Path(f.delivery.assignment_root) / runtime.ASSIGNMENT_DOCUMENT
    os.chmod(place, 0o666)
    f.boundary()
    return {"composed": True, "assignment_mode": oct(place.stat().st_mode & 0o7777)}


probe("writable_published_assignment", writable_assignment)

progress = (HERE.parents[1] / "PROGRESS.md").read_text()
audit = {}
for path, expected in re.findall(r"\| `(v12/python/[^`]+)` \| `([a-f0-9]{64})` \|", progress):
    data = (REPO / path).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    audit[path] = {"expected": expected, "actual": actual, "matches": expected == actual}
    dest = HERE / "candidate" / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
(HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
if (HERE / "results.json").exists():
    prior = (HERE / "results.json").read_bytes()
    (HERE / ("prior-results-" + hashlib.sha256(prior).hexdigest()[:12] + ".json")).write_bytes(prior)
(HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps({"candidate": audit, "probes": results}, indent=2))
