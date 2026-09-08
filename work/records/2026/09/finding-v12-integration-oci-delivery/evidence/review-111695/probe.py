"""Independent corrected-candidate probes, disposable stores and recorded engine."""
import hashlib
import json
import os
from pathlib import Path
import re

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import oci_delivery, runtime
from baton_v12.worker_manager import attempts
from baton_v12.worker_manager.source_boundary import nominate_source
from tests.manager.test_oci_integration import LABELS, TheFinalProofIsAskedImmediatelyBeforeTheEngine as Fixture
from tests.integration.test_runtime import _group_of

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "v12/python").is_dir())
DOSSIER = HERE.parents[1]
results = {}


def outcome(call):
    try:
        return {"accepted": True, "answer": call()}
    except ContractRefusal as exc:
        return {"accepted": False, "reason": exc.message}
    except Exception as exc:
        return {"exception": type(exc).__name__, "message": str(exc)}


def probe(name, call):
    f = Fixture("test_the_unchanged_case_reaches_the_run_with_the_three_binds")
    f.setUp()
    try:
        results[name] = call(f)
    finally:
        f.tearDown()
        f.doCleanups()


def starting(f, variant):
    calls = []
    base = f.engine(calls, binds=None if variant == "unknown_mounts" else ...)
    def engine(argv, **kw):
        if argv[1] == "ps":
            if variant == "late_result_mode":
                os.chmod(f.delivery.result_root, 0o777)
            if variant == "late_binding_mode":
                os.chmod(Path(f.delivery.root) / oci_delivery.BINDING_DOCUMENT, 0o666)
        return base(argv, **kw)
    adapter = f.adapter(engine)
    labels = dict(LABELS)
    if variant == "foreign_participant":
        labels["participant"] = "baton.foreign"
    if variant == "ordinary_workspace_mount":
        adapter.mounts = ({"source": adapter.assignment_roots["workspace"], "target": "/output", "writable": True},)
    answer = outcome(lambda: adapter.start({"labels": labels, "operation_id": "start-1"}))
    if answer.get("accepted"):
        # This is the exact closed parser request_runtime_start calls on the
        # real adapter answer. It writes no state and supplies no substitute.
        answer["manager_start_answer_parser"] = outcome(lambda: attempts._started(answer["answer"]))
    answer["engine_operations"] = [a[1] for a in calls]
    answer["run_calls"] = sum(a[1] == "run" for a in calls)
    return answer


for v in ("normal", "unknown_mounts", "ordinary_workspace_mount", "foreign_participant", "late_result_mode", "late_binding_mode"):
    probe(v, lambda f, v=v: starting(f, v))


def observation(f):
    calls = []
    adapter = f.adapter(f.engine(calls, binds=[]))
    return {"ordinary_observation": adapter.observe("runtime-1"),
            "integration_comparator": adapter.integration_mounts_agree("runtime-1")}


probe("ordinary_observation_missing_binds", observation)


def recovery(f, variant):
    b = f.boundary()
    if variant == "blocked":
        f.block()
    if variant == "missing":
        companion = Path(f.delivery.root) / oci_delivery.BINDING_DOCUMENT
        companion.rename(companion.with_suffix(".saved"))
    target = f.target
    if variant == "other_configured_directory":
        other = Path(f.root) / "other-target"
        other.mkdir()
        target = oci_delivery.integration_target(f.target.canonical_target_id, nominate_source(str(other)))
    answer = outcome(lambda: oci_delivery.adopt_mount_boundary(f.manager, delivery=f.delivery, target=target, workspace_group=_group_of(f)))
    if answer.get("accepted"):
        recovered = answer.pop("answer")
        answer["mounts"] = oci_delivery.boundary_mounts(recovered)
        answer["configured_target"] = target.source.place
        answer["restart_refusal"] = outcome(lambda: oci_delivery.revalidate_boundary(recovered))
    return answer


for v in ("blocked", "missing", "other_configured_directory"):
    probe("recovery_" + v, lambda f, v=v: recovery(f, v))


def immutable(f):
    b = f.boundary()
    answers = []
    for value, key in ((b.sources[2], "writable"), (b.assignment, "integrator_participant"), (b.profile, "integrator_participant")):
        answers.append(outcome(lambda value=value, key=key: value.__setitem__(key, False)))
    return answers


probe("public_immutability", immutable)

audit = {}
for path, expected in re.findall(r"\| `(v12/python/[^`]+)` \| `([a-f0-9]{64})` \|", (DOSSIER / "PROGRESS.md").read_text()):
    data = (REPO / path).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    audit[path] = {"expected": expected, "actual": actual, "matches": expected == actual}
    dest = HERE / "candidate" / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
for name in ("FINDING.md", "PLAN.md", "PROGRESS.md"):
    (HERE / ("at-review-" + name)).write_bytes((DOSSIER / name).read_bytes())
(HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
(HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps({"audit": audit, "results": results}, indent=2))
