"""Deterministic proof of the fresh instance-3 preparation. No Git, no production.

EXTENDED at claim358517 for review-2026-10-23T05-00-27Z.md. The previous 15
positive checks are preserved and the negatives the review required are added:
every pre-mint refusal must happen WITHOUT CREATING THE DESTINATION, which is
the property the reviewer's reproduction disproved.

THE SHIPPED DEFAULTS ARE EXERCISED, not only synthetic overrides. That lesson
was learned the hard way at claim357900, where four pins were None and the
check that "passed" had handed in its own values. So: `HELPER_PINS` and
`configure.INHERITED_PINS` are used AS SHIPPED by every run below -- they name
the real helper and the real consumption site, which staging does not move --
and `PACKET_PINS` is additionally asserted to be the real digests of the real
packet documents, plus a None pin is proved to refuse.

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

PACKET = pathlib.Path("/home/sl/src/baton/work/records/2026/10/"
                      "finding-v12-native-pilot-instance-packet/fresh3-358443")
sys.path.insert(0, str(PACKET))
import fresh                                                  # noqa: E402

BUILD = pathlib.Path("/home/sl/baton-builds/w325959-30245386-356981")
held = []


def ok(what, answer, **extra):
    one = {"check": what, "ok": bool(answer)}
    one.update(extra)
    held.append(one)
    if not answer:
        raise AssertionError(what)


def refuses(what, call, naming, *, root=None):
    """A refusal counts only when its REASON is the expected one.

    `root` adds the property the review turned on: a refusal that already
    created the destination is not a preflight refusal.
    """
    try:
        call()
    except (Exception, SystemExit) as refusal:                # noqa: BLE001
        said = str(refusal)
        good = naming in said
        one = {"check": what, "ok": good, "refusal": said[:300]}
        if root is not None:
            created = pathlib.Path(root).exists()
            one["destination_created"] = created
            good = good and not created
            if created:
                one["ok"] = False
                raise AssertionError(what + " -- IT CREATED THE DESTINATION")
        one["ok"] = good
        held.append(one)
        if not good:
            raise AssertionError(what + " -- wrong reason: " + said)
        return said
    held.append({"check": what, "ok": False})
    raise AssertionError(what + " -- did not refuse")


class Done:
    def __init__(s, stdout="", returncode=0, stderr=""):
        s.stdout, s.returncode, s.stderr = stdout, returncode, stderr


def runner(argv, **k):
    """A SIMULATED repository tool -- creates plain directories, never a repo."""
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


def stage(home, root, name="packet"):
    """The packet retargeted to `root`, with recomputed pins.

    `root` is what the staged documents will name as their state_root, which is
    why the isolation cases below stage their own copy: pointing a run at a
    destination the packet does not name is refused by the state_root check
    first, and that refusal would hide the one being tested.
    """
    staged = home / name
    staged.mkdir()
    for one in ("install-inputs.json", "configure-inputs.json", "task.json",
                "submission.json"):
        (staged / one).write_text(
            (PACKET / one).read_text().replace(fresh.DESTINATION, str(root)))
    pins = {one: "sha256:" + hashlib.sha256(
        (staged / one).read_bytes()).hexdigest() for one in fresh.PACKET_PINS}
    return staged, pins


answer = {"packet": str(PACKET), "git_executed": False,
          "repository_boundary": "SIMULATED through the product's injected runner",
          "claim": 358517}

# ---- THE SHIPPED PINS ARE REAL DIGESTS OF THE REAL BYTES -------------------
ok("every shipped PACKET_PINS entry is the real digest of the real document",
   all(want and want == "sha256:" + hashlib.sha256(
       (PACKET / name).read_bytes()).hexdigest()
       for name, want in fresh.PACKET_PINS.items()),
   pinned=sorted(fresh.PACKET_PINS))
ok("the shipped HELPER_PINS entry is the real digest of the imported helper",
   all(want == "sha256:" + hashlib.sha256(
       (fresh.SIBLING / name).read_bytes()).hexdigest()
       for name, want in fresh.HELPER_PINS.items()),
   helper=str(fresh.SIBLING))
ok("the shipped INHERITED_PINS resolve at the ACTUAL consumption site",
   all(want and want == "sha256:" + hashlib.sha256(
       (fresh.SIBLING.parent / name).read_bytes()).hexdigest()
       for name, want in fresh.configure.INHERITED_PINS.items()),
   site=str(fresh.SIBLING.parent))
ok("the resolved distro is an executable bundle, no longer PENDING",
   fresh.DISTRO.is_dir() and (fresh.DISTRO / "baton-v12-stack").is_file()
   and os.access(fresh.DISTRO / "baton-v12-stack", os.X_OK),
   distro=str(fresh.DISTRO))

with tempfile.TemporaryDirectory(prefix="fresh3-prove-") as home:
    home = pathlib.Path(home)
    root = home / "native-coordination-pilot-w321608-3"
    distro = stub_bundle(home / "distro")
    src = home / "src"
    (src / "v12").mkdir(parents=True)
    (src / "v12" / "justfile").write_text("# x\n")
    staged, pins = stage(home, root)

    ok("the install document carries NO workers and NO jobs",
       not (json.loads((staged / "install-inputs.json").read_text()).get("workers")
            or json.loads((staged / "install-inputs.json").read_text()).get("jobs")))
    ok("the packet names the selected fresh identifiers",
       json.loads((staged / "configure-inputs.json").read_text())["jobs"][0]["job_id"] == "quickstart-c"
       and json.loads((staged / "submission.json").read_text())["submission_id"] == "sub-w321608-quickstart-3"
       and json.loads((staged / "task.json").read_text())["task_id"] == "w321608-native-operator-quickstart-3")

    # ---- THE REVIEWER'S REPRODUCTION, NOW A REFUSAL -----------------------
    # A malformed task plus a nonexistent bundle and source: the exact input
    # that reported planned: true and then half-installed.
    broken, broken_pins = stage(home, root, "packet-malformed-task")
    (broken / "task.json").write_text("not json at all\n")
    broken_pins["task.json"] = "sha256:" + hashlib.sha256(
        (broken / "task.json").read_bytes()).hexdigest()
    refuses("REPRODUCTION: a malformed task refuses in preflight, creating nothing",
            lambda: fresh.prepare(str(root), broken, apply=False,
                                  bundle=home / "no-such-bundle",
                                  source=home / "no-such-source",
                                  pins=broken_pins),
            "is not valid JSON", root=root)
    refuses("REPRODUCTION: and the SAME input refuses at apply, creating nothing",
            lambda: fresh.prepare(str(root), broken, apply=True,
                                  bundle=home / "no-such-bundle",
                                  source=home / "no-such-source",
                                  pins=broken_pins, runner=runner),
            "is not valid JSON", root=root)

    # ---- PINS, HELPER DRIFT AND TAMPERING ---------------------------------
    tampered, _ = stage(home, root, "packet-tampered")
    # ONE ALTERED BYTE, and `pins` left naming the original. The first attempt
    # at this check staged a byte-identical copy and so tampered with nothing;
    # it reported a pass for a refusal that never happened.
    held_doc = json.loads((tampered / "configure-inputs.json").read_text())
    held_doc["policy_generation"] = 99
    (tampered / "configure-inputs.json").write_text(json.dumps(held_doc))
    refuses("a packet document that does not hash to its pin refuses, creating nothing",
            lambda: fresh.prepare(str(root), tampered, apply=True,
                                  bundle=distro, source=src, pins=pins,
                                  runner=runner),
            "these are not the reviewed bytes", root=root)
    refuses("an UNPINNED consumed document refuses rather than passing on existence",
            lambda: fresh.prepare(str(root), staged, apply=True, bundle=distro,
                                  source=src,
                                  pins=dict(pins, **{"task.json": None}),
                                  runner=runner),
            "has no pinned digest", root=root)
    refuses("helper drift refuses: the imported module is not the accepted one",
            lambda: fresh.prepare(str(root), staged, apply=True, bundle=distro,
                                  source=src, pins=pins,
                                  helper={"configure.py": "sha256:" + "0" * 64},
                                  runner=runner),
            "the helper module configure.py is", root=root)
    refuses("an absent consumed document refuses, creating nothing",
            lambda: fresh.prepare(str(root), staged, apply=True, bundle=distro,
                                  source=src, pins=pins,
                                  inherited={"revision-4/inputs/absent.json":
                                             "sha256:" + "0" * 64},
                                  runner=runner),
            "is missing at", root=root)

    # ---- BUNDLE AND SOURCE PREREQUISITES ----------------------------------
    refuses("a nonexistent bundle refuses, creating nothing",
            lambda: fresh.prepare(str(root), staged, apply=True,
                                  bundle=home / "no-such-bundle", source=src,
                                  pins=pins, runner=runner),
            "is not a directory this preparation can admit", root=root)
    hollow = home / "hollow-bundle"
    hollow.mkdir()
    refuses("a bundle with no baton-v12-stack refuses, creating nothing",
            lambda: fresh.prepare(str(root), staged, apply=True, bundle=hollow,
                                  source=src, pins=pins, runner=runner),
            "carries no baton-v12-stack executable", root=root)
    unarmed = stub_bundle(home / "nonexecutable-bundle")
    (unarmed / "baton-v12-stack").chmod(0o644)
    refuses("a NON-EXECUTABLE bundle command refuses, creating nothing",
            lambda: fresh.prepare(str(root), staged, apply=True, bundle=unarmed,
                                  source=src, pins=pins, runner=runner),
            "is not executable", root=root)
    refuses("a nonexistent repository source refuses, creating nothing",
            lambda: fresh.prepare(str(root), staged, apply=True, bundle=distro,
                                  source=home / "no-such-source", pins=pins,
                                  runner=runner),
            "step 4 clones every non-mirror role from it", root=root)
    notsource = home / "not-the-product"
    notsource.mkdir()
    refuses("a source tree with no v12 directory refuses, creating nothing",
            lambda: fresh.prepare(str(root), staged, apply=True, bundle=distro,
                                  source=notsource, pins=pins, runner=runner),
            "carries no v12 directory", root=root)

    # ---- A RETAINED INSTANCE IS NOT AN INPUT ------------------------------
    inside = pathlib.Path(fresh.RETAINED[1], "distro")
    refuses("a bundle inside a RETAINED instance refuses, creating nothing",
            lambda: fresh.prepare(str(root), staged, apply=True, bundle=inside,
                                  source=src, pins=pins, runner=runner),
            "which lies inside", root=root)
    # A packet that genuinely names a destination nested in a retained
    # instance, so the ISOLATION refusal is the one under test rather than the
    # state_root mismatch.
    nested = pathlib.Path(fresh.RETAINED[0], "nested-3")
    nest_packet, nest_pins = stage(home, nested, "packet-nested-in-instance-1")
    refuses("an instance-3 path inside a retained instance refuses",
            lambda: fresh.prepare(str(nested), nest_packet, apply=True,
                                  bundle=distro, source=src, pins=nest_pins,
                                  runner=runner),
            "a fresh instance isolates its own state", root=nested)

    # ---- A WRONG DESTINATION IS CAUGHT BEFORE THE MINT --------------------
    refuses("a packet whose state_root is another destination refuses",
            lambda: fresh.prepare(str(home / "elsewhere-3"), staged, apply=True,
                                  bundle=distro, source=src, pins=pins,
                                  runner=runner),
            "names state_root")

    ok("after every negative case the destination still does not exist",
       not root.exists())

    # ---- THE POSITIVE PATH, PRESERVED -------------------------------------
    planned = fresh.prepare(str(root), staged, apply=False, bundle=distro,
                            source=src, pins=pins)
    ok("preflight plans and creates nothing", planned.get("planned") is True
       and not root.exists())
    ok("preflight validated the CONTRACTS against a provisional identity, pre-mint",
       planned["static"]["provisional"]["authority_uuid"] == fresh.PROVISIONAL
       and planned["static"]["provisional"]["work"] == "00000000-W1"
       and planned["static"]["provisional"]["manifest_digest"].startswith("sha256:"),
       provisional=planned["static"]["provisional"]["manifest_digest"])
    ok("preflight checked the bundle, the source and every consumed path",
       planned["static"]["prerequisites"]["command"].endswith("baton-v12-stack")
       and "bundle" in planned["noninterference"]["consumed_checked"]
       and "helper" in planned["noninterference"]["consumed_checked"])
    ok("noninterference with instances 1 and 2 is checked",
       planned["noninterference"]["checked_paths"] > 10)

    applied = fresh.prepare(str(root), staged, apply=True, bundle=distro,
                            source=src, pins=pins, runner=runner)
    ok("step 1 minted an authority", len(applied["authority_uuid"]) == 32)
    ok("the minted authority is NOT the provisional rehearsal uuid",
       applied["authority_uuid"] != fresh.PROVISIONAL)
    ok("the Work carries that authority's prefix",
       applied["work"] == applied["authority_uuid"][:8] + "-W1")
    ok("the Work is NOT the instance-2 one", applied["work"] != "673355e1-W1")
    ok("ALL FOUR repositories were prepared by the supported call -- no manual clone",
       applied["repositories"] == ["source-implementation-pilot",
                                   "source-review-pilot", "target.git", "workspace"])
    ok("both stage workers are installed",
       applied["installed_workers"] == ["implementation", "review"])
    ok("the Job is bound", applied["installed_job_bindings"] >= 1)
    # READ FROM THE INSTALLATION ITSELF, not from what we composed: these two
    # used to be asserted as literal True on the grounds that `prepare` refuses
    # otherwise, which proves the refusal exists rather than that it answered.
    installed = json.loads((root / "deployment.json").read_bytes())
    ok("every installed worker names the MINTED authority, not the provisional one",
       [w["deployment"]["authority_uuid"] for w in installed["workers"]]
       == [applied["authority_uuid"]] * len(installed["workers"])
       and fresh.PROVISIONAL not in json.dumps(installed))
    from tools import stage_execution

    ok("the real runtime consumer accepts the INSTALLED configuration",
       stage_execution.held_configuration(installed) is not None)
    ok("the installed manifest carries the shared two-stage output contract",
       [o["name"] for o in
        installed["workers"][0]["deployment"]["input_manifest"]["outputs"]]
       == [o["name"] for o in fresh.configure.SHARED_OUTPUTS]
       and not any(o["required"] for o in
                   installed["workers"][0]["deployment"]["input_manifest"]["outputs"]))
    ok("the readback task digest describes the EMITTED bytes and is not null",
       applied["task_digest"] and applied["task_digest"] == "sha256:"
       + hashlib.sha256(pathlib.Path(
           root, "state", "task",
           "w321608-native-operator-quickstart-3.json").read_bytes()).hexdigest(),
       task_digest=applied["task_digest"])

    # THE WORKSPACES PREREQUISITE -- MEASURED. `bootstrap.storage_bound`
    # derives and bounds workspace_storage but creates nothing, and
    # `workspaces.check_workspace_storage` lstats it and refuses "not a
    # directory this manager can see". So the answer decides whether COMMANDS
    # must carry the prerequisite.
    answer["workspace_storage"] = applied["workspace_storage"]
    answer["workspace_storage_present"] = applied["workspace_storage_present"]
    ok("the workspace storage prerequisite is measured, not assumed",
       len(applied["workspace_storage"]) == 1,
       present=applied["workspace_storage_present"],
       created_by_preparation=all(applied["workspace_storage_present"].values()))

    # ---- BOTH ROLE CONTRACTS, AGAINST THE CLEAN REVIEWED ADAPTER ----------
    sys.path.insert(0, str(BUILD / "src" / "v12" / "worker"))
    sys.path.insert(0, str(BUILD / "src" / "v12" / "python" / "src" / "baton_v12"))
    import claude_agent

    outs = (applied["configured"]["workers"][0]["deployment"]
            ["input_manifest"]["outputs"])
    answer["adapter_source"] = str(pathlib.Path(claude_agent.__file__).resolve())
    ok("the adapter under test is the CLEAN REVIEWED build, not the dirty tree",
       answer["adapter_source"].startswith(str(BUILD)),
       adapter_sha256=hashlib.sha256(
           pathlib.Path(claude_agent.__file__).read_bytes()).hexdigest())
    for role, produce in (("implementation", claude_agent.IMPLEMENTATION_OUTPUTS),
                          ("review", claude_agent.REVIEW_OUTPUTS)):
        chose, absent = claude_agent._selected(outs, produce, role)
        ok("the " + role + " role selects its half and answers the rest absent",
           [o["name"] for o in chose] == list(produce) and absent)
    refuses("a proposal-only declaration still refuses the review role",
            lambda: claude_agent._selected(
                [dict(outs[0], required=True)], claude_agent.REVIEW_OUTPUTS,
                "review"),
            "declares no findings, logs")

    # ---- COLLISION: a second preparation refuses -------------------------
    refuses("a second preparation refuses the existing destination",
            lambda: fresh.prepare(str(root), staged, apply=True, bundle=distro,
                                  source=src, pins=pins, runner=runner),
            "already exists")

    answer["authority_uuid"] = applied["authority_uuid"]
    answer["work"] = applied["work"]
    answer["manifest_digest"] = applied["manifest_digest"]
    answer["input_digest"] = applied["input_digest"]
    answer["repositories"] = applied["repositories"]
    answer["task_digest"] = applied["task_digest"]

answer["checks"] = {"total": len(held),
                    "failed": [o for o in held if not o["ok"]], "checks": held}
answer["limits"] = (
    "Deterministic and disposable. The repository boundary is SIMULATED through "
    "the product's injected runner and the bundle is a STUB satisfying admit's "
    "identity checks. This establishes composition, ordering, both role "
    "declaration contracts and every pre-mint refusal -- NOT that a real "
    "bundle, real clones or a real provider turn succeed.")
print(json.dumps(answer, indent=1, sort_keys=True))
