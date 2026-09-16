"""W177936 fixture. --audit is offline; --run awaits separate owner selection."""
import argparse
import grp
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import select
import signal
import stat
import subprocess
import sys
import time
import uuid

# Validate the selected package before importing its executable helper. Imports
# in the offline test module are made from the locally authored fixture bytes.
if __name__ == "__main__":
    try:
        directory_at_start = Path(__file__).resolve().parent
        manifest_raw = (directory_at_start / "qualification-manifest.json").read_bytes()
        pinned = json.loads(manifest_raw)
        if "--run" in sys.argv:
            position = sys.argv.index("--approved-manifest")
            assert hashlib.sha256(manifest_raw).hexdigest() == sys.argv[position + 1]
        assert set(pinned["files"]) == {"qualification-fixture.py", "qualification_contract.py", "qualification_worker.py", "test_qualification.py"}
        for filename, digest in pinned["files"].items():
            path = directory_at_start / filename
            assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == digest
    except BaseException:
        print('{"outcome":"package-not-verified"}')
        sys.exit(1)

import qualification_contract as c

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "qualification-manifest.json"
SOURCE = Path("/home/sl/.claude/.credentials.json")
# THE FIXED RUN IDENTITY. Owner 2026-09-16T03:35:29Z. THREE identities are now
# consumed and none is reusable: 178579 by the initial-artifact failure
# (run179075), 180078 by the collection failure, and 183114 by the publication
# failure. The fixture refuses a taken root rather than repairing it, so a rerun
# needs a new NAME, never a reset marker. All three earlier root sets and their
# evidence stay exactly where they are; this is a fourth name, not a replacement
# for any of them.
#
# `EXPORT` is derived from ROOT in `run`, so these two lines plus that
# derivation are the whole identity, and the manifest below declares all three
# and is checked against them at audit time.
IDENTITY = "183372"
ROOT = Path("/tmp/baton-w177936-qualification-" + IDENTITY)
VOLATILE = Path("/dev/shm/baton-w177936-qualification-" + IDENTITY)
DOCKER = ("/usr/bin/docker", "--host", "unix:///var/run/docker.sock")
ENGINE_DEADLINE = None
DOCKER_ENV = {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "DOCKER_CONFIG": "/nonexistent"}


def export_root():
    """Derived from ROOT, in ONE place, so the three roots stay one identity.

    `audit` and `run` both go through here; a second copy of the derivation is
    exactly how the manifest's declared export root and the reserved one would
    drift apart.
    """
    return ROOT.with_name(ROOT.name + "-export")


def audit(expected=None):
    raw = c.read_file(MANIFEST)
    manifest = c.decoded(raw)
    if expected is not None:
        c.require(c.sha(raw) == expected, "manifest-digest")
    # The declared identity must BE the identity this code would take. Without
    # this the manifest's root fields are decorative: an approved manifest could
    # name one set of roots while the fixture reserved another, and the digest
    # would still verify. The three roots are one identity, so all three are
    # declared and all three are checked.
    c.require(manifest["image"] == c.IMAGE and manifest["group"] == c.GROUP and manifest["model"] == c.MODEL and
              manifest["private_root"] == str(ROOT) and manifest["credential_copy_root"] == str(VOLATILE) and
              manifest["export_root"] == str(export_root()) and manifest["run_identity"] == IDENTITY, "manifest-constants")
    c.require(set(manifest["files"]) == {"qualification-fixture.py", "qualification_contract.py", "qualification_worker.py", "test_qualification.py"}, "manifest-file-set")
    for name, digest in manifest["files"].items():
        c.require(c.sha(c.read_file(HERE / name, 256 * 1024)) == digest, "fixture-drift")
    return c.sha(raw)


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        raw = c.encoded(value)
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(temporary, path)


def event(root, kind, **facts):
    record = {"event": kind, "monotonic_ns": time.monotonic_ns(), **facts}
    fd = os.open(root / "events.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(c.encoded(record) + b"\n")
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)


