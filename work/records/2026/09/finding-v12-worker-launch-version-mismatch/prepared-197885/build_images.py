"""Build a compatible provider/integration pair and smoke them deterministically.

W197661, claim197885, under owner seq197881: "prepare compatible provider and
integration images with immutable base, exact source/build provenance and final
image digests; authorize necessary image builds and bounded deterministic
container smoke checks, no live models."

WHAT IT DOES NOT DO. No model, no credential, no network, no package
installation, no download, no image SELECTION, no deployment, no production
store or runtime touch, no Git operation. Every build is
`--pull=false --no-cache --network none --platform linux/amd64` over an
IMMUTABLE base digest, so the only new bytes are this repository's own reviewed
source.

THE SHAPE IS THE ACCEPTED ONE. `prepared-149053/build_images.py` was
independently reviewed for exactly this act and its base digest is the one
bound there; this is that script's shape with the smoke checks the reported
defect actually needs. Partial outputs and inspection containers are retained
for custody; nothing here retries, deletes or selects an image.

THE SMOKE ANSWERS THE COMPATIBILITY QUESTION, which is the whole reason a
rebuild was selected. The September-12 pair understood `baton.worker-launch/1`
and `/2`; the manager launches `/3` and `/4`. So each image is asked, IN A REAL
CONTAINER: which launch generations does the program you carry read, does it
validate a real `/3` the manager's own composer produced, and does it refuse an
unreadable generation PROMPTLY instead of waiting on a stdin nobody writes to.
The last one is this Work's correction, at the artefact.
"""
import hashlib
import io
import json
from pathlib import Path
import posixpath
import re
import stat
import subprocess
import sys
import tarfile
import time

HERE = Path(__file__).resolve().parent
CONTEXT = HERE / "image-context"
# `work/records/YYYY/MM/<record>/prepared-197885` is six levels down.
REPO = HERE.parents[5]

# THE IMMUTABLE INSTALLATION BASE. The provider runtime 2.1.247, the system
# trust store, python3 and git, already installed and already independently
# accepted: `prepared-149053` bound this exact digest and
# `provider-installation.json` (copied unchanged beside this script) carries
# the binding. Reinstalling any of it here would mint a second unreviewed
# provider installation for one deployment.
BASE = "sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4"

TAG = "baton-w197661-{kind}:candidate-197885"
LAUNCH_TARGET = "/run/baton/launch.json"
SESSION = "session-w197661-smoke"

# Every unconditional restriction the manager applies, copied from
# `oci.RESTRICTIONS` at the time of writing and re-derived below from the
# manager package when it can be imported, so a smoke container is never
# less confined than a production one.
FALLBACK_RESTRICTIONS = (
    ("--cap-drop", "ALL"), ("--security-opt", "no-new-privileges"),
    ("--security-opt", "label=disable"), ("--user", "65532:65532"),
    ("--read-only", None), ("--network", "none"), ("--pids-limit", "512"),
    ("--memory", "2g"), ("--cpus", "2"),
    ("--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m"),
    ("--tmpfs", "/dev/shm:rw,noexec,nosuid,nodev,size=16m"))


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def restrictions():
    try:
        sys.path.insert(0, str(REPO / "v12/python/src"))
        from baton_v12.worker_manager.oci import RESTRICTIONS

        return tuple(RESTRICTIONS)
    except Exception:
        return FALLBACK_RESTRICTIONS


def confined(*flags):
    arguments = list(flags)
    for flag, value in restrictions():
        arguments.append(flag)
        if value is not None:
            arguments.append(value)
    return arguments


def checked_file(data, expected):
    """Inspect exactly one regular archive member without extracting to disk."""
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members = archive.getmembers()
        if len(members) != 1 or not members[0].isfile():
            raise RuntimeError("image copy is not exactly one regular file")
        item = members[0]
        if item.size != expected["bytes"]:
            raise RuntimeError("image file size differs")
        measured = sha(archive.extractfile(item).read())
        if measured != expected["sha256"]:
            raise RuntimeError("image file bytes differ")
        return {"sha256": measured, "bytes": item.size, "mode": item.mode}


def checked_launcher(data):
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members = archive.getmembers()
        if len(members) != 1 or not members[0].issym():
            raise RuntimeError("provider launcher is not one symlink")
        target = posixpath.normpath(
            posixpath.join("/usr/local/bin", members[0].linkname))
        if target != ("/usr/local/lib/node_modules/@anthropic-ai/"
                      "claude-code/bin/claude.exe"):
            raise RuntimeError("provider launcher differs from verified package")
        return {"target": target, "linkname": members[0].linkname}


