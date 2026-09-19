"""Compose and VALIDATE the capacity chain for a disposable lifecycle.

W197661 claim198871, under owner seq198635 and `review-2026-09-18T00-56-06Z.md`,
which named the two composition references this adapts: `dogfood_operator
.input_manifest` for the sealed manifest, and `prepared-149053/deployment.py`
for tasks, policies, worker deployments, stage configuration and a submission
bound to the sealed manifest.

ADAPTED, NOT INHERITED. No old authority, identity, credential, network,
mutable tag, version-control write or execution selection travels from that
record. The image is this Work's LABELLED FIXTURE, the identities are this
episode's own, and nothing here runs a provider or a model.

THE CANONICAL OWNERS DECIDE WHETHER IT COMPOSES. `stage_execution
.held_configuration` and the Job manager's own submission reader are what say
yes or no; a refusal names the next missing selection, which is exactly how the
submission in `instance-198750` was built. This script validates only -- it
bootstraps nothing, starts nothing and submits nothing.
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

DEST = Path("/home/sl/baton-v12-lifecycle-198871")
JOB = "w197661-lifecycle"
ROLES = ("implementation", "review", "integration")
# INDEPENDENT PARTICIPANTS AND PRINCIPALS, which `DEPLOYMENT-INPUTS-185653.md`
# records as a rule rather than a convention: implementation and review may
# share neither participant nor principal.
ACTORS = {"implementation": "baton.claude-author",
          "review": "baton.codex-reviewer",
          "integration": "baton.merge"}


def digest(value):
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True,
                   separators=(",", ":")).encode()).hexdigest()


def policy_documents():
    """This episode's own selections. Deterministic, offline, no credential."""
    from baton_v12.worker_manager import source_boundary

    return {
        "policy": {
            "work": "W197661",
            "ruling": "owner seq198635: a bounded disposable deterministic"
                      " lifecycle exercised with a fake provider",
            "automatic_retry": False, "review_before_execution": True,
            "submission": [JOB]},
        "resource_policy": {
            "wall_seconds": 600, "implementation_attempt_seconds": 120,
            "review_or_judge_attempt_seconds": 90, "integration_seconds": 60,
            "runtime_cpus": 2, "runtime_memory_bytes": 2147483648,
            "runtime_pids": 512,
            "scratch_mounts": [list(one) for one
                               in source_boundary.SCRATCH_MOUNTS],
            "workspace_declared_capacity_bytes": 536870912,
            "workspace_capacity_is_quota": False,
            "deadline_action": "stop; retain evidence; no retry"},
        # NO NETWORK. The fixture is a scripted agent; it calls nothing, so a
        # bridge would be a capability this exercise has no use for.
        "network_policy": {"engine_network": "none",
                           "purpose": "a deterministic fixture reaches nothing"},
        "mount_policy": {
            "source": "read-only original source and a manager-held private"
                      " development line",
            "mutable_storage": str(DEST / "storage"),
            "target": str(DEST / "repo/target.git"),
            "target_reference": "refs/heads/main"},
        "tool_policy": {
            "provider_arguments": [],
            "model_selection": "NONE; a scripted deterministic agent",
            "verification": [], "final_verification": []},
        # NO CREDENTIAL IS SELECTED AND NONE IS INHERITED. The review is
        # explicit that the referenced record's live credentials must not
        # travel, and a scripted agent authenticates to nothing.
        "credential_policy": {"registry": None, "slots": {},
                              "payload_in_configuration": False},
        "retention_policy": {"disposition": "retain", "root": str(DEST),
                             "automatic_deletion": False}}


def main():
    held = policy_documents()
    digests = {name + "_digest": digest(value) for name, value in held.items()}
    (HERE / "policies.json").write_text(
        json.dumps(held, indent=2, sort_keys=True) + "\n")
    found = {"claim": 198871, "fixture_image": FIXTURE,
             "destination": str(DEST), "job_id": JOB,
             "actors": ACTORS, "policy_digests": digests,
             "composes_only": "this script validates a configuration; it"
                              " bootstraps nothing, starts nothing, submits"
                              " nothing and runs no provider"}
    (HERE / "composition.json").write_text(
        json.dumps(found, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"fixture_image": FIXTURE,
                      "policy_digests": len(digests),
                      "written": ["policies.json", "composition.json"]},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
