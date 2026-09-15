"""W103525 independent review: offline mutations, never owner-state edits."""
import copy
import json
from pathlib import Path
from tests.tools import scheduler_trace as oracle


def main():
    source = Path(__file__).with_name("trace-155821-composed.json")
    artifacts = {s["name"]: s["artifact"] for s in json.loads(source.read_text())["schedules"]}
    results = {"label": "Synthetic single-boundary mutations of retained real artifacts", "checks": {}}

    def check(name, artifact):
        results["checks"][name] = oracle.validate(artifact)

    sessions = artifacts["composed-role-sessions"]
    check("original_sessions", sessions)
    altered = copy.deepcopy(sessions)
    row = next(r for r in altered["records"] if r.get("session_id"))
    row["session_id"] = row["session_id"].rsplit("/", 1)[0] + "/foreign-provider-id"
    check("foreign_provider_component", altered)
    altered = copy.deepcopy(sessions)
    row = next(r for r in altered["records"] if r.get("session_id") and r["stage_id"].endswith("/review"))
    row["participant"] = "other.unassigned"
    check("foreign_session_participant", altered)
    correction = artifacts["composed-correction"]
    check("original_correction", correction)
    altered = copy.deepcopy(correction)
    altered["records"] = [r for r in altered["records"] if not (r.get("stage_id") or "").endswith("/review") or r["act"] == "reserve"]
    check("review_reservation_only", altered)
    altered = copy.deepcopy(correction)
    for row in altered["records"]:
        if row.get("stage_id") == "job-a/review":
            row["stage_id"] = "job-b/review"
            row["job_id"] = "job-b"
    check("review_attempt_belongs_to_other_job", altered)
    for member, value in (("reviewer_participant", "other.unassigned"),
                          ("reviewer_principal", "principal:other.unassigned"),
                          ("review_assignment_generation", 999)):
        altered = copy.deepcopy(correction)
        row = next(r for r in altered["records"] if r["act"] == "correct")
        row["correction"][member] = value
        check("correction_foreign_" + member, altered)
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
