"""Corrected bounded smoke for the EXISTING candidates. No rebuild, no model.

W197661 claim197975, correcting review-2026-09-17T22-27-16Z.md R1 and R2 under
the authority owner seq197881 already selected. Nothing here builds an image:
the two immutable candidate IDs prepared in claim197885 are reused exactly, so
this repairs the EVIDENCE without minting a second artefact for one deployment.

R1 — THE RESTRICTIONS WERE APPLICATION ARGUMENTS. `prepared-197885`'s helper
appended them to the whole argv its callers had already ended with the IMAGE,
and `docker run [OPTIONS] IMAGE [COMMAND] [ARG...]` means everything after the
image is the container's argv. All six of its smoke vectors put `--cap-drop`
AFTER the image reference, so no network, filesystem, capability, security or
resource restriction was applied by those flags, however the evidence read.
Here the vector is composed from three SEPARATE operands, the restrictions are
proved to precede the image before any container starts, the table is taken
from the manager's own `oci.RESTRICTIONS` with NO fallback, and the exact
container's own `HostConfig` is inspected afterwards -- because a vector
containing the right flags is an argument about a string, and what a container
IS is a fact only the engine can answer.

R2 — `input=b""` IS AN EOF, NOT A HELD-OPEN STDIN. `subprocess.run(input=...)`
and `Popen.communicate()` both CLOSE the writer (`_communicate` closes stdin
whenever `input` is falsy), so the previous "held open" run actually handed the
container an immediate end of input -- which the worker is entitled to answer
by ending. This owns the pipe itself and never calls `communicate`: the writer
stays open until the container's own exit is observed, the streams are drained
by threads, and a NEGATIVE CONTROL proves the mechanism -- an invalid `/1`
document, whose preserved contract is to WAIT for a frame, must still be
running at the observation bound. If it were not, the "held open" claim beside
it would be worthless.

Every container is named and owned: bounded observation, then stop, remove and
a confirmed positive absence from the engine, because killing a Docker client
does not prove its container ended.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
RECORD = HERE.parent
REPO = HERE.parents[5]
PREPARED = RECORD / "prepared-197885"

# THE EXISTING IMMUTABLE CANDIDATES, read from the preparation this corrects
# rather than retyped. Nothing here rebuilds them.
CANDIDATES = json.loads((PREPARED / "candidate-images.json").read_text())

LAUNCH_TARGET = "/run/baton/launch.json"
SESSION = "session-w197661-smoke"
NAME = "w197661-smoke197975-{what}"

# How long a container that is supposed to END gets, and how long a container
# that is supposed to STILL BE RUNNING is watched for. The second is the
# negative control's whole measurement.
EXIT_BOUND = 60.0
BLOCKING_BOUND = 15.0
# How long a CONVERSATION waits for its answer before closing its send side.
ANSWER_BOUND = 15.0


def authoritative_restrictions():
    """The manager's OWN table, or nothing at all.

    R1: the previous helper fell back to a hand-copied tuple on ANY exception,
    so a rename, a moved module or an import error would have produced a smoke
    that silently confined itself with this record's idea of the rules instead
    of the deployment's. There is no fallback here. A preparation that cannot
    read the authoritative restrictions has nothing to prove a container
    against and refuses.
    """
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.worker_manager.oci import RESTRICTIONS

    return tuple(RESTRICTIONS)


def compose(*, options, image, arguments=(), restrictions):
    """`docker run [OPTIONS] IMAGE [ARG...]`, with the shape ENFORCED.

    THREE OPERANDS AND NOT ONE STRING. The defect this corrects was possible
    because one helper took a single flat argv that already ended with the
    image and appended more flags to it. A composer that cannot be handed the
    image in the middle of its options cannot make that mistake.
    """
    if not restrictions:
        raise RuntimeError("a confined vector needs the deployment's own "
                           "restrictions; there is no fallback")
    for one in restrictions:
        if type(one) is not tuple or len(one) != 2 or not one[0].startswith("-"):
            raise RuntimeError(f"a restriction is a (flag, value) pair; "
                               f"this is {one!r}")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise RuntimeError("a smoke runs an immutable image id")
    argv = ["docker", "run", *options]
    for flag, value in restrictions:
        argv.append(flag)
        if value is not None:
            argv.append(value)
    argv.append(image)
    argv.extend(arguments)
    return argv


def vector_regression(restrictions):
    """The focused regression R1 asks for, run BEFORE any container starts.

    It drives the composer rather than describing it, and it fails this
    preparation rather than reporting a finding: a smoke whose vectors are
    wrong proves nothing about an image, and the previous episode's evidence is
    exactly what that looks like.
    """
    image = "sha256:" + "0" * 64
    argv = compose(options=["--name", "x", "--interactive"], image=image,
                   arguments=["-c", "print(1)"], restrictions=restrictions)
    at = argv.index(image)
    checks = {}
    # 1. EVERY RESTRICTION IS AN OPTION, which is the defect itself.
    flags = [one[0] for one in restrictions]
    checks["restrictions_precede_image"] = all(
        index < at for index, token in enumerate(argv) if token in flags)
    # 2. NOTHING BUT THE APPLICATION ARGUMENTS FOLLOWS THE IMAGE.
    checks["only_arguments_follow_image"] = argv[at + 1:] == ["-c", "print(1)"]
    # 3. THE IMAGE IS NAMED EXACTLY ONCE.
    checks["image_named_once"] = argv.count(image) == 1
    # 4. AND IT FAILS CLOSED, both ways.
    for what, table in (("no_restrictions", ()),
                        ("malformed_restrictions", (("--cap-drop",),)),
                        ("not_a_flag", (("cap-drop", "ALL"),))):
        try:
            compose(options=[], image=image, restrictions=table)
            checks[f"refuses_{what}"] = False
        except RuntimeError:
            checks[f"refuses_{what}"] = True
    try:
        compose(options=[], image="baton-w197661-provider:candidate-197885",
                restrictions=restrictions)
        checks["refuses_a_mutable_tag"] = False
    except RuntimeError:
        checks["refuses_a_mutable_tag"] = True
    # 5. AND THE PREVIOUS EPISODE'S SHAPE IS THE ONE THAT FAILS, recorded so
    #    this regression names the defect rather than only the rule.
    superseded = ["docker", "run", "--rm", image, "-c", "print(1)"]
    for flag, value in restrictions:
        superseded.append(flag)
        if value is not None:
            superseded.append(value)
    checks["superseded_shape_puts_restrictions_after_image"] = any(
        index > superseded.index(image)
        for index, token in enumerate(superseded) if token in flags)
    if not all(checks.values()):
        raise RuntimeError(f"the vector regression failed: {checks}")
    return checks


def launch_documents(work):
    """The deliveries this smoke mounts, 0444, composed by the MANAGER's own
    functions so the images are held to a document this record did not invent."""
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.job_manager import execution_limits
    from baton_v12.worker_manager import launch

    held = execution_limits.resolved({}, execution_limits.CURRENT_GENERATION)
    documents = {
        "three": launch.launch_document(
            session=SESSION, contract="smoke", role="implementation",
            transport=None,
            job_execution={
                "job_id": "smoke-197975", "attempt_id": "attempt-smoke",
                "job_input_digest": "sha256:" + "1" * 64,
                "job_policy_digest": "sha256:" + "2" * 64,
                "runtime_input_digest": "sha256:" + "1" * 64,
                "runtime_policy_digest": "sha256:" + "2" * 64,
                "execution_limits": held,
                "execution_limits_digest": launch._digest(held)}),
        # THE GENERATION NEITHER IMAGE READS -- the incident's own shape.
        "five": {"schema": "baton.worker-launch/5", "session": SESSION,
                 "contract": "smoke", "role": "implementation"},
        # THE NEGATIVE CONTROL'S DOCUMENT. A `/1` carrying an unexpected member
        # is correlatable and invalid, and the accepted contract PRESERVES its
        # behaviour: latch, and wait for a frame on stdin. With a writer that
        # is genuinely held open it must therefore still be running at the
        # bound -- which is what makes the held-open runs beside it mean
        # anything.
        # THE VALID `/1` the describe conversation is spoken under.
        "one_valid": launch.launch_document(session=SESSION, contract="smoke",
                                            role="implementation"),
        "one_invalid": {"schema": "baton.worker-launch/1", "session": SESSION,
                        "contract": "smoke", "role": "implementation",
                        "unexpected_member": "from another manager"},
    }
    places = {}
    for name, document in documents.items():
        place = work / f"launch-{name}.json"
        place.write_bytes(json.dumps(document, ensure_ascii=False,
                                     sort_keys=True,
                                     separators=(",", ":")).encode("utf-8"))
        place.chmod(0o444)
        places[name] = str(place)
    return places


def main():
    output = HERE / "smoke"
    output.mkdir(exist_ok=False)
    work = HERE / "smoke-scratch"
    work.mkdir(exist_ok=False)
    report = {"claim": 197975, "corrects": "review-2026-09-17T22-27-16Z.md",
              "rebuilt": False, "selected": False, "complete": False,
              "images": CANDIDATES, "commands": [], "runs": {},
              "no_model": True}
    started = time.monotonic()

    def record(argv, returncode, seconds, **extra):
        report["commands"].append({"argv": argv, "returncode": returncode,
                                   "wall_seconds": seconds, **extra})

    def engine(argv, seconds=60, check=True):
        tick = time.monotonic()
        done = subprocess.run(argv, capture_output=True, timeout=seconds)
        number = len(report["commands"])
        (output / f"command-{number}.stderr").write_bytes(done.stderr)
        record(argv, done.returncode, time.monotonic() - tick)
        if check and done.returncode:
            raise RuntimeError(f"command failed; see command-{number}.stderr: "
                               f"{argv!r}")
        return done.stdout

    def gone(name):
        """POSITIVE ABSENCE, asked of the engine. Killing a client proves
        nothing about the container it started."""
        looked = subprocess.run(["docker", "inspect", name],
                                capture_output=True, timeout=60)
        if looked.returncode == 0:
            return {"absent": False,
                    "state": json.loads(looked.stdout)[0]["State"]}
        return {"absent": True,
                "engine_said": looked.stderr.decode("utf-8", "replace")[:200]}

    def remove(name):
        subprocess.run(["docker", "stop", "--time", "5", name],
                       capture_output=True, timeout=60)
        subprocess.run(["docker", "rm", "--force", name],
                       capture_output=True, timeout=60)
        return gone(name)

    def held_open(what, image, place, *, options=(), arguments=(),
                  bound=EXIT_BOUND, expect_running=False, conversation=None):
        """One container whose stdin pipe is OURS and stays OPEN until it ends.

        No `communicate`, at all: `Popen.communicate()` closes stdin whenever
        its `input` is falsy, which is precisely the defect R2 found. The
        streams are drained by threads so a container that writes more than a
        pipe buffer cannot deadlock against an observer that is not reading.
        """
        name = NAME.format(what=what)
        remove(name)
        argv = compose(
            options=["--name", name, "--interactive", *options,
                     "--mount", f"type=bind,source={place},"
                                f"target={LAUNCH_TARGET},readonly=true"],
            image=image, arguments=arguments,
            restrictions=report["restrictions"])
        tick = time.monotonic()
        process = subprocess.Popen(argv, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        chunks = {"stdout": [], "stderr": []}

        def drain(stream, into):
            # `read1`, NOT `read`. A buffered `read(n)` blocks until it has n
            # bytes or an EOF, so a drain built on it cannot see a bounded
            # answer from a container that is still running -- which is
            # exactly what a conversation has to wait for before it closes
            # its send side.
            try:
                for piece in iter(lambda: stream.read1(4096), b""):
                    into.append(piece)
            except Exception:                              # noqa: BLE001
                pass

        readers = [threading.Thread(target=drain,
                                    args=(getattr(process, name_), chunks[name_]),
                                    daemon=True)
                   for name_ in ("stdout", "stderr")]
        for one in readers:
            one.start()
        # THE WRITER IS NEVER TOUCHED WHILE WE WAIT unless a CONVERSATION was
        # asked for. A conversation is the manager's own shape and is not a
        # held-open claim: `worker_entry.converse` sends its frames and then
        # CLOSES its send side, which is what lets the worker's loop end. It
        # is labelled separately in the evidence for exactly that reason.
        status = None
        if conversation is not None:
            process.stdin.write(conversation)
            process.stdin.flush()
            # The answer has to be back before the send side closes, or this
            # would be measuring a race rather than an answer. Its own bound,
            # so a silent peer spends a fraction of the run's budget here and
            # the exit observation still gets the rest.
            answering = time.monotonic()
            while time.monotonic() - answering < ANSWER_BOUND \
                    and not chunks["stdout"]:
                time.sleep(0.02)
            process.stdin.close()
        while time.monotonic() - tick < bound:
            status = process.poll()
            if status is not None:
                break
            time.sleep(0.05)
        elapsed = time.monotonic() - tick
        still_running = status is None
        inspected = None
        if still_running:
            # THE CONTAINER'S OWN STATE, asked of the engine while it is up:
            # this is the negative control's actual measurement and the
            # confinement proof in one reading.
            looked = subprocess.run(["docker", "inspect", name],
                                    capture_output=True, timeout=60)
            if looked.returncode == 0:
                inspected = json.loads(looked.stdout)[0]
        else:
            looked = subprocess.run(["docker", "inspect", name],
                                    capture_output=True, timeout=60)
            if looked.returncode == 0:
                inspected = json.loads(looked.stdout)[0]
        # OWNED THROUGH THE END, whatever happened: close our writer, end the
        # client, and stop and remove the exact container by name.
        try:
            if not process.stdin.closed:
                process.stdin.close()
        except Exception:                                  # noqa: BLE001
            pass
        if still_running:
            process.kill()
        process.wait(timeout=60)
        for one in readers:
            one.join(timeout=10)
        for pipe in (process.stdout, process.stderr):
            try:
                pipe.close()
            except Exception:                              # noqa: BLE001
                pass
        removal = remove(name)
        record(argv, status, elapsed, container=name,
               still_running_at_bound=still_running)
        if inspected is not None:
            write = output / f"{what}.container.inspect.json"
            write.write_text(json.dumps(inspected, indent=2, sort_keys=True)
                             + "\n")
        found = {
            "returncode": status,
            "still_running_at_bound": still_running,
            "observed_seconds": elapsed,
            "stdout_bytes": sum(len(one) for one in chunks["stdout"]),
            "stdout": b"".join(chunks["stdout"]).decode("utf-8", "replace")[:600],
            "stderr": b"".join(chunks["stderr"]).decode("utf-8", "replace")[:1200],
            "stdin_held_open_until_exit": conversation is None,
            "shape": ("the manager's send-then-close conversation"
                      if conversation is not None
                      else "an owned writer held OPEN until the observed exit"),
            "removal": removal,
            "confinement": None}
        if inspected is not None:
            host = inspected["HostConfig"]
            found["confinement"] = {
                "NetworkMode": host.get("NetworkMode"),
                "ReadonlyRootfs": host.get("ReadonlyRootfs"),
                "CapDrop": host.get("CapDrop"),
                "SecurityOpt": host.get("SecurityOpt"),
                "PidsLimit": host.get("PidsLimit"),
                "Memory": host.get("Memory"),
                "NanoCpus": host.get("NanoCpus"),
                "Tmpfs": host.get("Tmpfs"),
                "User": inspected["Config"].get("User"),
                "Mounts": [{"Source": one.get("Source"),
                            "Destination": one.get("Destination"),
                            "RW": one.get("RW")}
                           for one in inspected.get("Mounts", [])]}
        if expect_running and not still_running:
            raise RuntimeError(
                f"the negative control {what} ENDED at {elapsed:.3f}s "
                f"(status {status}); the writer was not held open, so no "
                f"held-open claim beside it is established")
        if not expect_running and still_running:
            raise RuntimeError(f"{what} was still running at {bound}s")
        return found

    try:
        report["restrictions"] = authoritative_restrictions()
        report["vector_regression"] = vector_regression(report["restrictions"])
        places = launch_documents(work)
        for kind, image in CANDIDATES.items():
            if json.loads(engine(["docker", "image", "inspect", image]))[0]["Id"] \
                    != image:
                raise RuntimeError(f"the {kind} candidate is not present")

        runs = {}
        # 1. THE NEGATIVE CONTROL, FIRST. If a container that is CONTRACTUALLY
        #    obliged to wait for a frame does not wait, this harness cannot
        #    hold a pipe open and nothing after it means anything.
        runs["negative_control_invalid_one"] = held_open(
            "negcontrol", CANDIDATES["provider"], places["one_invalid"],
            bound=BLOCKING_BOUND, expect_running=True)
        # 2. THE INCIDENT'S SHAPE, AT BOTH ARTEFACTS, with the writer open for
        #    the whole run.
        for kind, image in CANDIDATES.items():
            runs[f"{kind}_unreadable_generation_held_open"] = held_open(
                f"{kind}-five", image, places["five"])
        # 3. AND WHAT EACH IMAGE READS, under real confinement this time.
        program = (
            "import json,sys;"
            "sys.path.insert(0,'/opt/baton');"
            "import baton_worker as w;"
            "d=json.load(open('/run/baton/launch.json'));"
            "print(json.dumps({'supported':list(w.SUPPORTED_LAUNCH_SCHEMAS),"
            "'validated':sorted(w.launched(d,'/run/baton/launch.json'))}))")
        for kind, image in CANDIDATES.items():
            # `--entrypoint` IS AN OPTION and belongs before the image, which
            # is the whole of R1: the composer is the only thing that places
            # it, and `-c <program>` is the only thing after the image.
            runs[f"{kind}_reads"] = held_open(
                f"{kind}-reads", image, places["three"],
                options=["--entrypoint", "python3"],
                arguments=["-c", program])
        # 4. AND THE PROVIDER'S REAL ENTRYPOINT ANSWERS THE REAL CHANNEL,
        #    under genuine confinement this time. `describe` dispatches no
        #    provider by contract, so this reaches no model and needs no
        #    credential. The previous episode recorded this answer from an
        #    UNCONFINED container; that observation is superseded by this one.
        request = {"protocol": "baton.worker-entry/1", "session": SESSION,
                   "operation_id": "op-smoke-197975",
                   "operation": "describe"}
        body = json.dumps(request).encode("utf-8")
        spoke = held_open(
            "provider-describe", CANDIDATES["provider"], places["one_valid"],
            conversation=str(len(body)).encode("ascii") + b"\n" + body)
        answers = []
        rest = spoke["stdout"].encode("utf-8", "replace")
        while rest:
            header, _, rest = rest.partition(b"\n")
            if not header.isdigit():
                break
            answers.append(json.loads(rest[:int(header)].decode("utf-8")))
            rest = rest[int(header):]
        spoke["answers"] = answers
        runs["provider_describe"] = spoke
        if spoke["returncode"] != 0 or len(answers) != 1 \
                or not answers[0].get("ok") \
                or answers[0]["operation_id"] != "op-smoke-197975" \
                or answers[0]["answer"]["protocol"] != "baton.worker-entry/1":
            raise RuntimeError("the provider candidate did not answer describe")
        report["runs"] = runs

        # THE CONFINEMENT IS ASSERTED FROM THE ENGINE'S ANSWER, not the argv.
        for what, found in runs.items():
            held = found["confinement"]
            if held is None:
                raise RuntimeError(f"{what} produced no container inspection")
            if held["NetworkMode"] != "none" or not held["ReadonlyRootfs"] \
                    or held["CapDrop"] != ["ALL"] \
                    or "no-new-privileges" not in " ".join(held["SecurityOpt"] or []) \
                    or held["PidsLimit"] != 512 or held["User"] != "65532:65532":
                raise RuntimeError(f"{what} did not run confined: {held}")
            if not found["removal"]["absent"]:
                raise RuntimeError(f"{what} left its container behind")
        report["complete"] = True
    finally:
        report["restrictions"] = [list(one) for one
                                  in report.get("restrictions", ())]
        report["wall_seconds"] = time.monotonic() - started
        (output / "result.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"complete": report["complete"],
                      "rebuilt": False, "selected": False,
                      "wall_seconds": report["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
