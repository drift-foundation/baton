"""Re-derive and check every binding in the deployment packet. Deploys nothing.

W197661 claim198640, under owner seq198635. This is the packet's own proof that
it still describes the world: it re-reads the installed manager's identity,
re-derives the required layout from `tools.bootstrap.layout` rather than from
the packet's copy of it, asks the engine about both accepted images, and holds
the fixture rule to the recipes on disk.

IT INSTALLS NOTHING, STARTS NOTHING AND SELECTS NOTHING. No bootstrap, no
scheduler, no container, no Job, no model, no credential, no network, no
production store or runtime touch. Every engine call is a read-only inspection.

A packet that can only be believed is not a packet; a reviewer runs this.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
PACKET = json.loads((HERE / "deployment-packet.json").read_text())

sys.path.insert(0, str(REPO / "v12/python"))
sys.path.insert(0, str(REPO / "v12/python/src"))


def main():
    from tools import bootstrap

    checks = {}
    found = {"checks": checks, "engine": "read-only image inspection only"}

    # 1. THE INSTALLED MANAGER IS STILL THE ONE THIS PACKET BINDS.
    launcher = Path(PACKET["installed_manager"]["launcher"])
    checks["the_launcher_is_present"] = launcher.is_file()
    if checks["the_launcher_is_present"]:
        measured = hashlib.sha256(launcher.read_bytes()).hexdigest()
        checks["the_launcher_bytes_match"] = \
            measured == PACKET["installed_manager"]["launcher_sha256"]
        said = subprocess.run([str(launcher), "identity"], capture_output=True,
                              timeout=120)
        checks["the_manager_answers_identity"] = said.returncode == 0
        if said.returncode == 0:
            identity = json.loads(said.stdout)
            bound = PACKET["installed_manager"]["identity"]
            checks["the_identity_is_unchanged"] = identity == bound
            checks["the_identity_reports_its_own_sha256"] = \
                identity.get("sha256") == measured
            found["identity"] = identity

    # 2. THE ACCEPTED IMAGES ARE PRESENT AND ARE WHAT WAS ACCEPTED.
    accepted = PACKET["accepted_images"]
    for kind in ("provider", "integration"):
        digest = accepted[kind]
        said = subprocess.run(["docker", "image", "inspect", digest],
                              capture_output=True, timeout=120)
        ok = said.returncode == 0
        checks[f"the_{kind}_image_is_present"] = ok
        if not ok:
            continue
        record = json.loads(said.stdout)[0]
        checks[f"the_{kind}_image_id_is_the_accepted_one"] = \
            record["Id"] == digest
        checks[f"the_{kind}_image_runs_as_the_fixed_pair"] = \
            record["Config"]["User"] == "65532:65532"
        checks[f"the_{kind}_image_carries_no_credential_override"] = not any(
            one.startswith(("ANTHROPIC_", "CLAUDE_CODE_OAUTH_TOKEN="))
            for one in record["Config"].get("Env", []))
        entry = ["python3", "/opt/baton/" + ("dogfood_entry.py"
                                             if kind == "provider"
                                             else "integration_entry.py")]
        checks[f"the_{kind}_image_keeps_its_entrypoint"] = \
            record["Config"]["Entrypoint"] == entry
        # THE BASE ANCESTRY IS AN ORDERED PREFIX, as the preparation proved it.
        base = subprocess.run(["docker", "image", "inspect",
                               accepted["immutable_base"],
                               "--format", "{{json .RootFS.Layers}}"],
                              capture_output=True, timeout=120)
        if base.returncode == 0:
            layers = json.loads(base.stdout)
            checks[f"the_{kind}_image_inherits_the_immutable_base"] = \
                record["RootFS"]["Layers"][:len(layers)] == layers

    # 3. THE REQUIRED LAYOUT IS THE CODE'S, NOT THE PACKET'S COPY.
    derived = {name: place.replace("/EXAMPLE", "<DESTINATION>")
               for name, place in bootstrap.layout("/EXAMPLE").items()}
    checks["the_required_layout_is_still_the_bootstrap's"] = \
        derived == PACKET["required_directories"]["layout"]
    capacity = PACKET["configuration"]["part_two_capacity_selection"]
    checks["the_worker_members_are_still_the_bootstrap's"] = \
        capacity["worker_members"] == list(bootstrap._WORKER)
    checks["the_job_members_are_still_the_bootstrap's"] = \
        capacity["job_members"] == list(bootstrap._JOB)
    checks["the_roles_are_still_the_bootstrap's"] = \
        capacity["roles"] == list(bootstrap.ROLES)
    checks["workers_are_still_DEFERRED_from_the_instance_document"] = \
        "workers" in bootstrap.DEFERRED

    # 4. THE INCIDENT'S OWN SELECTION IS STILL WHERE THE PACKET SAYS IT IS.
    stopped = Path("/home/sl/baton-v12-instance-2026-09-17T20-29-21Z"
                   "/deployment.json")
    if stopped.is_file():
        record = json.loads(stopped.read_text())
        digests = [one["deployment"].get("image_digest")
                   for one in record.get("workers", [])]
        checks["the_stopped_instance_still_names_the_stale_image"] = \
            "sha256:2e222e4cf33ff7f52b2048ae1a9c0a2139707e36943328fdd8674b84937f2b13" \
            in digests
        checks["the_stopped_instance_does_not_name_an_accepted_image"] = not (
            set(digests) & {accepted["provider"], accepted["integration"]})
        found["stopped_instance_image_digests"] = digests
    else:
        checks["the_stopped_instance_is_readable"] = False

    # 5. THE FIXTURE RULE IS ABOUT RECIPES THAT EXIST.
    provider_recipe = REPO / "v12/worker/Dockerfile.claude"
    reference_recipe = REPO / "v12/worker/Dockerfile"
    checks["the_provider_recipe_injects_the_real_adapter"] = (
        provider_recipe.is_file()
        and "dogfood_entry.py" in provider_recipe.read_text())
    checks["a_deterministic_fake_provider_has_a_recipe_seam"] = (
        reference_recipe.is_file()
        and "scripted_agent.py" in reference_recipe.read_text())
    # THE INSTRUCTIONS, NOT THE PROSE. A first cut searched the whole recipe
    # for `scripted_agent` and failed: `Dockerfile.claude` has a long comment
    # explaining that `scripted_agent.py` deliberately does NOT travel, and a
    # substring test cannot tell an explanation from a `COPY`.
    instructions = [line for line in provider_recipe.read_text().splitlines()
                    if line.strip() and not line.lstrip().startswith("#")]
    checks["the_accepted_provider_copies_no_scripted_agent"] = not any(
        "scripted_agent" in line for line in instructions)

    found["all_true"] = all(checks.values())
    found["failed"] = [name for name, ok in checks.items() if not ok]
    (HERE / "verification.json").write_text(
        json.dumps(found, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_true": found["all_true"],
                      "checks": len(checks),
                      "failed": found["failed"]}, indent=2))
    return 0 if found["all_true"] else 1


if __name__ == "__main__":
    sys.exit(main())
