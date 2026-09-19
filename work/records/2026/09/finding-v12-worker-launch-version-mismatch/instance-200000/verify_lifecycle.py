"""Re-derive every identity this exercise claims. DEPLOYS NOTHING.

A packet that can only be believed is not a packet. Each check below re-reads a
durable artefact and compares it with what the record says, and every one of
them records an explicit True or False -- a check that disappears when its
input does is not a check, which is `verify_packet.py`'s rule kept here.

IT ASSERTS NO SUCCESS THIS EXERCISE DID NOT REACH. The implementation stage did
not conclude, and the checks about that are checks that the UNFINISHED state is
exactly the one reported -- not that it finished.

    python3 verify_lifecycle.py
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DOSSIER = HERE.parent
DEST = Path("/home/sl/baton-v12-lifecycle-198943")
ATTEMPT = ("attempt-432eb7b77502fbb65e041e5400c54464ae47353749dc5fa9408acb6f"
           "617c7af9")


def sha(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main():
    checks = []

    def check(what, answer, detail=None):
        checks.append({"check": what, "held": bool(answer), "detail": detail})
        return bool(answer)

    try:
        return _verify(checks, check)
    except Exception as failure:                             # noqa: BLE001
        # AND AN ARTEFACT THAT IS NOT THERE IS A FAILED VERIFICATION, never an
        # absent one. A missing status document or an unreadable record would
        # otherwise raise out of this function and leave no `verification.json`
        # at all -- which reads to the next person as "not run yet" rather than
        # as "this deployment no longer holds what it claimed".
        check("the verification ran to the end over every artefact", False,
              f"{type(failure).__name__}: {str(failure)[:300]}")
        return _emit(checks)


def _verify(checks, check):
    composition = load(HERE / "composition.json")
    inputs = load(HERE / "bootstrap_inputs.json")
    submission = load(HERE / "submission.json")

    # -- the composition validated, and said so -------------------------------
    check("every required validator accepted", composition["complete"],
          composition["refused"])
    ran = {one["validator"] for one in composition["validator_calls"]
           if one["result"] == "accepted"}
    check("each required validator is in the accepted set",
          all(one in ran for one in composition["required"]),
          sorted(composition["required"]))

    # -- the emitted deployment is the composed one ---------------------------
    emitted = load(DEST / "deployment.json")
    seals = {one["deployment"]["input_manifest"]["manifest_digest"]
             for one in emitted["workers"]}
    check("the installed deployment carries ONE manifest for all three stages",
          len(seals) == 1 and len(emitted["workers"]) == 3, sorted(seals))
    check("that seal is the one the Job names",
          seals == {submission["jobs"][0]["input_digest"]},
          submission["jobs"][0]["input_digest"])
    check("the composed and emitted configurations agree member for member",
          load(HERE / "stage_execution.json") == emitted)

    roles = {one["role"]: one["deployment"] for one in emitted["workers"]}
    roles_named = {one["role"]: one["worker_id"] for one in emitted["workers"]}
    check("three roles are configured", sorted(roles) ==
          ["implementation", "integration", "review"], sorted(roles))
    for member in ("participant", "principal", "launch_home",
                   "credential_home"):
        values = {one[member] for one in roles.values()}
        check(f"every role has its own {member}", len(values) == 3,
              sorted(values))

    # -- the identities are measured, not placeholders ------------------------
    base = emitted["line_declared_base"]
    packed = (DEST / "repo/target.git/packed-refs").read_text()
    named = [line.split(" ", 1)[0] for line in packed.splitlines()
             if line.endswith(" refs/heads/main")]
    check("the declared base is the target repository's own main revision",
          named == [base], {"declared": base, "target": named})
    check("the declared base is not the all-zero placeholder",
          base != "0" * 40, base)
    adapter = composition["adapter"]
    check("the adapter digest is the measured bytes of the named file",
          adapter["sha256"] == sha(Path("/home/sl/src/baton") /
                                   adapter["path"]), adapter["path"])
    binding = composition["record_binding"]
    check("the record binding digests the retained snapshot bytes",
          binding["finding_digest"] == sha(HERE / "record-snapshot/FINDING.md")
          and binding["plan_digest"] == sha(HERE / "record-snapshot/PLAN.md"))
    check("the task document on disk is the width the manifest declares",
          (HERE / "task.json").stat().st_size ==
          roles["implementation"]["input_manifest"]["human_contract"]["bytes"])
    check("the task document on disk is the digest the manifest declares",
          sha(HERE / "task.json") ==
          roles["implementation"]["input_manifest"]["human_contract"][
              "content_digest"])

    # -- the Authority really bound these identities --------------------------
    record = load(DEST / "bootstrap.json")
    bound = record["bindings"].get(inputs["jobs"][0]["job_id"])
    # EVERY MEMBER, and the review 2026-09-18T01-52-22Z is why this is not a
    # tidy-up: the previous form compared the whole expected mapping ONLY when
    # the binding was absent, and in the case that actually happens -- the
    # binding present -- it compared `work_id` and the base alone. So a record
    # binding this Job to another producer or another canonical target would
    # have passed a check whose own name said it compared them.
    asked = inputs["jobs"][0]
    expected = {"work_id": asked["work_id"],
                "line_declared_base": base,
                "canonical_target_id": asked["canonical_target_id"],
                "source_worker_id": asked["source_worker_id"]}
    check("the bootstrap record binds this Job to this Work, base, target "
          "AND producer -- every member, present or absent",
          bound == expected, {"expected": expected, "bound": bound})
    check("the producer it names is this deployment's implementation worker",
          bound is not None
          and bound.get("source_worker_id") == roles_named["implementation"],
          bound.get("source_worker_id") if bound else None)
    check("the Job the record binds is the Job that was submitted",
          list(record["bindings"]) == [submission["jobs"][0]["job_id"]],
          list(record["bindings"]))
    check("the instance identity is the Authority every document names",
          load(DEST / "authority-identity.json")["authority_uuid"]
          == emitted["authority_uuid"]
          == roles["implementation"]["input_manifest"]["work_ref"][
              "authority_uuid"])

    # -- the synthetic credential source is private and labelled --------------
    credential = composition["credential_fixture"]
    held = os.stat(credential["source"])
    check("the synthetic source is a private file this user owns",
          held.st_uid == os.geteuid() and (held.st_mode & 0o077) == 0)
    with open(credential["source"], encoding="utf-8") as handle:
        marker = handle.read()
    check("the synthetic source declares in its own text that it is not one",
          "NOT-A-CREDENTIAL" in marker)
    check("no real deployment's registry is named anywhere",
          "/home/sl/.baton/credential-sources.json" not in
          json.dumps(emitted), credential["registry"])

    # -- the image is this Work's labelled fixture, not an accepted one -------
    image = roles["implementation"]["image_digest"]
    exercise = load(DOSSIER / "instance-198750/exercise.json")
    check("the configured image is the labelled fixture",
          image == exercise["fixture_image"]["digest"], image)
    for name, accepted in exercise["fixture_image"][
            "not_the_accepted_image"].items():
        if name.startswith("accepted"):
            check(f"the configured image is not the {name} digest",
                  image != accepted)
    found = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
        capture_output=True, text=True, timeout=30)
    check("the engine positively holds that exact image",
          found.returncode == 0 and found.stdout.strip() == image,
          found.stdout.strip() or found.stderr.strip()[:200])

    # -- what the lifecycle actually reached, asserted as UNFINISHED ----------
    status = load(DEST / "state/status.json")
    stages = {one["kind"]: one for one in status["jobs"][0]["stages"]}
    check("the Job in the store is this submission's",
          status["jobs"][0]["submission_id"] == submission["submission_id"])
    check("the implementation stage allocated THIS attempt",
          stages["implementation"]["attempt_id"] == ATTEMPT)
    check("the implementation stage is answering and NOT concluded",
          stages["implementation"]["state"] == "answering",
          stages["implementation"]["state"])
    check("review and integration are blocked behind it",
          stages["review"]["state"] == "blocked"
          and stages["integration"]["state"] == "blocked")
    events = (DEST / "launch/implementation" / ATTEMPT / "events")
    terminal = load(events / "terminal.json")
    check("the worker answered the whole exchange and ended completed",
          terminal["disposition"] == "completed"
          and terminal["ending"] == "answered"
          and terminal["answered"] == ["describe", "work"], terminal["ending"])
    reconcile = load(HERE / "build/reconcile-once.json")
    spoken = reconcile["spoken"]
    check("one reconcile tick owes conclude and DEFERS it",
          len(spoken) == 1 and spoken[0]["act"] == "conclude"
          and spoken[0]["outcome"] == "deferred",
          spoken[0] if spoken else None)
    check("the deferral is the already-sealed precondition",
          "output is sealed" in spoken[0]["detail"]["message"],
          spoken[0]["detail"]["message"])
    check("nothing in the operator status surface records that deferral",
          all(one["act"] in ("admit", "claim")
              for one in stages["implementation"]["receipts"]),
          [one["act"] for one in stages["implementation"]["receipts"]])

    return _emit(checks)


def _emit(checks):
    found = {"schema": "baton.w197661.lifecycle-verification/1",
             "claim": 199021, "attempt": ATTEMPT,
             "all_true": bool(checks) and all(one["held"] for one in checks),
             "checks": len(checks),
             "failed": [one for one in checks if not one["held"]],
             "detail": checks}
    (HERE / "verification.json").write_text(
        json.dumps(found, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": found["checks"],
                      "all_true": found["all_true"],
                      "failed": [one["check"] for one in found["failed"]]},
                     indent=1))
    return 0 if found["all_true"] else 1


if __name__ == "__main__":
    sys.exit(main())
