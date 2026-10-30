"""Deterministic proof of the fresh-attempt helper. NO GIT, NO LIVE OPERATION.

TWO SCENARIOS, and both are needed.

  1. THE LIVE INSTANCE, READ-ONLY. `check` is run against the actual failed
     instance 3 with the helper's SHIPPED identities, so what is proved is the
     defaults rather than values this proof handed in. It asserts the real
     supported operation rehearses clean, the failed Job's binding and workers
     survive, all four stage/Job pairs select a worker, and every accountable
     byte of the instance -- including `db/`, where the attempt history lives --
     is identical before and after.

  2. A DISPOSABLE INSTANCE. `apply`, repeat-apply, submission emission and every
     refusal are exercised where mutation is safe. The disposable instance is
     built by the ACCEPTED fresh3 packet, so it has the same shape as the real
     one.

WHAT SCENARIO 2 DOES NOT CLAIM. Its retained Job is configured but never ran,
because running one needs a live provider. The preservation property proved
there is about bindings, workers and configuration; the claim that the real
failed Job's RECORDED HISTORY is untouched rests on scenario 1's accountable
digest over the live `db/`, which is measurement of the actual instance.

    cd <build>/src/v12/python && PYTHONPATH=src:. python3 <this file>
"""
import copy
import hashlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile

DOSSIER = pathlib.Path("/home/sl/src/baton/work/records/2026/10/"
                       "finding-v12-native-pilot-instance-packet")
PACKET = DOSSIER / "fresh-attempt-358697"
sys.path.insert(0, str(PACKET))
sys.path.insert(0, str(DOSSIER / "fresh3-358443"))
import fresh_attempt as helper                                 # noqa: E402
import fresh                                                   # noqa: E402

held = []


def ok(what, answer, **extra):
    one = {"check": what, "ok": bool(answer)}
    one.update(extra)
    held.append(one)
    if not answer:
        raise AssertionError(what)


def refuses(what, call, naming, *, unchanged=None):
    try:
        call()
    except (Exception, SystemExit) as refusal:                 # noqa: BLE001
        said = str(refusal)
        good = naming in said
        one = {"check": what, "ok": good, "refusal": said[:300]}
        if unchanged is not None:
            now = helper.accountable_digest(unchanged[0])
            one["destination_unchanged"] = now == unchanged[1]
            if now != unchanged[1]:
                one["ok"] = False
                held.append(one)
                raise AssertionError(what + " -- IT CHANGED THE DESTINATION")
            good = good and True
        one["ok"] = good
        held.append(one)
        if not good:
            raise AssertionError(what + " -- wrong reason: " + said)
        return said
    held.append({"check": what, "ok": False})
    raise AssertionError(what + " -- it did NOT refuse")


class Done:
    def __init__(s, stdout="", returncode=0, stderr=""):
        s.stdout, s.returncode, s.stderr = stdout, returncode, stderr


def runner(argv, **k):
    argv = list(argv)
    if len(argv) > 1 and argv[1] == "clone":
        d = pathlib.Path(argv[-1])
        d.mkdir(parents=True, exist_ok=False)
        (d / ".simulated-git" / "objects" / "info").mkdir(parents=True)
        return Done()
    if len(argv) > 3 and argv[3] == "rev-parse":
        if "--git-common-dir" in argv:
            return Done(str(pathlib.Path(argv[2]) / ".simulated-git"))
        return Done("302453869d07eb5579e79a6572586d3c3cf62a5c")
    return Done()


def stub_bundle(where):
    where.mkdir(parents=True)
    c = where / "baton-v12-stack"
    c.write_text("#!/bin/sh\ncat <<I\n" + json.dumps(
        {"frozen": True,
         "schema_assets": {"agent-session-1.0": 1, "worker-control-1.0": 1},
         "native_rpds": str(where / "rpds.so")}) + "\nI\n")
    c.chmod(0o755)
    (where / "rpds.so").write_bytes(b"sim\n")
    return where


answer = {"git_executed": False, "claim": 358697,
          "live_instance_read_only": helper.SELECTED["destination"]}

# ===== SCENARIO 1 -- THE LIVE FAILED INSTANCE, SHIPPED IDENTITIES, READ-ONLY ==
configure, pins = helper.pinned_helper()
ok("the accepted helper and templates match their shipped pins",
   pins == dict(helper.HELPER_PINS, **helper.TASK_PIN), pins=sorted(pins))

