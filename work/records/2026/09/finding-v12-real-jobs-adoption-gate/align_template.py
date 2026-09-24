"""Bring SELECTIONS-247941.json in line with what the composer consumes.

Run once under claim 249503 and kept as the record of how the template was
brought into agreement with `two_jobs.INSTANCE_OPERANDS`/`JOB_OPERANDS`. It
adds the missing operands as owner choices; it resolves nothing.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import two_jobs                                             # noqa: E402


def owner(what):
    return f"<OWNER: {what}>"


def main():
    place = HERE / "SELECTIONS-247941.json"
    document = json.loads(place.read_text("utf-8"))
    given = document["arrangement"]
    instance = given["instance"]
    instance.update({
        "policy_generation": 1,
        "checkpoint_profile": owner("the checkpoint profile name, e.g. git"),
        "integration_profile": {
            "profile_kind": owner("the integration profile kind"),
            "profile_version": 1,
            "integrator_participant": owner("the integrator participant"),
            "instructions_digest": owner(
                "the pinned integration instructions digest")},
        "receipt_participants": {
            "verification": owner("the verification receipt participant"),
            "review": owner("the review receipt participant"),
            "approval": owner("the approval receipt participant")},
        "retention_disposition": owner(
            "retain, quarantine or discard-after-intake"),
        "job_work_id": owner(
            "the instance-level Work; _MEMBERS requires it even in a /2 "
            "document, and job_bindings is what actually binds each Job"),
        "review_work_id": owner(
            "the instance-level review Work, equal to job_work_id"),
        "line_declared_base": owner("the instance-level declared base"),
        "canonical_target_id": owner(
            "the canonical target both lines publish against"),
        "policy_digest": owner(
            "the Job and input manifest's exact policy digest"),
        "adapter_name": owner("the deployment's fixed OCI adapter name"),
        "adapter_digest": owner("that adapter's digest"),
        "engine": owner("docker or podman; only docker is certified"),
        "image_digest":
            "sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6"
            "cad334ca2",
        "workspace_group": owner("the provisioned non-authority gid"),
        "credential_slots": owner(
            "the closed list of logical slot names, e.g. [\"api\"]"),
        "credential_profile": owner(
            "the trusted provider/reference mapping for those slots"),
        "workspace_capacity": {"max_bytes": owner(
            "the bytes this assignment declares its writable workspace "
            "needs, proved against free bytes before launch")},
        "launch_contract": owner("the immutable worker launch contract"),
        "review_route": owner(
            "the Route a producer's frozen candidate is passed to"),
        "reviewed_route": owner(
            "the Route a REVIEW worker's own answered assignment is passed "
            "to; it is not the producer's"),
        "submission_id": owner("a fresh submission identity for this run"),
    })
    for one, letter in zip(given["jobs"], "AB"):
        one.update({
            "implementation_principal": owner(
                f"the principal Authority resolves Job {letter}'s producer to"),
            "review_principal": owner(
                f"the principal Authority resolves Job {letter}'s reviewer to"),
            "input_digest": owner(f"Job {letter}'s input manifest identity"),
            "test_scope": owner(
                f"Job {letter}'s test scope: the paths its terminal result is "
                f"judged against"),
            "terminal_policy": "report-and-hold",
            "profile_name": owner(
                f"Job {letter}'s certified implementation profile name"),
            "profile_digest": owner("that profile's digest"),
            "review_profile_name": owner(
                f"Job {letter}'s certified review profile name"),
            "review_profile_digest": owner("that profile's digest"),
            "implementation_input_manifest": owner(
                f"Job {letter}'s complete frozen implementation inputManifest"),
            "review_input_manifest": owner(
                f"Job {letter}'s complete frozen review inputManifest"),
        })
    document.pop("submission", None)
    note = document["_note"]
    line = ("Every operand two_jobs.INSTANCE_OPERANDS and JOB_OPERANDS name "
            "is present here; compose refuses by name if they drift apart.")
    if line not in note:
        note.extend(["", line])
    place.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    missing = ([f"instance.{one}" for one in two_jobs.INSTANCE_OPERANDS
                if one not in instance]
               + [f"jobs[{index}].{name}"
                  for index, one in enumerate(given["jobs"])
                  for name in two_jobs.JOB_OPERANDS if name not in one])
    print(json.dumps({"missing": sorted(missing)}, indent=2))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
