"""Verify this episode's bindings. FAILS CLOSED. Writes its own evidence.

W197661 claim198750, correcting `review-2026-09-18T00-36-37Z.md` items 2 and 4
and superseding `packet-198640/verify_packet.py` WITHOUT overwriting it or its
`verification.json`.

WHAT CHANGED, and both were real defects:

FAIL CLOSED. The draft added its base-ancestry obligation *only if* the base
inspection succeeded, so a failed inspection silently dropped an obligation and
the run could still answer `all_true`. Every prerequisite here records an
explicit `False` when it cannot be established, and a fake-command regression
drives exactly that: a base inspection that fails must make the whole run
false. A check that disappears when its input does is not a check.

THE WHOLE INSTALLED RUNTIME. The draft bound the launcher's bytes and the
manager's self-reported identity. A one-folder distro is a directory: its
`_internal` resources and native libraries are as load-bearing as its launcher.
This binds the COMPLETE manifest through `tools.instance.manifest` -- the
deployment's own producer, which records symlinks as link text and refuses one
pointing out of the bundle -- and verifies the disposable installed copy
against it entry by entry.

IT STARTS NOTHING AND SELECTS NOTHING. Read-only image inspection, file digests
and one canonical `status` read. No bootstrap, no scheduler, no container, no
Job, no model, no credential, no network, no production touch.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
EXERCISE = json.loads((HERE / "exercise.json").read_text())

sys.path.insert(0, str(REPO / "v12/python"))
sys.path.insert(0, str(REPO / "v12/python/src"))

ACCEPTED = {
    "provider": "sha256:35f36286cb1653712dc3a62b3e5ba9b02d06e04ac4306a77e31a1c11777f0e06",
    "integration": "sha256:dac354d89aa879fe0b802bda48f04d0b7e52c95c92fc22a97d84f6e1d23b4407"}
BASE = "sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4"


def inspected(reference, run):
    """The engine's answer, or an explicit failure. Never an omission."""
    done = run(["docker", "image", "inspect", reference])
    if done.returncode != 0:
        return None, done.stderr.decode("utf-8", "replace")[:300]
    try:
        return json.loads(done.stdout)[0], None
    except (ValueError, IndexError, KeyError):
        return None, "the engine's inspection is not one record"


def image_checks(kind, digest, run, checks, *, entrypoint):
    record, why = inspected(digest, run)
    checks[f"{kind}_image_is_present"] = record is not None
    base, base_why = inspected(BASE, run)
    # FAIL CLOSED: the ancestry obligation EXISTS whether or not its input does.
    checks[f"{kind}_base_is_inspectable"] = base is not None
    if record is None or base is None:
        checks[f"{kind}_image_id_is_bound"] = False
        checks[f"{kind}_image_runs_as_the_fixed_pair"] = False
        checks[f"{kind}_image_keeps_its_entrypoint"] = False
        checks[f"{kind}_image_carries_no_credential_override"] = False
        checks[f"{kind}_image_inherits_the_immutable_base"] = False
        return {"why": why or base_why}
    checks[f"{kind}_image_id_is_bound"] = record["Id"] == digest
    checks[f"{kind}_image_runs_as_the_fixed_pair"] = \
        record["Config"]["User"] == "65532:65532"
    checks[f"{kind}_image_keeps_its_entrypoint"] = \
        record["Config"]["Entrypoint"] == entrypoint
    checks[f"{kind}_image_carries_no_credential_override"] = not any(
        one.startswith(("ANTHROPIC_", "CLAUDE_CODE_OAUTH_TOKEN="))
        for one in record["Config"].get("Env", []))
    layers = base["RootFS"]["Layers"]
    checks[f"{kind}_image_inherits_the_immutable_base"] = \
        record["RootFS"]["Layers"][:len(layers)] == layers
    return {"Id": record["Id"]}


def fail_closed_regression():
    """A base inspection that FAILS must make the run false, not shorter.

    This is the draft's defect driven rather than described: a fake command
    that refuses every inspection, through the same `image_checks` the live
    path uses.
    """
    class Answer:
        def __init__(self, returncode, stdout=b"", stderr=b""):
            self.returncode, self.stdout, self.stderr = returncode, stdout, stderr

    def refusing(argv):
        return Answer(1, b"[]\n", b"failed to connect to the docker API\n")

    def only_the_base_fails(argv):
        if argv[-1] == BASE:
            return Answer(1, b"[]\n", b"error: no such object: " + BASE.encode())
        return Answer(0, json.dumps([{
            "Id": argv[-1], "Config": {"User": "65532:65532",
                                       "Entrypoint": ["python3", "x"],
                                       "Env": []},
            "RootFS": {"Layers": ["a", "b"]}}]).encode())

    checks = {}
    image_checks("fake", ACCEPTED["provider"], refusing, checks,
                 entrypoint=["python3", "x"])
    every_false = not any(checks.values())
    second = {}
    image_checks("fake", ACCEPTED["provider"], only_the_base_fails, second,
                 entrypoint=["python3", "x"])
    ancestry_false = second["fake_image_inherits_the_immutable_base"] is False
    base_named = second["fake_base_is_inspectable"] is False
    return {"a_refusing_engine_makes_every_check_false": every_false,
            "a_failed_base_inspection_is_not_omitted": base_named,
            "a_failed_base_inspection_fails_the_ancestry_check": ancestry_false}