def engine(arguments, seconds=20):
    """Bound the actual Docker client, including its output and child group."""
    if ENGINE_DEADLINE is not None:
        seconds = min(seconds, ENGINE_DEADLINE - time.monotonic())
    c.require(seconds > 0, "engine-deadline")
    process = subprocess.Popen([*DOCKER, *arguments], env=DOCKER_ENV, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
    data = bytearray()
    deadline = time.monotonic() + seconds
    try:
        fd = process.stdout.fileno()
        os.set_blocking(fd, False)
        eof = False
        while not eof or process.poll() is None:
            left = deadline - time.monotonic()
            c.require(left > 0, "engine-timeout")
            if not eof and select.select([fd], [], [], min(left, 0.1))[0]:
                piece = os.read(fd, 4096)
                eof = not piece
                data.extend(piece)
                c.require(len(data) <= 2 * 1024 * 1024, "engine-output-bound")
            elif eof:
                time.sleep(min(left, 0.01))
        c.require(process.returncode == 0, "engine-refused")
        return bytes(data)
    finally:
        try:
            process.kill()
        except ProcessLookupError:
            pass
        process.wait(timeout=3)
        process.stdout.close()


def inspect(name, kind="container"):
    values = c.decoded(engine([kind, "inspect", name]))
    c.require(type(values) is list and len(values) == 1, "inspect-shape")
    return values[0]


def directory(path):
    path.mkdir(mode=0o700)
    os.chown(path, -1, c.GROUP)
    os.chmod(path, 0o2770)


def private_file(path, raw, group=False, writable=False):
    """One manager-owned file, at the mode its ROLE actually needs.

    R1, review 2026-09-15T14-36-52Z. `group=True` alone is 0640: the runtime
    can READ it and cannot write it. That is exactly right for the two objects
    this fixture hands the container as inputs -- the credential slot copy and
    the request document, both mounted read-only -- and exactly wrong for the
    reconstructed session state, which the accepted design calls a WRITABLE
    working copy and mounts writable.

    SETGID ON THE PARENT SUPPLIES GROUP IDENTITY, NOT FILE WRITE PERMISSION,
    and that is the confusion the review caught. Uid 65532 holds gid 1001 as a
    supplementary group, so a 0640 manager-owned file is readable and not
    appendable by it. A group-writable parent may let the CLI unlink and
    replace instead, so this is not a claim that the provider would certainly
    fail -- it is that the fixture would be qualifying a read-only input under
    the name of a writable working copy, and a negative result would not mean
    what the packet says it means.

    `writable=True` is therefore its own operand rather than a widened default:
    every existing protected object keeps 0640 by construction, and only the
    newly reconstructed per-use state is 0660.
    """
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        if group:
            os.fchown(fd, -1, c.GROUP)
            os.fchmod(fd, 0o660 if writable else 0o640)
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)


def prepare_home(root, turn):
    use = root / ("use-" + str(turn))
    directory(use)
    home = use / "home"
    directory(home)
    directory(home / ".claude")
    (home / ".claude/.credentials.json").symlink_to(c.SLOT)
    return use, home


def credential(turn):
    # Executed only after the explicit --run boundary. Never called by audit
    # or offline verification. No bearer bytes enter an export or diagnostics.
    info = SOURCE.lstat()
    c.require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o077, "credential-source-boundary")
    raw = c.read_file(SOURCE)
    path = VOLATILE / ("slot-" + str(turn))
    private_file(path, raw, group=True)
    return path


