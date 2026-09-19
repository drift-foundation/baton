"""Compose the capacity chain AND CALL ITS VALIDATORS. W197661 claim198943.

Correcting `review-2026-09-18T01-08-25Z.md` R1: `compose.py` serialized seven
dictionaries and hashed them, and its module text, its output and the evidence
all said it *validated a configuration*. It did not call a single validator.
Hash agreement establishes content identity and nothing else. That file and its
outputs are preserved; this one is the correction, and it reports the actual
validator calls and their results.

WHAT IT CALLS, and each is the canonical owner rather than a second opinion:

  `dogfood_operator.input_manifest`   seals each role's input manifest and
                                      holds its policy identities;
  `contracts.check_manifest_structure` holds the sealed document to the frozen
                                      schema after the outputs are set and the
                                      seal recomputed;
  `stage_execution.held_configuration` holds the whole deployment -- workers,
                                      roles, bindings, receipts;
  `job_manager.documents.owned_submission` holds the submission, whose
                                      `input_digest` is taken FROM the seal.

STILL COMPOSES ONLY. It bootstraps nothing, starts nothing, submits nothing and
runs no provider: the lifecycle is the next step and this is what has to be
right before it.

ADAPTED, NOT INHERITED. No old authority, identity, credential, network,
mutable tag, version-control write or execution selection travels from the
reference record. The image is this Work's LABELLED FIXTURE.
"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO / "v12/python"))
sys.path.insert(0, str(REPO / "v12/python/src"))

FIXTURE = json.loads(
    (HERE.parent / "instance-198750/exercise.json").read_text()
)["fixture_image"]["digest"]

DEST = Path("/home/sl/baton-v12-lifecycle-198943")
JOB = "w197661-lifecycle"
WORK = "b0657dfa-W1"           # replaced by the bootstrapped authority's own
UUID = "b0657dfa4b4b4eb4b19f6c7b5252d709"
CREATED = "2026-09-18T01:00:00.000Z"
PROFILE = "w197661-fixture-profile"
TARGET_ID = "w197661-target"
BASE = "0000000000000000000000000000000000000000"

ROLES = ("implementation", "review", "integration")
ACTORS = {"implementation": "baton.claude-author",
          "review": "baton.codex-reviewer",
          "integration": "baton.merge"}


def digest(value):
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True,
                   separators=(",", ":")).encode()).hexdigest()


def main():
    from tools import dogfood_operator, stage_execution
    from baton_v12.contracts import check_manifest_structure
    from baton_v12.job_manager import documents as job_documents
    from baton_v12.worker_manager import source_boundary

    held = json.loads((HERE / "policies.json").read_text())
    policies = {name + "_digest": digest(value) for name, value in held.items()}
    steps = []

    def step(what, run):
        try:
            answer = run()
        except Exception as failure:                       # noqa: BLE001
            steps.append({"validator": what, "result": "REFUSED",
                          "refusal": f"{type(failure).__name__}: "
                                     f"{str(failure)[:400]}"})
            return None
        steps.append({"validator": what, "result": "accepted"})
        return answer

    profile = {"name": PROFILE, "provider": "scripted fixture",
               "selected_base": FIXTURE, "image_variants": {"fixture": FIXTURE},
               "source_profile": "git-line", "roles": list(ROLES),
               "model_selection": "NONE; a deterministic scripted agent",
               "credentials": None, "network": "none"}
    toolchain = {"fixture_image": FIXTURE,
                 "worker_source_manifest": digest({"fixture": FIXTURE})}
    role_instructions = {one: "deterministic fixture; no provider is called"
                         for one in ROLES}
    binding = {"root": "baton",
               "path": "work/records/2026/09/finding-v12-worker-launch-version-mismatch",
               "finding_digest": digest({"finding": "w197661"}),
               "plan_digest": digest({"plan": "w197661"})}
    task = {"schema": "baton.v12.task/1", "task_id": JOB,
            "instructions": "A deterministic fixture turn. No provider runs.",
            "scope": []}
    payload = json.dumps(task, sort_keys=True,
                         separators=(",", ":")).encode()
    # THE EXACT BYTES THAT WERE DECLARED. `held_configuration` compares the
    # task document on disk against the human-contract artifact the manifest
    # names, and an indented rewrite is a different document from the one that
    # was measured -- 153 bytes against a declared 135, which is what it said.
    (HERE / "task.json").write_bytes(payload)

    empty = {"entries": [], "entry_count": 0, "total_bytes": 0,
             "tree_digest": stage_execution.single_worker.EMPTY_TREE_DIGEST}

    def manifest(role):
        given = dogfood_operator.input_manifest(
            work_ref={"authority_uuid": UUID, "work_id": WORK}, staged=empty,
            created_at=CREATED, manifest_id=f"w197661-{role}",
            assignment_contract="v12-assignment-1",
            human_contract={"artifact_id": f"w197661-task-{role}",
                            "media_type": "application/json",
                            "bytes": len(payload),
                            "content_digest": digest(task),
                            "locator": f"artifact://contracts/w197661-{role}"},
            record_binding=binding,
            role_instructions_digest=digest(role_instructions),
            runtime_profile_digest=digest(profile),
            toolchain_digest=digest(toolchain),
            worker_image_digest=FIXTURE, policies=policies)
        given["sources"][0]["consumption"] = \
            source_boundary.source_consumption("git-line")
        constraints = {"max_bytes": 67108864, "max_entries": 2000,
                       "allowed_media_types": ["application/octet-stream",
                                               "text/plain"],
                       "link_policy": "forbid", "validator_digest": None}
        given["outputs"] = [
            {"name": one, "type": kind, "path": one, "required": False,
             "constraints": constraints}
            for one, kind in (("proposal", "git-change-proposal"),
                              ("findings", "directory-result"),
                              ("logs", "directory-result"))]
        # THE SEAL IS RECOMPUTED AFTER THE OUTPUTS, as deployment.py:253-272
        # does: a manifest whose seal predates its own contents is a document
        # that agrees with nothing.
        given.pop("manifest_digest")
        given["manifest_digest"] = digest(given)
        return check_manifest_structure(given, "inputManifest")

    manifests = {}
    for role in ROLES:
        answer = step(f"dogfood_operator.input_manifest + "
                      f"check_manifest_structure ({role})",
                      lambda role=role: manifest(role))
        if answer is None:
            print(json.dumps({"validator_calls": steps}, indent=1))
            return 1
        manifests[role] = answer

    def deployment(role):
        return {
            "schema": "baton.v12.single-worker-deployment/4",
            "authority_store": str(DEST / "db/authority.sqlite3"),
            "authority_uuid": UUID,
            "participant": ACTORS[role],
            "principal": "principal:" + ACTORS[role],
            "profile_name": PROFILE, "profile_digest": digest(profile),
            "policy_digest": policies["policy_digest"],
            "adapter_name": "docker-single-worker",
            "adapter_digest": digest({"adapter": "oci"}),
            "engine": "docker", "image_digest": FIXTURE,
            "network": "none",
            "workspace_storage": str(DEST / "storage"),
            "workspace_group": 1001,
            "launch_home": str(DEST / "launch" / role),
            "credential_home": str(DEST / "credentials" / role),
            "credential_sources": None, "credential_slots": [],
            "credential_profile": {},
            "nominated_source": str(DEST / "repo/workspace"),
            "workspace_capacity": {"max_bytes": 536870912},
            "input_manifest": manifests[role],
            "task_document": str(HERE / "task.json"),
            "launch_contract": "v12-assignment-1", "launch_role": role,
            "review_route": "rview",
            "retention_policy_digest": policies["retention_policy_digest"],
            "retention_disposition": "retain"}

    workers = [{"worker_id": f"w197661-{role}", "role": role,
                "deployment": deployment(role)} for role in ROLES]
    config = {
        "schema": "baton.v12.stage-execution-deployment/1",
        "authority_store": str(DEST / "db/authority.sqlite3"),
        "authority_uuid": UUID,
        "integration_store": str(DEST / "db/integration.sqlite3"),
        "state_root": str(DEST / "state"),
        "pool_generation": 1, "policy_generation": 1,
        "line_declared_base": BASE,
        "receipt_participants": {"verification": "baton.codex",
                                 "review": "baton.codex",
                                 "approval": "baton.slaw"},
        "job_work_id": WORK, "review_work_id": WORK,
        "canonical_target_id": TARGET_ID, "checkpoint_profile": "git",
        "integration_profile": {"profile_kind": "git", "profile_version": 1,
                                "integrator_participant": ACTORS["integration"],
                                "instructions_digest": digest({"i": JOB})},
        "retention_policy_digest": policies["retention_policy_digest"],
        "retention_disposition": "retain", "workers": workers,
        "integration_target": str(DEST / "repo/target.git"),
        "integration_workspace": str(DEST / "repo/workspace")}
    step("stage_execution.held_configuration",
         lambda: stage_execution.held_configuration(config))

    submission = {
        "schema": "baton.v12.job-submission/2",
        "submission_id": "w197661-lifecycle-198943",
        "jobs": [{
            "job_id": JOB,
            # THE INPUT DIGEST COMES FROM THE SEAL, not the other way round.
            "input_digest": manifests["implementation"]["manifest_digest"],
            "policy_digest": policies["policy_digest"],
            "test_scope": [], "terminal_policy": "report-and-hold",
            "stages": [{"kind": kind, "work_id": WORK,
                        "profile_name": PROFILE,
                        "profile_digest": digest(profile),
                        "depends_on": ([] if kind == "implementation" else
                                       [{"job_id": JOB,
                                         "kind": "implementation"}]
                                       if kind == "review" else
                                       [{"job_id": JOB, "kind": "review"}])}
                       for kind in ROLES]}]}
    step("job_manager.documents.owned_submission",
         lambda: job_documents.owned_submission(submission))

    (HERE / "stage-execution.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n")
    (HERE / "submission.json").write_text(
        json.dumps(submission, indent=2, sort_keys=True) + "\n")

    found = {"claim": 198943, "fixture_image": FIXTURE,
             "corrects": "review-2026-09-18T01-08-25Z.md R1: compose.py"
                         " claimed validation it never performed",
             "validator_calls": steps,
             "composes_only": "bootstraps nothing, starts nothing, submits"
                              " nothing, runs no provider",
             "sealed_manifests": {role: one["manifest_digest"]
                                  for role, one in manifests.items()},
             "submission_input_digest": submission["jobs"][0]["input_digest"],
             "derived_from_the_seal": (
                 submission["jobs"][0]["input_digest"]
                 == manifests["implementation"]["manifest_digest"])}
    (HERE / "chain.json").write_text(json.dumps(found, indent=2,
                                                sort_keys=True) + "\n")
    for role, one in manifests.items():
        (HERE / f"manifest-{role}.json").write_text(
            json.dumps(one, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"validator_calls": steps,
                      "sealed": found["sealed_manifests"]}, indent=1))
    return 0 if manifests else 1


if __name__ == "__main__":
    sys.exit(main())
