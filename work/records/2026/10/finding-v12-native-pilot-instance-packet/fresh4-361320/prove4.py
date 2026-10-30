"""Deterministic proof for the revision-4 fresh preparation. W325959.

WHAT IS REUSED AND WHAT IS NEW. The accepted `fresh3-358443/prove.py` already
proved the four-step ordering, the pre-mint gate and thirteen refusals against
revision 3, and that acceptance is not re-litigated here: this packet IMPORTS
its simulated repository runner and stub bundle VERBATIM -- restated rather
than imported, because that file is a script whose whole revision-3 proof runs
at import time -- so the disposable apply below is driven exactly as the
accepted one was. What is new
is this revision -- its four documents, its identities, its real bundle pin,
and the occupied-destination refusal the review asked for by name.

NOTHING REAL IS INSTALLED. Every apply runs against a disposable root with a
SIMULATED repository runner and a STUB bundle, so what is established is
composition, ordering, identity and refusal -- not that a real clone, a real
runtime or a real provider turn succeeds. The real bundle is pinned by digest
through the product's own reader and never installed here.
"""
import io
import json
import os
import pathlib
import sys
import tempfile
import time

PACKET = pathlib.Path(__file__).resolve().parent
ACCEPTED = PACKET.parent / "fresh3-358443"
ROOT = PACKET.parents[5]
sys.path[:0] = [str(ROOT / "v12" / "python" / "src"),
                str(ROOT / "v12" / "python"), str(ACCEPTED), str(PACKET)]
os.environ.setdefault("BATON_V12_STACK_TEST_ROOT", "/var/tmp")

import fresh4                                               # noqa: E402


class Done:
    """One simulated subprocess result."""

    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr


def runner(argv, **named):
    """A SIMULATED repository tool -- plain directories, never a repository.

    RESTATED RATHER THAN IMPORTED, and the reason is mechanical: the accepted
    `fresh3-358443/prove.py` is a SCRIPT whose whole revision-3 proof runs at
    import time, so importing it to borrow two helpers would re-run that
    proof. These two are its own, carried verbatim and credited, with the
    commit this revision reports.
    """
    argv = list(argv)
    if len(argv) > 1 and argv[1] == "clone":
        where = pathlib.Path(argv[-1])
        where.mkdir(parents=True, exist_ok=False)
        (where / ".simulated-git" / "objects" / "info").mkdir(parents=True)
        return Done()
    if len(argv) > 3 and argv[3] == "rev-parse":
        if "--git-common-dir" in argv:
            return Done(str(pathlib.Path(argv[2]) / ".simulated-git"))
        return Done(fresh4.COMMIT)
    return Done()


def stub_bundle(where):
    """A bundle satisfying `admit`'s identity checks. SIMULATED, not a build."""
    where.mkdir(parents=True)
    command = where / "baton-v12-stack"
    command.write_text("#!/bin/sh\ncat <<I\n" + json.dumps(
        {"frozen": True,
         "schema_assets": {"agent-session-1.0": 1, "worker-control-1.0": 1},
         "native_rpds": str(where / "rpds.so")}) + "\nI\n")
    command.chmod(0o755)
    (where / "rpds.so").write_bytes(b"sim\n")
    return where

CHECKS = []


def ok(what, answer, **extra):
    CHECKS.append(dict({"check": what, "outcome": bool(answer)}, **extra))
    return answer


def refuses(what, call, naming, *, root=None):
    try:
        call()
        return ok(what, False, detail="it did not refuse")
    except fresh4.Refused as refusal:
        said = str(refusal)
        made = root is not None and pathlib.Path(root).exists()
        return ok(what, naming in said and not made,
                  detail=said[:220], destination_exists=made)
    except Exception as failure:                             # noqa: BLE001
        return ok(what, False,
                  detail=f"{type(failure).__name__}: {failure}"[:220])


def staged(home, root, name="packet"):
    """This packet's documents RETARGETED to a disposable root, with pins.

    The shipped documents name the real destination and `fresh` refuses a run
    that names another -- a good refusal, and one that would hide every
    other case if the disposable runs did not retarget first. The accepted
    proof's own `stage` does exactly this; the pins are recomputed over the
    staged bytes because they are different bytes.
    """
    import hashlib

    where = pathlib.Path(home, name)
    where.mkdir(parents=True)
    for one in fresh4.PACKET_PINS:
        (where / one).write_text(
            (PACKET / one).read_text().replace(fresh4.DESTINATION, str(root)))
    pins = {one: "sha256:" + hashlib.sha256(
        (where / one).read_bytes()).hexdigest() for one in fresh4.PACKET_PINS}
    return where, pins