def create_vector(name, nonce, network, use, workspace, slot, request):
    mounts = [(use, "/run/baton/context", False), (workspace, "/output", False),
              (slot, c.SLOT, True), (request, "/qualification/request.json", True),
              (HERE / "qualification_worker.py", "/qualification/qualification_worker.py", True),
              (HERE / "qualification_contract.py", "/qualification/qualification_contract.py", True)]
    args = ["create", "--pull=never", "--name", name, "--label", "baton.qualification=" + nonce,
            "--network", network, "--user", c.USER, "--group-add", str(c.GROUP), "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--read-only", "--pids-limit", "64", "--memory", "2g", "--cpus", "1",
            "--tmpfs", "/tmp:rw,nosuid,nodev,mode=1777,size=268435456", "--workdir", "/output",
            "--env", "PYTHONPATH=/qualification", "--env", "PYTHONDONTWRITEBYTECODE=1", "--entrypoint", "python3"]
    for source, target, readonly in mounts:
        c.require("," not in str(source), "mount-path")
        args.extend(["--mount", f"type=bind,src={source},dst={target},bind-propagation=rprivate" + (",readonly" if readonly else "")])
    return args + [c.IMAGE, "-u", "/qualification/qualification_worker.py"], mounts


def validate_runtime(value, identity, nonce, network, mounts):
    c.require(value["Id"] == identity and value["Image"] == c.IMAGE and value["Config"]["Labels"].get("baton.qualification") == nonce, "runtime-identity")
    host = value["HostConfig"]
    c.require(value["Config"]["User"] == c.USER and host["NetworkMode"] == network and
              host["ReadonlyRootfs"] is True and host["Privileged"] is False and host["PidsLimit"] == 64 and
              host["Memory"] == 2147483648 and host["NanoCpus"] == 1000000000 and
              host["GroupAdd"] == [str(c.GROUP)] and host["CapDrop"] == ["ALL"] and
              "no-new-privileges" in host["SecurityOpt"], "runtime-posture")
    observed = {(m["Source"], m["Destination"], m["RW"]) for m in value["Mounts"] if m["Type"] == "bind"}
    c.require(observed == {(str(source), target, not readonly) for source, target, readonly in mounts}, "runtime-mounts")
    c.require(all(m.get("Propagation") == "rprivate" for m in value["Mounts"] if m["Type"] == "bind"), "mount-propagation")