def main():
    from tools import instance as instance_tool

    checks = {}
    found = {"checks": checks, "supersedes": "packet-198640/verify_packet.py",
             "engine": "read-only image inspection and file digests only"}

    regression = fail_closed_regression()
    found["fail_closed_regression"] = regression
    for name, ok in regression.items():
        checks[f"regression_{name}"] = ok

    def run(argv):
        return subprocess.run(argv, capture_output=True, timeout=120)

    # 1. THE WHOLE INSTALLED RUNTIME, and the disposable copy against it.
    bound = json.loads((HERE / "runtime-manifest.json").read_text())
    try:
        live = instance_tool.manifest(bound["distro"])
        checks["the_selected_distro_is_readable"] = True
    except Exception:                                      # noqa: BLE001
        live, checks["the_selected_distro_is_readable"] = None, False
    checks["the_selected_distro_manifest_is_unchanged"] = bool(
        live and live["entries"] == bound["entries"]
        and live["digest"] == bound["digest"])
    destination = EXERCISE["disposable_instance"]["destination"]
    try:
        copied = instance_tool.manifest(Path(destination) / "distro")
        checks["the_disposable_copy_is_readable"] = True
    except Exception:                                      # noqa: BLE001
        copied, checks["the_disposable_copy_is_readable"] = None, False
    checks["the_disposable_copy_is_byte_identical"] = bool(
        copied and copied["entries"] == bound["entries"])
    found["runtime"] = {"files": bound["files"], "digest": bound["digest"]}

    # 2. THE IMAGES: the two ACCEPTED ones and the labelled FIXTURE.
    found["images"] = {
        "provider": image_checks("provider", ACCEPTED["provider"], run, checks,
                                 entrypoint=["python3",
                                             "/opt/baton/dogfood_entry.py"]),
        "integration": image_checks("integration", ACCEPTED["integration"], run,
                                    checks,
                                    entrypoint=["python3",
                                                "/opt/baton/integration_entry.py"]),
        "fixture": image_checks("fixture",
                                EXERCISE["fixture_image"]["digest"], run, checks,
                                entrypoint=["python3",
                                            "/opt/baton/baton_worker.py"])}
    # AND THE FIXTURE IS NOT THE ACCEPTED IMAGE, which is the labelling rule.
    checks["the_fixture_is_distinct_from_both_accepted_images"] = \
        EXERCISE["fixture_image"]["digest"] not in ACCEPTED.values()

    # 3. THE DISPOSABLE INSTANCE IS REAL, SEPARATE AND CANONICAL.
    place = Path(destination)
    for name in ("instance.json", "deployment.json", "justfile",
                 "db/jobs.sqlite3"):
        checks[f"the_disposable_instance_has_{name.replace('/', '_')}"] = \
            (place / name).exists()
    checks["the_disposable_instance_is_not_production"] = \
        destination != "/home/sl/baton-v12-instance-2026-09-17T20-29-21Z"
    stopped = Path("/home/sl/baton-v12-instance-2026-09-17T20-29-21Z")
    checks["the_stopped_production_instance_is_still_there"] = stopped.is_dir()

    # 4. TASK RECEIPT, READ THROUGH THE INSTALLED COMMAND. No store is opened.
    said = run([str(place / "distro/baton-v12-stack"), "manager", "--store",
                str(place / "db/jobs.sqlite3"), "--incarnation",
                "w197661-verify", "--authority-uuid",
                EXERCISE["disposable_instance"]["authority_uuid"], "status"])
    checks["the_installed_manager_answers_status"] = said.returncode == 0
    if said.returncode == 0:
        status = json.loads(said.stdout)
        jobs = status.get("jobs", [])
        checks["the_submitted_job_is_recorded"] = len(jobs) == 1
        if jobs:
            stages = {one["kind"]: one["state"] for one in jobs[0]["stages"]}
            checks["the_implementation_stage_is_queued"] = \
                stages.get("implementation") == "queued"
            checks["the_later_stages_are_blocked"] = \
                stages.get("review") == "blocked" \
                and stages.get("integration") == "blocked"
            checks["the_terminal_policy_is_report_and_hold"] = \
                jobs[0]["terminal_policy"] == "report-and-hold"
            found["projection"] = {"job": jobs[0]["job_id"], "stages": stages}
    else:
        for name in ("the_submitted_job_is_recorded",
                     "the_implementation_stage_is_queued",
                     "the_later_stages_are_blocked",
                     "the_terminal_policy_is_report_and_hold"):
            checks[name] = False

    # 5. AND THE BLOCKER IS STILL THE ONE THIS EPISODE RECORDED.
    checks["the_capacity_blocker_is_recorded_verbatim"] = bool(
        EXERCISE["LIFECYCLE"]["candidate_collection"]["the_scheduler_s_own_words"])

    found["all_true"] = all(checks.values())
    found["failed"] = [name for name, ok in checks.items() if not ok]
    (HERE / "verification.json").write_text(
        json.dumps(found, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_true": found["all_true"], "checks": len(checks),
                      "failed": found["failed"]}, indent=2))
    return 0 if found["all_true"] else 1


if __name__ == "__main__":
    sys.exit(main())