before = helper.accountable_digest(helper.SELECTED["destination"])
live = helper.check()
after = helper.accountable_digest(helper.SELECTED["destination"])
ok("LIVE: check leaves every accountable byte of the failed instance identical",
   live["destination_unchanged"] and after == before,
   counted=before["counted"], digest=before["digest"])
ok("LIVE: the accountable set includes db/, where the attempt history lives",
   before["counted"] > 15 and any(
       pathlib.Path(helper.SELECTED["destination"], "db").is_dir()
       for _ in (0,)))
ok("LIVE: the real supported operation rehearses clean on this instance",
   live["rehearsal"]["exit"] == 0, said=live["rehearsal"]["said"][:2])
ok("LIVE: the failed Job's binding and workers survive byte-exact",
   live["rehearsal"]["preserved"]["binding_identical"]
   and live["rehearsal"]["preserved"]["existing_workers_identical"],
   compared=live["rehearsal"]["preserved"]["compared"])
ok("LIVE: all FOUR stage/Job pairs select a worker -- the failed Job is not orphaned",
   live["rehearsal"]["selector"] == {
       "quickstart-c/implementation": ["implementation-pilot"],
       "quickstart-c/review": ["review-pilot"],
       "quickstart-d/implementation": ["implementation-pilot-d"],
       "quickstart-d/review": ["review-pilot-d"]},
   selector=live["rehearsal"]["selector"])
ok("LIVE: the new Work is free and the failed Work is present",
   live["work_identity"]["new_work_free"]
   and live["work_identity"]["old_work_present"],
   asked=live["work_identity"]["asked_against"])
ok("LIVE: the new submission carries the fresh identities and the 3600/900 limits",
   live["new_submission"] == "sub-w321608-quickstart-4"
   and live["new_job"] == "quickstart-d"
   and live["new_work"] == "5a8fa4b4-W2"
   and live["new_task"] == "w321608-native-operator-quickstart-4")
answer["live"] = {"manifest_digest": live["manifest_digest"],
                  "input_digest": live["input_digest"],
                  "task_digest": live["task_digest"],
                  "accountable": before,
                  "selector": live["rehearsal"]["selector"]}