def the_real_bundle_is_the_pinned_one():
    held = fresh4.the_bundle()
    ok("the real bundle recomputes to this packet's pin through the "
       "product's own instance.manifest", True,
       files=held["files"], digest=held["digest"])
    ok("the frozen command carries the fresh-attempt verb, so a failure of "
       "THIS revision has a supported retry",
       _frozen_help(), detail="manager fresh-attempt --help")
    # AND THE PACKAGING ACCOUNTING THE REVIEW CORRECTED.
    toc = pathlib.Path("/home/sl/w325959-bundle/work/stack/PYZ-00.toc")
    text = toc.read_text() if toc.is_file() else ""
    ok("`verification_context` is NOT in the bundle's PYZ table of contents: "
       "package membership is not PyInstaller inclusion",
       "verification_context" not in text, detail="corrected accounting")
    ok("`fresh_attempt_ports` and `job_manager.fresh_attempt` ARE",
       "fresh_attempt_ports" in text and "job_manager.fresh_attempt" in text)


def _frozen_help():
    import subprocess

    ran = subprocess.run(
        [str(fresh4.DISTRO / "baton-v12-stack"), "manager", "--store",
         "/nonexistent", "--incarnation", "probe", "--authority-uuid",
         "0" * 32, "fresh-attempt", "--help"],
        capture_output=True, text=True)
    return ran.returncode == 0 and "--prior-job" in ran.stdout


def the_preflight_writes_nothing():
    with tempfile.TemporaryDirectory(prefix="w325959-r4-flight-") as home:
        root = pathlib.Path(home, "destination")
        where, pins = staged(home, root)
        answer = fresh4.prepare(str(root), where, apply=False, pins=pins)
        ok("the preflight validates and plans", answer["preparation"]
           ["static"]["validated"] and answer["preparation"]["step1"]
           ["planned"])
        ok("and it creates nothing at the destination", not root.exists())
        ok("it carries this revision's identities",
           (answer["identities"]["job"], answer["identities"]["submission"],
            answer["identities"]["task"]) ==
           ("quickstart-d", "sub-w321608-quickstart-4",
            "w321608-native-operator-quickstart-4"))


def the_apply_composes_everything():
    """One disposable apply, with a simulated runner and a stub bundle."""
    from tools import stage_execution

    home = tempfile.mkdtemp(prefix="w325959-r4-apply-")
    root = pathlib.Path(home, "destination")
    where, pins = staged(home, root)
    bundle = stub_bundle(pathlib.Path(home, "distro"))
    source = pathlib.Path(home, "src")
    (source / "v12").mkdir(parents=True)
    (source / "v12" / "justfile").write_text("# simulated\n")

    answer = fresh4.prepare(str(root), where, apply=True, bundle=bundle,
                            source=source, runner=runner,
                            pins=pins, check_bundle=False)
    held = answer["preparation"]
    uuid = held["authority_uuid"]
    ok("the apply mints an authority and reads it back", len(uuid) == 32,
       authority=uuid)
    ok("the Work carries THIS authority's prefix",
       held["work"] == uuid[:8] + "-W1", work=held["work"])
    ok("and it is not instance 3's Work", held["work"] != "5a8fa4b4-W1")
    ok("both stages are configured",
       held["installed_workers"] == ["implementation", "review"],
       workers=held["installed_workers"])
    ok("one Job binding is installed",
       held["installed_job_bindings"] == 1)
    ok("all four repositories are prepared",
       len(held["repositories"]) == 4, repositories=held["repositories"])
    ok("the emitted task document digests its own composed bytes",
       held["task_digest"].startswith("sha256:"),
       task_digest=held["task_digest"])

    installed = json.loads(
        pathlib.Path(root, "deployment.json").read_text())
    ok("the installed configuration is one this build accepts",
       stage_execution.held_configuration(installed) is not None)
    submission = held["submission_document"]
    ok("the submission names this revision's Job and submission",
       submission["submission_id"] == "sub-w321608-quickstart-4"
       and submission["jobs"][0]["job_id"] == "quickstart-d")
    ok("the per-invocation limits are preserved exactly",
       submission["jobs"][0]["execution_limits"] ==
       {"provider_turn_seconds": 3600,
        "verification_command_seconds": 900},
       limits=submission["jobs"][0]["execution_limits"])
    ok("the submission names NEITHER instance 3's Job NOR its Work",
       "quickstart-c" not in json.dumps(submission)
       and "5a8fa4b4-W1" not in json.dumps(submission))
    ok("both stages are submitted, review gated on implementation",
       [one["kind"] for one in submission["jobs"][0]["stages"]] ==
       ["implementation", "review"]
       and submission["jobs"][0]["stages"][1]["depends_on"] ==
       [{"job_id": "quickstart-d", "kind": "implementation"}])

    # THE OCCUPIED DESTINATION, asked for by name.
    refuses("a second preparation of the SAME destination refuses",
            lambda: fresh4.prepare(str(root), where, apply=True,
                                   bundle=bundle, source=source,
                                   runner=runner, pins=pins,
                                   check_bundle=False),
            "already")
    ok("and the first installation is untouched: its selector still names "
       "the authority it minted",
       json.loads(pathlib.Path(root, "authority-identity.json").read_text())
       ["authority_uuid"] == uuid)
    return {"root": str(root), "authority": uuid, "work": held["work"]}