def arm(root, nonce, network, turn, session, text, use, workspace, prior=None):
    if turn == 2:
        c.may_restore(prior)
    name = "w177936-" + nonce + "-" + str(turn)
    slot = credential(turn)
    request = root / ("request-" + str(turn) + ".json")
    private_file(request, c.encoded({"session": session, "turn": turn, "prompt": text}), group=True)
    vector, mounts = create_vector(name, nonce, network, use, workspace, slot, request)
    event(root, "container-create-intent", turn=turn, name=name)
    identity = engine(vector).decode().strip()
    c.require(len(identity) == 64 and all(x in "0123456789abcdef" for x in identity), "created-identity")
    event(root, "container-created", turn=turn, container=identity)
    observed = inspect(identity)
    validate_runtime(observed, identity, nonce, network, mounts)
    event(root, "user-turn-intent", turn=turn, container=identity, prompt_sha256=c.sha(text.encode()))
    raw = engine(["start", "--attach", identity], seconds=c.TURN_SECONDS + 15)
    observed = inspect(identity)
    receipt = c.stopped(observed, identity, nonce)
    event(root, "shutdown-observed", turn=turn, container=identity, running=False, pid=0)
    c.consume(receipt)
    event(root, "shutdown-receipt-consumed", turn=turn, container=identity)
    slot.unlink()
    record = c.decoded(raw)
    if type(record) is dict and set(record) == {"outcome", "provider_started", "failure_code", "publication", "observed"} and record["outcome"] == "failed":
        code = record["failure_code"]
        c.require(type(code) is str and code in c.REFUSAL_CODES and type(record["provider_started"]) is bool, "worker-failure-shape")
        # The closed publication diagnostic, and an observation the worker had
        # already made before the failure. Both optional; neither may be
        # malformed, and NEITHER TURNS A FAILED ARM INTO A PASS -- the refusal
        # below is raised exactly as before.
        c.require(record["publication"] is None or c.valid_publication(record["publication"]), "worker-failure-shape")
        preserved = record["observed"]
        if preserved is not None:
            c.require(type(preserved) is dict and set(preserved) == {"provider_exit", "terminal"} and
                      type(preserved["provider_exit"]) is int and -128 <= preserved["provider_exit"] <= 255,
                      "worker-failure-shape")
            # THE SAME validator the observed path uses. A shorter copy here
            # is exactly how six fields went unchecked on this path only.
            c.require(c.valid_terminal(preserved["terminal"], session), "worker-failure-shape")
        record["shutdown"] = receipt
        save(root / ("arm-" + str(turn) + ".json"), record)
        event(root, "provider-start-observed", turn=turn, started=record["provider_started"])
        raise c.Refusal(code)
    c.require(type(record) is dict and set(record) == {"outcome", "provider_started", "provider_exit", "terminal", "argv", "environment_keys", "cwd", "uid", "groups", "home_mode", "published"}, "worker-record-shape")
    terminal = record["terminal"]
    c.require(type(terminal) is dict and set(terminal) == c.TERMINAL_MEMBERS, "terminal-record-shape")
    # ONE validator, used by this path and by the preserved-observation path
    # above. `consistent` inside it refuses a record whose diagnostics
    # contradict its own verdict.
    c.require(type(record["provider_exit"]) is int and -128 <= record["provider_exit"] <= 255 and
              c.valid_terminal(terminal, session), "terminal-record-values")
    expected = c.argv(session, turn, text)
    c.require(record["outcome"] == "observed" and record["provider_started"] is True and
              record["argv"] == expected[:-1] + [{"prompt_sha256": c.sha(text.encode())}] and
              record["cwd"] == "/output" and record["uid"] == 65532 and type(record["groups"]) is list and set(record["groups"]) in ({c.GROUP}, {c.GROUP, 65532}) and
              record["environment_keys"] == sorted(c.environment()) and record["home_mode"] == "0o2770" and
              # P1a publishes in turn 1 and NEVER in turn 2, whose home is
              # manager-reconstructed at the accepted 0o660.
              record["published"] == ({"project_mode": "0o2750", "session_mode": "0o640"} if turn == 1 else None), "worker-observation")
    record["shutdown"] = receipt
    event(root, "provider-start-observed", turn=turn, started=record["provider_started"])
    save(root / ("arm-" + str(turn) + ".json"), record)
    return record