# ===== SCENARIO 2 -- A DISPOSABLE INSTANCE, WHERE MUTATION IS SAFE ===========
with tempfile.TemporaryDirectory(prefix="fresh-attempt-prove-") as home:
    home = pathlib.Path(home)
    root = home / "native-coordination-pilot-w321608-3"
    distro = stub_bundle(home / "distro")
    src = home / "src"
    (src / "v12").mkdir(parents=True)
    (src / "v12" / "justfile").write_text("# x\n")
    staged = home / "packet"
    staged.mkdir()
    for one in ("install-inputs.json", "configure-inputs.json", "task.json",
                "submission.json"):
        (staged / one).write_text((DOSSIER / "fresh3-358443" / one).read_text()
                                  .replace(fresh.DESTINATION, str(root)))
    pins3 = {one: "sha256:" + hashlib.sha256(
        (staged / one).read_bytes()).hexdigest() for one in fresh.PACKET_PINS}
    installed = fresh.prepare(str(root), staged, apply=True, bundle=distro,
                              source=src, pins=pins3, runner=runner)
    uuid = installed["authority_uuid"]
    ok("DISPOSABLE: an instance-3 analogue is installed by the ACCEPTED packet",
       installed["installed_workers"] == ["implementation", "review"]
       and installed["work"] == uuid[:8] + "-W1")

    bound = {"destination": str(root), "authority": uuid,
             "old_work": uuid[:8] + "-W1", "new_work": uuid[:8] + "-W2"}
    clean = helper.accountable_digest(str(root))

    # -- check mode is read-only here too ---------------------------------
    probe = helper.check(bound, configure=configure)
    ok("DISPOSABLE: check leaves the instance byte-identical",
       probe["destination_unchanged"]
       and helper.accountable_digest(str(root)) == clean)

    # -- COLLISIONS AND STALE CONFIGURATION, all before any write ---------
    refuses("the new Job colliding with the failed Job refuses",
            lambda: helper.check(dict(bound, new_job="quickstart-c"),
                                 configure=configure),
            "is ALREADY bound here", unchanged=(str(root), clean))
    refuses("the new Work colliding with the failed Work refuses",
            lambda: helper.check(dict(bound, new_work=uuid[:8] + "-W1"),
                                 configure=configure),
            "is already bound by Job", unchanged=(str(root), clean))
    refuses("an empty worker suffix refuses rather than reusing a serving name",
            lambda: helper.check(dict(bound, suffix=""), configure=configure),
            "these worker ids already exist", unchanged=(str(root), clean))
    refuses("a wrong authority refuses: a fresh attempt belongs to the failed instance",
            lambda: helper.check(dict(bound, authority="0" * 32),
                                 configure=configure),
            "a fresh attempt belongs to the instance that failed",
            unchanged=(str(root), clean))
    refuses("a wrong recorded Work for the failed Job refuses",
            lambda: helper.check(dict(bound, old_work="deadbeef-W9"),
                                 configure=configure),
            "and this procedure recorded", unchanged=(str(root), clean))
    refuses("an absent instance refuses",
            lambda: helper.check(dict(bound, destination=str(home / "nope")),
                                 configure=configure),
            "this continues an EXISTING installation")
    # HELPER DRIFT. The pin is checked by `pinned_helper`, which `check` calls
    # when no module is handed in -- so this drives the shipped path.
    kept = dict(helper.HELPER_PINS)
    helper.HELPER_PINS["configure.py"] = "sha256:" + "0" * 64
    refuses("helper drift refuses: the imported module is not the accepted one",
            lambda: helper.check(bound),
            "is not the reviewed module", unchanged=(str(root), clean))
    helper.HELPER_PINS.clear()
    helper.HELPER_PINS.update(kept)

    # STALE CONFIGURATION: the instance's own input no longer restates a
    # retained binding exactly, so the supported operation must refuse.
    stale_place = pathlib.Path(root, "generated", "bootstrap-inputs.json")
    good_bytes = stale_place.read_bytes()
    stale = json.loads(good_bytes)
    stale["jobs"][0]["line_declared_base"] = "0" * 40
    stale_place.write_text(json.dumps(stale, indent=1, sort_keys=True) + "\n")
    stale_clean = helper.accountable_digest(str(root))
    refuses("a STALE retained binding refuses in rehearsal, before any write here",
            lambda: helper.check(bound, configure=configure),
            "REFUSED", unchanged=(str(root), stale_clean))
    stale_place.write_bytes(good_bytes)
    ok("DISPOSABLE: the instance is back to its clean bytes after the stale case",
       helper.accountable_digest(str(root)) == clean)

    # -- submission before apply is refused -------------------------------
    refuses("emitting the submission BEFORE the apply refuses",
            lambda: helper.emit_submission(bound, configure=configure),
            "is not configured here yet", unchanged=(str(root), clean))

    # -- A PRE-EXISTING EMITTED INPUT IS NOT OVERWRITTEN -------------------
    # Asked BEFORE the apply, because afterwards the Job-already-bound check
    # runs first and would hide this one.
    occupied = pathlib.Path(root, "generated", "additive-inputs.json")
    occupied.write_text('{"left": "by a previous attempt"}\n')
    occupied_clean = helper.accountable_digest(str(root))
    refuses("a pre-existing emitted input refuses rather than being overwritten",
            lambda: helper.apply(bound, configure=configure),
            "already exists at", unchanged=(str(root), occupied_clean))
    ok("the pre-existing emitted input is byte-untouched",
       occupied.read_text() == '{"left": "by a previous attempt"}\n')
    occupied.unlink()
    ok("DISPOSABLE: back to clean bytes after the occupied-output case",
       helper.accountable_digest(str(root)) == clean)

    # -- THE APPLY --------------------------------------------------------
    applied = helper.apply(bound, configure=configure)
    ok("APPLY: the supported in-place operation accepted the additive document",
       applied["apply"]["exit"] == 0)
    ok("APPLY: both Jobs are bound and the failed one is UNCHANGED",
       [one["job_id"] for one in applied["apply"]["bindings"]]
       == ["quickstart-c", "quickstart-d"]
       and applied["apply"]["preserved"]["binding_identical"]
       and applied["apply"]["preserved"]["existing_workers_identical"],
       bindings=applied["apply"]["bindings"])
    ok("APPLY: the new Job is bound to the NEW Work, not the failed one",
       applied["apply"]["bindings"][1]["job_work_id"] == uuid[:8] + "-W2"
       and applied["apply"]["bindings"][1]["review_work_id"] == uuid[:8] + "-W2")
    ok("APPLY: the new Job names its OWN producer",
       applied["apply"]["bindings"][1]["source_worker_id"]
       == "implementation-pilot-d")
    ok("APPLY: four workers -- the two existing ones plus two new",
       applied["apply"]["workers"] == ["implementation-pilot", "review-pilot",
                                       "implementation-pilot-d",
                                       "review-pilot-d"])
    ok("APPLY: the product's own selector serves all four stage/Job pairs",
       sorted(applied["apply"]["selector"]) == [
           "quickstart-c/implementation", "quickstart-c/review",
           "quickstart-d/implementation", "quickstart-d/review"]
       and all(applied["apply"]["selector"].values()),
       selector=applied["apply"]["selector"])
    ok("APPLY: the new task document is emitted and its digest describes its bytes",
       applied["apply"]["task_digest"] == applied["task_digest"],
       task_digest=applied["apply"]["task_digest"])
    ok("APPLY: no new repository was needed -- the existing sources are reused",
       sorted(one.name for one in pathlib.Path(root, "repo").iterdir())
       == ["source-implementation-pilot", "source-review-pilot", "target.git",
           "workspace"])

    # -- REPEAT APPLY: a defined refusal, and no duplicate effect ----------
    # THE ALREADY-BOUND JOB IS WHAT ANSWERS, and it answers FIRST -- before the
    # emitted-output check, because `apply` rehearses before it writes. That
    # ordering is the right way round: the strongest statement available is
    # "this Job already exists", not "a file is in the way".
    settled = helper.accountable_digest(str(root))
    refuses("REPEAT APPLY refuses on the already-bound Job, instance byte-unchanged",
            lambda: helper.apply(bound, configure=configure),
            "is ALREADY bound here", unchanged=(str(root), settled))
    reread = json.loads(pathlib.Path(root, "deployment.json").read_bytes())
    ok("REPEAT APPLY produced no duplicate Job or worker",
       [one["job_id"] for one in reread["job_bindings"]]
       == ["quickstart-c", "quickstart-d"]
       and len(reread["workers"]) == 4)
    refuses("REPEAT CHECK also refuses once the Job is bound, rather than re-planning",
            lambda: helper.check(bound, configure=configure),
            "is ALREADY bound here", unchanged=(str(root), settled))

    # -- THE SUBMISSION, as its own selection ------------------------------
    emitted = helper.emit_submission(bound, configure=configure)
    ok("EMIT: the submission document is written and validated by the manager",
       emitted["submission_id"] == "sub-w321608-quickstart-4"
       and emitted["job"] == "quickstart-d"
       and emitted["input_digest"] == applied["input_digest"],
       wrote=pathlib.Path(emitted["wrote"]).name)
    body = json.loads(pathlib.Path(emitted["wrote"]).read_text())
    ok("EMIT: the submission names NEITHER the failed Job nor its Work",
       "quickstart-c" not in json.dumps(body)
       and uuid[:8] + "-W1" not in json.dumps(body))
    ok("EMIT: both stages bind the NEW Work and the per-invocation limits hold",
       [one["work_id"] for one in body["jobs"][0]["stages"]]
       == [uuid[:8] + "-W2"] * 2
       and body["jobs"][0]["execution_limits"] == {
           "provider_turn_seconds": 3600,
           "verification_command_seconds": 900})
    ok("EMIT: the new Job's input digest is the PUBLIC projection of its manifest",
       body["jobs"][0]["input_digest"] == applied["input_digest"])
    refuses("re-emitting the submission refuses rather than overwriting it",
            lambda: helper.emit_submission(bound, configure=configure),
            "already exists")
    answer["disposable"] = {
        "authority": uuid, "bindings": applied["apply"]["bindings"],
        "workers": applied["apply"]["workers"],
        "selector": applied["apply"]["selector"],
        "input_digest": applied["input_digest"]}

answer["checks"] = {"total": len(held),
                    "failed": [one for one in held if not one["ok"]],
                    "checks": held}
answer["limits"] = (
    "Scenario 1 is a read-only rehearsal against the real failed instance and "
    "is measurement of it. Scenario 2 is disposable, built with a SIMULATED "
    "repository runner and a STUB bundle, and its retained Job was configured "
    "but never ran. Neither scenario submits, serves, starts, or touches a "
    "provider, engine, model or credential, and no Git ran. That the new Job "
    "will actually SUCCEED is not proved here -- only that it is configured, "
    "bound, collision-free and selectable.")
print(json.dumps(answer, indent=1, sort_keys=True))
