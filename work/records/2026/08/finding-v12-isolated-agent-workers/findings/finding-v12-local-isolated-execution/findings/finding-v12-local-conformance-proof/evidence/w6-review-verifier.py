import hashlib
import importlib.util
import json
import pathlib
import sys

repo = pathlib.Path("/home/sl/src/baton")
dossier = repo / "work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-local-isolated-execution/findings/finding-v12-local-conformance-proof"
register = repo / "work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-runtime-conformance/evidence"
report_path = dossier / "evidence/w6-seal/w6-capability-pass-report.json"

spec = importlib.util.spec_from_file_location("review_model", register / "conformance_model.py")
model = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = model
spec.loader.exec_module(model)
report = json.loads(report_path.read_text())

def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

errors = []
for name, sealed in report["sealed_evidence"].items():
    path = repo / sealed["path"]
    if not path.is_file():
        errors.append(f"missing sealed input {name}: {path}")
        continue
    if path.stat().st_size != sealed["bytes"]:
        errors.append(f"byte mismatch for {name}")
    if digest(path) != sealed["content_digest"]:
        errors.append(f"digest mismatch for {name}")

fixture = model.accept_document(report["fixture"], "fixture")
run = model.accept_document(report["run"], "run")
if run["fixture_digest"] != fixture["document_digest"]:
    errors.append("run does not bind the fixture")
if run["obligations_digest"] != model.OBLIGATIONS_DIGEST:
    errors.append("run does not bind the obligation register")

derived = []
seen = set()
for observation in run["observations"]:
    case = model.validate_case(model.CASE_BY_ID[observation["case_id"]])
    if observation["case_id"] in seen:
        errors.append(f"duplicate observation {observation['case_id']}")
    seen.add(observation["case_id"])
    if observation["fixture_digest"] != fixture["document_digest"]:
        errors.append(f"fixture mismatch for {observation['case_id']}")
    if observation["case_digest"] != case["document_digest"]:
        errors.append(f"case digest mismatch for {observation['case_id']}")
    missing_facts = set(case["required_facts"]) - set(observation["facts"])
    if missing_facts:
        errors.append(f"missing facts for {observation['case_id']}: {sorted(missing_facts)}")
    purposes = {one["purpose"] for one in observation["evidence"]}
    if purposes != set(case["deciding_evidence"]):
        errors.append(f"evidence purposes mismatch for {observation['case_id']}")
    for evidence in observation["evidence"]:
        artifact = evidence["artifact"]
        if not artifact["locator"].startswith("file:"):
            errors.append(f"non-file evidence for {observation['case_id']}")
            continue
        path = repo / artifact["locator"][5:]
        if not path.is_file() or path.stat().st_size != artifact["bytes"] or digest(path) != artifact["content_digest"]:
            errors.append(f"artifact mismatch for {observation['case_id']}:{evidence['purpose']}")
    accepted = model.accept_observation(observation, case, fixture)
    assessment, rationale = model.assess(accepted, case)
    if assessment == "passed" and not model.faults_available(case, fixture):
        assessment = "unable"
        rationale = "required faults are not injectable by this fixture"
    derived.append({"case_id": case["case_id"], "assessment": assessment, "rationale": rationale})

core = model.core_for("local-oci")
failed = sorted(one["case_id"] for one in derived if one["assessment"] == "failed")
unable = sorted(one["case_id"] for one in derived if one["assessment"] == "unable")
missing = sorted(core - seen)
passed = sorted(one["case_id"] for one in derived if one["assessment"] == "passed")
if failed:
    verdict, rationale = "not-certified", f"{len(failed)} portable core case(s) failed"
elif unable:
    verdict, rationale = "not-certified", f"{len(unable)} portable core case(s) could not be decided; 'unable' is not a pass"
elif missing:
    verdict, rationale = "not-certified", f"{len(missing)} portable core case(s) were not observed"
else:
    verdict, rationale = "certified", "every portable core case was observed and passed"

expected = {
    "assessed": derived,
    "passed": passed,
    "failed": failed,
    "unable": unable,
    "not_observed": missing,
    "verdict": verdict,
    "verdict_rationale": rationale,
    "local_oci_portable_core": sorted(core),
}
for key, value in expected.items():
    if report[key] != value:
        errors.append(f"report mismatch: {key}")

try:
    model.build_report(run, fixture, "review", "2026-08-28T20:00:00.000Z")
except model.ConformanceError as error:
    gate = str(error)
else:
    errors.append("full frozen report unexpectedly admitted the partial fixture")
    gate = "not refused"

print(json.dumps({
    "errors": errors,
    "counts": {"core": len(core), "assessed": len(derived), "passed": len(passed), "failed": len(failed), "unable": len(unable), "missing": len(missing)},
    "verdict": verdict,
    "rationale": rationale,
    "full_report_gate": gate,
    "report_digest": digest(report_path),
}, indent=2, sort_keys=True))
raise SystemExit(1 if errors else 0)