def launch_documents(work):
    """The three launch deliveries the smoke mounts, written 0444.

    THE `/3` IS THE MANAGER'S OWN, composed by `launch.launch_document` with
    limits resolved by `execution_limits` and sealed by the manager's digest
    function -- not typed here. A hand-written document would prove the image
    accepts something this suite invented.
    """
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.job_manager import execution_limits
    from baton_v12.worker_manager import launch

    held = execution_limits.resolved({}, execution_limits.CURRENT_GENERATION)
    documents = {
        "one": launch.launch_document(session=SESSION, contract="smoke",
                                      role="implementation"),
        "three": launch.launch_document(
            session=SESSION, contract="smoke", role="implementation",
            transport=None,
            job_execution={
                "job_id": "smoke-197885", "attempt_id": "attempt-smoke",
                "job_input_digest": "sha256:" + "1" * 64,
                "job_policy_digest": "sha256:" + "2" * 64,
                "runtime_input_digest": "sha256:" + "1" * 64,
                "runtime_policy_digest": "sha256:" + "2" * 64,
                "execution_limits": held,
                "execution_limits_digest": launch._digest(held)}),
        # A GENERATION AFTER EVERY ONE THIS BUILD AUTHORS. This is the
        # incident's own shape from the container's point of view: a delivery
        # its program cannot read.
        "five": {"schema": "baton.worker-launch/5", "session": SESSION,
                 "contract": "smoke", "role": "implementation"},
    }
    places = {}
    for name, document in documents.items():
        place = work / f"launch-{name}.json"
        place.write_bytes(json.dumps(document, ensure_ascii=False,
                                     sort_keys=True,
                                     separators=(",", ":")).encode("utf-8"))
        place.chmod(0o444)
        places[name] = (str(place), document)
    return places


def framed(document):
    body = json.dumps(document).encode("utf-8")
    return str(len(body)).encode("ascii") + b"\n" + body


def unframed(payload):
    answers = []
    rest = payload
    while rest:
        header, _, rest = rest.partition(b"\n")
        if not header.isdigit():
            break
        length = int(header)
        answers.append(json.loads(rest[:length].decode("utf-8")))
        rest = rest[length:]
    return answers