def controller(root, nonce):
    # The parent can terminate this exact controller/client process group even
    # when a Docker create answer was lost. In-process offline tests disable it.
    os.setsid()
    outcome = {"outcome": "failed", "stage": "preflight", "arms": [],
               "gaps": {**{f"G{i}": "unobserved" for i in range(1, 7)}, "G7": "qualification-image-selected", "G8": "not-composed"}}
    try:
        image = inspect(c.IMAGE, "image")
        c.require(image["Id"] == c.IMAGE and not image["Config"].get("Volumes"), "image-not-local-or-drift")
        network_name = "w177936-" + nonce
        network = engine(["network", "create", "--driver", "bridge", "--label", "baton.qualification=" + nonce, network_name]).decode().strip()
        held = inspect(network, "network")
        c.require(held["Name"] == network_name and held["Labels"].get("baton.qualification") == nonce and held["Driver"] == "bridge", "network-identity")
        outcome["network"] = network
        workspace = root / "work"
        directory(workspace)
        session, token = str(uuid.uuid4()), uuid.uuid4().hex
        outcome["session"] = session
        use1, home1 = prepare_home(root, 1)
        outcome["stage"] = "first-turn"
        save(root / "outcome.json", outcome)
        first = arm(root, nonce, network, 1, session, c.prompt(1, token), use1, workspace)
        outcome["arms"].append(first)
        outcome["gaps"]["G1"] = "observed" if first["terminal"]["actual_model"] else "model-unobserved-or-conflicting"
        outcome["gaps"]["G4"] = "first-cwd-observed"
        outcome["gaps"]["G6"] = "first-home-mode-observed"
        c.require(first["provider_exit"] == 0 and c.success(first["terminal"]), "first-turn-unsuccessful")
        # OBSERVED, THEN JUDGED. The record is exported whether or not the bytes
        # are accepted, so a refusal carries the observed digest and length
        # rather than only a code. The controller never writes to the workspace.
        names = sorted(p.name for p in workspace.iterdir())
        event(root, "workspace-observed", turn=1, entry_count=len(names), expected_set=names == ["solution.py"])
        c.require(names == ["solution.py"], "initial-artifact")
        initial = c.artifact_record(c.read_file(workspace / "solution.py"), c.INITIAL)
        outcome["initial_artifact"] = initial
        save(root / "outcome.json", outcome)
        c.require(initial["form"] in c.ARTIFACT_FORMS, "initial-artifact")
        outcome["stage"] = "collection"
        save(root / "outcome.json", outcome)
        # P1c. The step is recorded BEFORE each operation, so a failure names
        # where it happened even though the exception itself never crosses.
        outcome["collection_step"] = "source-inventory"
        rows = c.inventory(home1)
        outcome["collection_step"] = "subset-selection"
        chosen = c.subset(rows, session)
        outcome["collection_step"] = "private-layout-save"
        save(root / "private-layout.json", {"inventory": rows, "selected": chosen})
        outcome["collection_step"] = "destination-home"
        use2, home2 = prepare_home(root, 2)
        outcome["collection_step"] = "state-copy"
        for row in chosen:
            target = home2 / row["path"]
            pending = []
            parent = target.parent
            while not parent.exists():
                pending.append(parent)
                parent = parent.parent
            for parent in reversed(pending):
                directory(parent)
            raw = c.read_file(home1 / row["path"], c.STATE_BYTES)
            c.require(c.sha(raw) == row["sha256"], "state-copy-drift")
            # THE ONE WRITABLE OBJECT. This is the reconstructed working copy
            # the selected runtime is expected to append to; the source
            # generation it was copied FROM is untouched and stays read-only.
            private_file(target, raw, group=True, writable=True)
        outcome["collection_step"] = "restored-inventory"
        restored = c.inventory(home2)
        outcome["collection_step"] = "reconstruction-event"
        event(root, "subset-reconstructed", subset_sha256=c.sha(c.encoded(chosen)), file_count=len(chosen))
        outcome["collection_step"] = "restored-validation"
        files = [r for r in restored if r["type"] == "file"]
        content = lambda items: [{key: row[key] for key in ("path", "type", "size", "sha256")} for row in items]
        c.require(content(files) == content(chosen), "restored-subset-drift")
        outcome.update(inventory=c.public_inventory(rows), promoted=c.public_inventory(chosen), reconstructed=c.public_inventory(restored),
                       expected_initial_artifact_sha256=c.sha(c.INITIAL), stage="second-turn")
        outcome["collection_step"] = None
        save(root / "outcome.json", outcome)
        second = arm(root, nonce, network, 2, session, c.prompt(2), use2, workspace, first["shutdown"])
        outcome["arms"].append(second)
        c.require(second["provider_exit"] == 0 and c.success(second["terminal"]), "second-turn-unsuccessful")
        names = sorted(p.name for p in workspace.iterdir())
        event(root, "workspace-observed", turn=2, entry_count=len(names), expected_set=names == ["continuity.txt", "solution.py"])
        c.require(names == ["continuity.txt", "solution.py"], "correction-artifact")
        corrected = c.artifact_record(c.read_file(workspace / "solution.py"), c.CORRECTED)
        # continuity.txt keeps its EXACT token-plus-one-LF contract; only
        # solution.py gained the second accepted form.
        continuity = c.token_record(c.read_file(workspace / "continuity.txt"), (token + "\n").encode())
        outcome.update(corrected_artifact=corrected, continuity_artifact=continuity)
        save(root / "outcome.json", outcome)
        c.require(corrected["form"] in c.ARTIFACT_FORMS and continuity["form"] == "exact", "correction-artifact")
        models = all(a["terminal"]["actual_model"] == c.ACTUAL_MODEL for a in outcome["arms"])
        outcome.update(outcome="qualified" if models else "not-qualified", stage="complete", token_verified=True,
                       expected_corrected_artifact_sha256=c.sha(c.CORRECTED), model_observed=models,
                       gaps={"G1": "pass" if models else "model-unobserved-or-conflicting", "G2": "pass", "G3": "pass", "G4": "pass", "G5": "pass", "G6": "pass", "G7": "qualification-image-selected", "G8": "not-composed"})
    except BaseException as error:
        outcome["outcome"] = "failed"
        outcome["failure_code"] = c.failure_code(error)
        # The closed triple: which step, what kind of failure, which errno
        # category. Never exception text, type names, paths or arguments.
        detail = {"step": outcome.get("collection_step"), **c.failure_detail(error)}
        outcome["failure_detail"] = detail if c.valid_failure_detail(detail) else {
            "step": None, "category": "other", "errno": "none", "cause": "none"}
    finally:
        outcome.pop("collection_step", None)
        for turn in (1, 2):
            path = root / ("arm-" + str(turn) + ".json")
            if path.exists():
                record = c.decoded(c.read_file(path))
                if record not in outcome["arms"]:
                    outcome["arms"].append(record)
        save(root / "outcome.json", outcome)