def what_it_refuses():
    home = tempfile.mkdtemp(prefix="w325959-r4-refuse-")
    root = pathlib.Path(home, "destination")
    where, pins = staged(home, root)
    bundle = stub_bundle(pathlib.Path(home, "distro"))
    source = pathlib.Path(home, "src")
    (source / "v12").mkdir(parents=True)
    (source / "v12" / "justfile").write_text("# simulated\n")

    broken, _ = staged(home, root, name="broken")
    (broken / "task.json").write_text("{ not json")
    refuses("a malformed packet document refuses before the mint",
            lambda: fresh4.prepare(str(root), broken, apply=True,
                                   bundle=bundle, source=source,
                                   runner=runner,
                                   pins={one: "sha256:" + __import__(
                                       "hashlib").sha256(
                                       (broken / one).read_bytes()
                                   ).hexdigest() for one in
                                       fresh4.PACKET_PINS},
                                   check_bundle=False),
            "task.json", root=root)

    held = dict(pins, **{"task.json": "sha256:" + "0" * 64})
    refuses("a changed pin refuses before the mint",
            lambda: fresh4.prepare(str(root), where, apply=True,
                                   bundle=bundle, source=source,
                                   runner=runner, pins=held,
                                   check_bundle=False),
            "task.json", root=root)

    refuses("an absent bundle refuses before the mint",
            lambda: fresh4.prepare(str(root), where, apply=True,
                                   bundle=pathlib.Path(home, "nowhere"),
                                   source=source, runner=runner,
                                   pins=pins, check_bundle=False),
            "nowhere", root=root)

    # ALL THREE RETAINED INSTANCES, including the one holding quickstart-c.
    # The third is the case the accepted module did not cover, because it did
    # not exist when that module was written.
    for retained in ("native-coordination-pilot-w321608-1",
                     "native-coordination-pilot-w321608-2",
                     "native-coordination-pilot-w321608-3"):
        inside = f"/home/sl/baton-instances/{retained}/inside"
        held, inside_pins = staged(home, inside, name="inside" + retained[-1])
        refuses(f"a destination inside retained {retained[-1]} refuses",
                lambda held=held, inside=inside, p=inside_pins:
                fresh4.prepare(inside, held, apply=False, bundle=bundle,
                               source=source, runner=runner,
                               pins=p, check_bundle=False),
                "lies inside")

    # AND THE ACCEPTED HELPER'S OWN BYTES.
    held = dict(fresh4.ACCEPTED_PINS)
    fresh4.ACCEPTED_PINS["fresh.py"] = "sha256:" + "0" * 64
    try:
        refuses("a drifted accepted helper refuses",
                lambda: fresh4.prepare(str(root), where, apply=False,
                                       bundle=bundle, source=source,
                                       pins=pins, check_bundle=False),
                "fresh.py")
    finally:
        fresh4.ACCEPTED_PINS.update(held)


def main():
    started = time.monotonic()
    the_real_bundle_is_the_pinned_one()
    the_preflight_writes_nothing()
    applied = the_apply_composes_everything()
    what_it_refuses()
    answer = {"revision": 4, "packet": str(PACKET),
              "source_commit": fresh4.COMMIT,
              "bundle": str(fresh4.DISTRO),
              "bundle_digest": fresh4.BUNDLE_DIGEST,
              "disposable_apply": applied,
              "checks": CHECKS,
              "failed": [one for one in CHECKS if not one["outcome"]],
              "seconds": time.monotonic() - started}
    print(json.dumps(answer, indent=1, sort_keys=True, default=str))
    return 1 if answer["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