def main():
    output = HERE / "image-build"
    output.mkdir(exist_ok=False)
    work = HERE / "smoke-scratch"
    work.mkdir(exist_ok=False)
    report = {"claim": 197885, "selected": False, "complete": False,
              "base": BASE, "commands": [], "images": {},
              "content_checks": {}, "inspection_containers": {},
              "launch_smoke": {}, "no_model": True}
    started = time.monotonic()

    def run(argv, seconds=30, stdin=None):
        tick = time.monotonic()
        try:
            done = subprocess.run(argv, capture_output=True, timeout=seconds,
                                  input=stdin)
        except Exception as error:
            report["commands"].append(
                {"argv": argv, "wall_seconds": time.monotonic() - tick,
                 "error_type": type(error).__name__})
            raise
        number = len(report["commands"])
        (output / f"command-{number}.stderr").write_bytes(done.stderr)
        report["commands"].append({"argv": argv,
                                   "returncode": done.returncode,
                                   "wall_seconds": time.monotonic() - tick})
        if done.returncode:
            raise RuntimeError(f"command failed; see retained "
                               f"command-{number}.stderr: {argv!r}")
        return done.stdout

    def ran(argv, seconds=60, stdin=None):
        """A container whose NON-ZERO ending is the answer, not a failure."""
        tick = time.monotonic()
        done = subprocess.run(argv, capture_output=True, timeout=seconds,
                              input=stdin)
        number = len(report["commands"])
        (output / f"command-{number}.stderr").write_bytes(done.stderr)
        report["commands"].append({"argv": argv,
                                   "returncode": done.returncode,
                                   "wall_seconds": time.monotonic() - tick})
        return done

    try:
        if (HERE / "candidate-images.json").exists():
            raise RuntimeError("fresh preparation refuses an existing candidate")
        manifest = json.loads((HERE / "image-context-manifest.json").read_text())
        installation = json.loads((HERE / "provider-installation.json").read_text())
        # THE CONTEXT IS PROVED BEFORE IT IS BUILT, and against the REPOSITORY
        # too: a frozen copy that has drifted from the reviewed tree would
        # build an artefact nobody reviewed.
        source = {"worker": REPO / "v12/worker",
                  "python/src/baton_v12/source_profiles":
                      REPO / "v12/python/src/baton_v12/source_profiles"}
        for name, expected in manifest.items():
            path = CONTEXT / name
            if path.is_symlink() or not path.is_file() \
                    or sha(path.read_bytes()) != expected["sha256"] \
                    or path.stat().st_size != expected["bytes"]:
                raise RuntimeError("image context drift: " + name)
            if name == "Dockerfile.provider":
                continue          # this record's own recipe; it has no twin
            for prefix, root in source.items():
                if name.startswith(prefix + "/"):
                    twin = root / name[len(prefix) + 1:]
                    if sha(twin.read_bytes()) != expected["sha256"]:
                        raise RuntimeError(
                            "frozen context disagrees with the reviewed tree: "
                            + name)
        report["context_manifest"] = manifest
        base = json.loads(run(["docker", "image", "inspect", BASE]))[0]
        if base["Id"] != BASE:
            raise RuntimeError("immutable base unavailable")
        write_json(output / "base.inspect.json", base)

        for kind in ("provider", "integration"):
            recipe = CONTEXT / ("Dockerfile.provider" if kind == "provider"
                                else "worker/Dockerfile.integration")
            command = ["docker", "build", "--pull=false", "--no-cache",
                       "--network", "none", "--platform", "linux/amd64",
                       "--iidfile", str(output / (kind + ".iid")),
                       "--tag", TAG.format(kind=kind), "--file", str(recipe)]
            if kind == "integration":
                command += ["--build-arg", "PROVIDER_BASE=" + BASE]
            command += [str(CONTEXT)]
            (output / (kind + ".build.log")).write_bytes(run(command,
                                                            seconds=300))
            image = (output / (kind + ".iid")).read_text().strip()
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
                raise RuntimeError("build returned no immutable ID")
            facts = json.loads(run(["docker", "image", "inspect", image]))[0]
            entry = ["python3", "/opt/baton/"
                     + ("dogfood_entry.py" if kind == "provider"
                        else "integration_entry.py")]
            if facts["Id"] != image or facts["Os"] != "linux" \
                    or facts["Architecture"] != "amd64" \
                    or facts["Config"]["User"] != "65532:65532" \
                    or facts["Config"]["Entrypoint"] != entry:
                raise RuntimeError(
                    "candidate identity/platform/user/entrypoint differs")
            if facts["RootFS"]["Layers"][:len(base["RootFS"]["Layers"])] \
                    != base["RootFS"]["Layers"]:
                raise RuntimeError(
                    "candidate does not inherit the exact immutable base layers")
            if any(value.startswith(("ANTHROPIC_", "CLAUDE_CODE_OAUTH_TOKEN="))
                   for value in facts["Config"].get("Env", [])):
                raise RuntimeError("candidate carries a credential override")
            write_json(output / (kind + ".inspect.json"), facts)

            # THE PAYLOAD, BYTE BY BYTE, out of a NEVER-STARTED container.
            container = run(["docker", "create",
                             "--name", f"w197661-check-{kind}-197885",
                             "--network", "none", "--read-only",
                             "--entrypoint", "/bin/true", image]).decode().strip()
            if not re.fullmatch(r"[0-9a-f]{64}", container):
                raise RuntimeError("inspection container identity invalid")
            report["inspection_containers"][kind] = container
            checked = {}
            for name, expected in manifest.items():
                if name == "Dockerfile.provider" \
                        or name.endswith("Dockerfile.integration") \
                        or (kind == "provider" and "/integration_" in name) \
                        or (kind == "integration"
                            and name.endswith("/dogfood_entry.py")):
                    continue
                target = ("/opt/baton/source_profiles/"
                          if "/source_profiles/" in name
                          else "/opt/baton/") + Path(name).name
                checked[target] = checked_file(
                    run(["docker", "cp", container + ":" + target, "-"]),
                    expected)
            for target, expected in installation["files"].items():
                checked[target] = checked_file(
                    run(["docker", "cp", container + ":" + target, "-"]),
                    expected)
            checked["/usr/local/bin/claude"] = checked_launcher(
                run(["docker", "cp", container + ":/usr/local/bin/claude", "-"]))
            state = json.loads(run(["docker", "inspect", container]))[0]
            if state["Image"] != image \
                    or state["State"]["Status"] != "created" \
                    or state["State"]["Running"] \
                    or not state["HostConfig"]["ReadonlyRootfs"] \
                    or state["HostConfig"]["NetworkMode"] != "none" \
                    or state["Mounts"]:
                raise RuntimeError("inspection container started or lost isolation")
            write_json(output / (kind + ".container.inspect.json"), state)
            report["images"][kind] = image
            report["content_checks"][kind] = checked

        # -- the bounded deterministic launch smoke ------------------------
        places = launch_documents(work)
        smoke = {}
        for kind, image in report["images"].items():
            found = {}
            # 1. WHICH GENERATIONS THE CARRIED PROGRAM READS, and whether it
            #    validates the manager's own `/3`. One container, no
            #    entrypoint, no provider, no network, no mounts but the
            #    document itself.
            program = (
                "import json,sys;"
                "sys.path.insert(0,'/opt/baton');"
                "import baton_worker as w;"
                "d=json.load(open('/run/baton/launch.json'));"
                "print(json.dumps({'supported':list(w.SUPPORTED_LAUNCH_SCHEMAS),"
                "'validated':sorted(w.launched(d,'/run/baton/launch.json'))}))")
            answer = run(confined(
                "docker", "run", "--rm",
                "--mount", f"type=bind,source={places['three'][0]},"
                           f"target={LAUNCH_TARGET},readonly=true",
                "--entrypoint", "python3", image, "-c", program), seconds=120)
            found["reads"] = json.loads(answer.decode("utf-8"))
            if found["reads"]["supported"] != ["baton.worker-launch/1",
                                               "baton.worker-launch/2",
                                               "baton.worker-launch/3",
                                               "baton.worker-launch/4"]:
                raise RuntimeError(f"{kind} does not read the manager's launch "
                                   f"generations")
            if "job_execution" not in found["reads"]["validated"]:
                raise RuntimeError(f"{kind} did not validate the manager's /3")
            # 2. THE CORRECTION, AT THE ARTEFACT. A generation this image
            #    cannot read, with stdin at /dev/null held open by nothing:
            #    it must END and it must SAY WHY.
            refused = ran(confined(
                "docker", "run", "--rm",
                "--mount", f"type=bind,source={places['five'][0]},"
                           f"target={LAUNCH_TARGET},readonly=true",
                image), seconds=120)
            found["unreadable_generation"] = {
                "returncode": refused.returncode,
                "stdout": refused.stdout.decode("utf-8", "replace")[:400],
                "stderr": refused.stderr.decode("utf-8", "replace")[:1200]}
            if refused.returncode == 0:
                raise RuntimeError(f"{kind} accepted a generation it cannot read")
            smoke[kind] = found

        # 3. THE PROVIDER IMAGE'S REAL ENTRYPOINT ANSWERS THE REAL CHANNEL.
        #    One `describe` over the framed transport, which dispatches NO
        #    provider by contract -- so this reaches no model and needs no
        #    credential.
        request = {"protocol": "baton.worker-entry/1", "session": SESSION,
                   "operation_id": "op-smoke-1", "operation": "describe"}
        spoke = ran(confined(
            "docker", "run", "--rm", "--interactive",
            "--mount", f"type=bind,source={places['one'][0]},"
                       f"target={LAUNCH_TARGET},readonly=true",
            report["images"]["provider"]), seconds=120, stdin=framed(request))
        answers = unframed(spoke.stdout)
        smoke["provider"]["describe"] = {
            "returncode": spoke.returncode, "answers": answers}
        if spoke.returncode != 0 or len(answers) != 1 \
                or not answers[0].get("ok") \
                or answers[0]["answer"]["protocol"] != "baton.worker-entry/1" \
                or answers[0]["operation_id"] != "op-smoke-1":
            raise RuntimeError("the provider image did not answer describe")
        # 4. AND THE PROVIDER IMAGE'S REAL ENTRYPOINT REFUSES A `/5` WITHOUT
        #    READING A STDIN NOBODY WRITES TO: the pipe is open and empty for
        #    the whole run, exactly as the incident's was.
        held = ran(confined(
            "docker", "run", "--rm", "--interactive",
            "--mount", f"type=bind,source={places['five'][0]},"
                       f"target={LAUNCH_TARGET},readonly=true",
            report["images"]["provider"]), seconds=120, stdin=b"")
        said = held.stderr.decode("utf-8", "replace")
        smoke["provider"]["held_open_stdin"] = {
            "returncode": held.returncode, "stdout_bytes": len(held.stdout),
            "stderr": said[:1200]}
        if held.returncode != 3 or held.stdout \
                or "baton-worker: " not in said \
                or "another generation" not in said:
            raise RuntimeError(
                "the provider image did not refuse promptly on stderr")
        report["launch_smoke"] = smoke
        report["complete"] = True
        write_json(HERE / "candidate-images.json", report["images"])
    finally:
        report["wall_seconds"] = time.monotonic() - started
        write_json(output / "result.json", report)
    print(json.dumps({"images": report["images"], "selected": False,
                      "wall_seconds": report["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