def cleanup(nonce):
    """Inspect exact nonce identities; never force-remove an uncertain runtime."""
    results = []
    for turn in (1, 2):
        name = "w177936-" + nonce + "-" + str(turn)
        row = {"turn": turn, "confirmed": False}
        try:
            # A missing container is proved by an exact name-filtered inventory,
            # not inferred from a failed inspect (which could be daemon loss).
            found = engine(["ps", "--all", "--no-trunc", "--filter", "name=^/" + name + "$", "--format", "{{.ID}}"], 8).decode().split()
            c.require(len(found) <= 1, "cleanup-ambiguous")
            if found:
                value = inspect(found[0])
                c.require(value["Image"] == c.IMAGE and value["Config"]["Labels"].get("baton.qualification") == nonce, "cleanup-identity")
                if value["State"]["Running"]:
                    engine(["stop", "--time", "2", found[0]], 8)
                    value = inspect(found[0])
                if value["State"]["Status"] == "created":
                    c.require(value["State"]["Running"] is False and value["State"]["Pid"] == 0, "cleanup-unstarted")
                    row["unstarted"] = True
                else:
                    row["shutdown"] = c.stopped(value, found[0], nonce)
                engine(["rm", found[0]], 8)
            row["confirmed"] = True
            slot = VOLATILE / ("slot-" + str(turn))
            if slot.exists():
                slot.unlink()
        except BaseException:
            pass
        results.append(row)
    if all(r["confirmed"] for r in results):
        try:
            name = "w177936-" + nonce
            ids = engine(["network", "ls", "--no-trunc", "--filter", "name=^" + name + "$", "--format", "{{.ID}}"], 8).decode().split()
            c.require(len(ids) <= 1, "cleanup-network-ambiguous")
            if ids:
                value = inspect(ids[0], "network")
                c.require(value["Name"] == name and value["Labels"].get("baton.qualification") == nonce, "cleanup-network-identity")
                engine(["network", "rm", ids[0]], 8)
            results.append({"network": True, "confirmed": True})
        except BaseException:
            results.append({"network": True, "confirmed": False})
    return results


