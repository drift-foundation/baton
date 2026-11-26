"""Execution contract of a selected, report-only MANUAL assignment."""
import json
import re

from ..contracts import ContractRefusal, digest, digest_of_bytes
from ..contracts.manifest import job_input_identity
from . import documents

TEMPLATE = "baton.v12.manual-research/1"
TASK = "baton.v12.research-task/1"
REPORT = "findings"
REPORT_LIMIT = 65536


def refusal(message):
    return ContractRefusal("refused", "precondition", message)


def template():
    return {"version": TEMPLATE, "roles": [{"role": "research", "kind": "research", "consumes": [],
                                           "depends_on": [], "produces": [REPORT]}]}


def outputs():
    return [{"name": REPORT, "type": "directory-result", "path": REPORT,
             "required": True, "constraints": {
                 "max_bytes": REPORT_LIMIT, "max_entries": 1,
                 "allowed_media_types": ["application/octet-stream"],
                 "link_policy": "forbid", "validator_digest": None}}]


def delivery(given, phase):
    manifest = given["input_manifest"]
    binding = given.get("provider_contract") or {}
    adapter = binding.get("adapter") or {}
    if (adapter.get("provider") != "claude" or adapter.get("research") is not True or not adapter.get("participation_sources")):
        raise refusal("research requires a selected report-only Claude provider with participation evidence")
    if (given["launch_role"] != "research" or manifest["outputs"] != outputs()
            or given["retention_disposition"] != "retain"):
        raise refusal("research needs a report-only worker with retained findings")
    commit = phase.get("source_commit") or json.loads(given["task_bytes"]).get("base_commit")
    if type(commit) is not str or not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", commit):
        raise refusal("research requires a pinned source commit")
    task = {"schema": TASK, "statement": phase["statement"], "scope": phase["scope"], "source_commit": commit}
    body = json.dumps(task, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    contract = dict(manifest["human_contract"], bytes=len(body), content_digest=digest_of_bytes(body))
    manifest = dict(manifest, human_contract=contract, work_ref=dict(manifest["work_ref"], work_id=phase["work_id"]))
    manifest.pop("manifest_digest")
    manifest["manifest_digest"] = digest(manifest)
    return dict(given, input_manifest=manifest, task_bytes=body)


def compatible(given, phase):
    if (given.get("launch_role") != "research" or given["profile_name"] != phase["profile_name"]
            or given["profile_digest"] != phase["profile_digest"] or given["policy_digest"] != phase["policy_digest"]):
        return False
    material = delivery(given, phase)
    return job_input_identity(material["input_manifest"]) == phase["input_digest"]


def prepare_submission(execution_job_id, descriptor):
    stage = {key: descriptor[key] for key in ("kind", "work_id", "profile_name", "profile_digest")}
    if stage["kind"] != "research":
        raise refusal("the selected assignment must declare the research role")
    stage["depends_on"] = []
    job = {key: descriptor[key] for key in ("input_digest", "policy_digest")}
    job.update(job_id=execution_job_id, stages=[stage], test_scope=[], terminal_policy="report-and-hold")
    return documents.owned_submission({"schema": documents.RESEARCH_SUBMISSION_SCHEMA,
                                       "submission_id": execution_job_id, "jobs": [job]})


def frozen_evidence(control, attempt_id):
    """Read the worker owner's freeze instant, validating the exact sealed manifest."""
    from ..worker_manager import frozen_output_of, load_manifest, model_attribution

    output = frozen_output_of(control, attempt_id)
    if output is None:
        return None
    sealed = load_manifest(control, output["manifest_digest"], "resultManifest")
    if (not sealed or sealed["result_id"] != output["result_id"]
            or sealed["freeze_operation"]["operation_id"] != output["freeze_operation_id"]):
        raise refusal("research freeze differs from the retained manifest")
    frozen = {key: output[key] for key in ("attempt_id", "manifest_digest", "result_id", "freeze_operation_id", "frozen_at")}
    frozen.update(sealed["assignment_ref"]["work_ref"])
    assessment = model_attribution.assessment_of(control, attempt_id)
    cause = None
    if assessment is not None and assessment["outcome"] == "held":
        if any(assessment[key] != frozen[key] for key in ("attempt_id", "manifest_digest", "result_id")):
            raise refusal("research attribution hold belongs to a different frozen result")
        cause = assessment["cause"]
    return frozen, cause


def owner_disposition(store, execution, frozen, cause):
    """Only the committed decision for this phase's exact frozen result permits release."""
    from . import manual

    with store.read_snapshot():
        phase = manual.phase_for_execution(store, execution)
        if phase is None or not phase["settled_at"]:
            return None
        result = phase["result"] or {}
        receipt = result.get("owner_decision")
        if not receipt:
            return None
        target = {"job_id": phase["job_id"], "phase": phase["phase"]}
        key = "manual.finish-phase:" + digest(target)[7:]
        journal = store.operation_record(key)
        if (journal is None or journal["kind"] != "manual.finish-phase" or journal["state"] != "committed"
                or json.loads(journal["result"]) != receipt or receipt["operation_id"] != key
                or any(receipt[k] != target[k] for k in target) or receipt["execution_job_id"] != execution
                or receipt["frozen"] != frozen or phase["frozen"] != frozen
                or result["attempt_id"] != frozen["attempt_id"] or receipt["held_cause"] != cause or phase["held_cause"] != cause
                or (receipt["outcome"], phase["state"]) not in (("success", "completed"), ("failure", "exceptional"))):
            raise refusal("owner disposition does not match this held research attempt and its frozen evidence")
        return receipt


def retained_result(control, attempt_id):
    from ..worker_manager import frozen_output_of, load_manifest
    from ..worker_manager.intake import intake_receipt_of, retentions_of

    frozen = frozen_output_of(control, attempt_id)
    receipt = intake_receipt_of(control, attempt_id)
    if not frozen or frozen["disposition"] != "completed" or not receipt:
        raise refusal("research findings have no completed result in custody")
    sealed = load_manifest(control, frozen["manifest_digest"], "resultManifest")
    artifact_id = attempt_id + ":" + REPORT
    if receipt["custody"] != "accepted" or (receipt["result_id"], receipt["manifest_digest"]) != (frozen["result_id"], frozen["manifest_digest"]):
        raise refusal("the research intake did not accept this frozen result")
    present = [row for row in sealed["outputs"] if row["status"] == "present"]
    if len(present) != 1 or present[0]["name"] != REPORT:
        raise refusal("research findings are missing from the sealed result")
    tree = present[0]["content_manifest"]
    if tree["entry_count"] != 1 or [entry["path"] for entry in tree["entries"]] != ["report.txt"]:
        raise refusal("the retained research output must contain exactly report.txt")
    if len(receipt["artifacts"]) != 1 or len(frozen["artifacts"]) != 1:
        raise refusal("research requires exactly one frozen findings artifact in custody")
    artifact, measured = receipt["artifacts"][0], frozen["artifacts"][0]
    if artifact["artifact_id"] != artifact_id or any(artifact[key] != measured[key] for key in ("artifact_id", "bytes", "content_digest")):
        raise refusal("the custody receipt differs from the frozen findings")
    if (tree["tree_digest"] != artifact["content_digest"] or tree["total_bytes"] != artifact["bytes"]
            or not 0 < artifact["bytes"] <= REPORT_LIMIT):
        raise refusal("research findings are empty or exceed their declared bound")
    if not any(row["artifact_id"] == artifact_id and row["disposition"] == "retain" for row in retentions_of(control, attempt_id)):
        raise refusal("research findings need an explicit retention decision")
    return {"attempt_id": attempt_id, "artifact_id": artifact_id, "locator": artifact["custody_locator"],
            "content_digest": artifact["content_digest"], "bytes": artifact["bytes"]}