def run(approved):
    global ENGINE_DEADLINE
    manifest = audit(approved)
    c.require(os.getuid() != 0 and grp.getgrnam("baton-workspace").gr_gid == c.GROUP and c.GROUP in os.getgroups(), "manager-group")
    # Fixed exclusive identity refuses rerun/restart rather than duplicating a
    # user turn. Operator repair/reselection is needed after any partial run.
    # R2, review 2026-09-15T14-36-52Z: EVERY FIXED ROOT IS RESERVED BEFORE ANY
    # CONTROLLER, CREDENTIAL OR ENGINE ADMISSION.
    #
    # The export root used to be created after both live turns, so an existing
    # one refused AFTER the expensive part -- consuming the fixed run identity
    # and failing publication at the one moment the evidence matters. The three
    # roots are one owned identity and are taken together or not at all.
    #
    # EXCLUSIVE AND NEVER REPAIRED. `mkdir` without `exist_ok` is the refusal:
    # a foreign path at any of these names stops the run rather than being
    # chmodded, emptied or written into. A partial reservation is unwound so a
    # refusal leaves no half-taken identity behind, and rerun/restart still
    # needs operator repair rather than being silently permitted.
    EXPORT = export_root()
    reserved = []
    try:
        for place in (ROOT, VOLATILE, EXPORT):
            place.mkdir(mode=0o700)
            reserved.append(place)
    except BaseException:
        for place in reversed(reserved):
            try:
                place.rmdir()
            except OSError:
                pass
        raise
    nonce = uuid.uuid4().hex
    save(ROOT / "identity.json", {"nonce": nonce, "manifest": manifest, "manager_uid": os.getuid(), "image": c.IMAGE})
    began = time.monotonic()
    process = multiprocessing.Process(target=controller, args=(ROOT, nonce))
    process.start()
    interrupted = False
    try:
        process.join(c.ACTIVE_SECONDS)
    except BaseException:
        interrupted = True
    if process.is_alive():
        process.terminate()
        process.join(3)
        if process.is_alive():
            process.kill()
            process.join(3)
        interrupted = True
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    ENGINE_DEADLINE = began + c.OVERALL_SECONDS - 5
    # Independent parent cleanup follows a stopped controller. It knows the
    # nonce/names even if create completed without its answer being journaled.
    ending = cleanup(nonce)
    try:
        outcome = c.decoded(c.read_file(ROOT / "outcome.json", 2 * 1024 * 1024), 2 * 1024 * 1024)
    except BaseException:
        outcome = {"outcome": "failed", "stage": "unrecorded"}
    try:
        lines = c.read_file(ROOT / "events.jsonl", 2 * 1024 * 1024).splitlines()
        c.require(len(lines) <= 128, "event-bound")
        outcome["events"] = [c.decoded(line) for line in lines]
    except BaseException:
        outcome["events"] = []
        outcome["outcome"] = "failed"
    clean = all(x["confirmed"] for x in ending)
    if interrupted or not clean:
        outcome["outcome"] = "failed"
    outcome.update(cleanup=ending, cleanup_confirmed=clean, interrupted=interrupted, elapsed_seconds=time.monotonic() - began,
                   fixture_manifest_sha256=manifest, image=c.IMAGE, cli_version_reference=c.CLI_VERSION, model_argument=c.MODEL,
                   manager_uid=os.getuid(), runtime_user=c.USER, workspace_gid=c.GROUP,
                   omitted_unlisted_flags=["--max-turns"], live_user_invocations_limit=2)
    save(ROOT / "export.json", outcome)
    # ALREADY RESERVED ABOVE, before anything was admitted. See R2.
    exported = EXPORT
    save(exported / "qualification.json", outcome)
    save(exported / "PROVENANCE.json", {"fixture_manifest_sha256": manifest, "qualification_sha256": c.sha(c.encoded(outcome)),
                                        "method": "closed fixture projection; private prompts, transcript/state contents and raw path inventory not exported"})
    print(json.dumps({"outcome": outcome["outcome"], "cleanup_confirmed": clean, "export": str(exported)}))
    return 0 if outcome["outcome"] == "qualified" and clean else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--audit", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--approved-manifest")
    args = parser.parse_args()
    try:
        if args.audit:
            print(json.dumps({"audit": "pass", "manifest_sha256": audit()}))
            return 0
        c.require(args.approved_manifest is not None, "owner-selection-required")
        return run(args.approved_manifest)
    except BaseException:
        print('{"outcome":"refused-before-completion"}')
        return 1


if __name__ == "__main__":
    sys.exit(main())
