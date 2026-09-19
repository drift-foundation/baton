"""Bounded smoke whose CONTAINER OWNERSHIP is proved at creation.

W197661 claim198115, correcting the remaining R3 ownership defect of
`review-2026-09-17T22-50-56Z.md`, under the authority owner seq197881 already
selected. `prepared-197885/`, `corrected-197975/` and `corrected-198054/` are
preserved unchanged. No image is rebuilt and no product file changes.

THE DEFECT. `corrected-198054`'s `held_open` ended with
`released(found["owned_id"] or name, ...)`, and `owned_id` was only assigned by
an inspection that ran AFTER the observation. So a failure before that point --
the reviewer drove a `BrokenPipeError` on the conversation write -- left
`owned_id` null and the `finally` stopped and removed WHATEVER CURRENTLY HELD
THE NAME. `claim_the_name` is a read-only preflight, not a reservation: another
container can take the name between the look and the launch, and then this run
fails and destroys the winner. Even the ordinary path adopted the ID a name
lookup returned without proving this invocation had created it.

OWNERSHIP IS NOW TAKEN AT CREATION, ATOMICALLY. Every run passes
`--cidfile` at a PRIVATE per-run path that does not exist beforehand; the
engine refuses to start if that file is already there, and writes the container
id into it as part of creating the container. An id read from that file was
therefore created by THIS invocation, which a name lookup can never establish.

AND UNPROVED OWNERSHIP IS NEVER DESTRUCTIVE. If the cidfile is absent,
unreadable or not an id, this run issues NO stop and NO rm at all, records the
exact uncertainty and the name it had asked for, and leaves it for an operator.
Every later inspection names the OWNED ID and is checked to be about it. The
name preflight survives as a convenience and is labelled as one.

The vector, absence and judgement regressions of the accepted episodes are
carried forward unchanged, and an ORCHESTRATION regression is added at the
boundary the defect actually lived on: `held_open` itself, driven with fake
process and engine seams.
"""
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time

HERE = Path(__file__).resolve().parent
RECORD = HERE.parent
REPO = HERE.parents[5]
PREPARED = RECORD / "prepared-197885"
ACCEPTED = RECORD / "corrected-197975" / "smoke"

CANDIDATES = json.loads((PREPARED / "candidate-images.json").read_text())

ENGINE = "docker"
LAUNCH_TARGET = "/run/baton/launch.json"
SESSION = "session-w197661-smoke"
NAME = "w197661-smoke198115-{what}"

EXIT_BOUND = 60.0
BLOCKING_BOUND = 15.0
ANSWER_BOUND = 15.0
ENGINE_BOUND = 60.0
# How long the engine gets to write the container id it is creating.
CREATION_BOUND = 30.0

SUPPORTED = ["baton.worker-launch/1", "baton.worker-launch/2",
             "baton.worker-launch/3", "baton.worker-launch/4"]
VALIDATED = ["contract", "job_execution", "role", "schema", "session",
             "transport"]
_IDENTITY = re.compile(r"[0-9a-f]{64}")


def authoritative(what):
    """The manager's OWN rule, or nothing at all."""
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.worker_manager import oci

    if what == "restrictions":
        return tuple(oci.RESTRICTIONS)
    if what == "absent_prose":
        return oci._absent_prose
    raise RuntimeError(f"no authoritative source for {what!r}")


# -- the vector, from the accepted R1 correction ------------------------------


def compose(*, options, image, arguments=(), restrictions):
    """`docker run [OPTIONS] IMAGE [ARG...]`, with the shape ENFORCED."""
    if not restrictions:
        raise RuntimeError("a confined vector needs the deployment's own "
                           "restrictions; there is no fallback")
    for one in restrictions:
        if type(one) is not tuple or len(one) != 2 or not one[0].startswith("-"):
            raise RuntimeError(f"a restriction is a (flag, value) pair; "
                               f"this is {one!r}")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise RuntimeError("a smoke runs an immutable image id")
    argv = [ENGINE, "run", *options]
    for flag, value in restrictions:
        argv.append(flag)
        if value is not None:
            argv.append(value)
    argv.append(image)
    argv.extend(arguments)
    return argv


def vector_regression(restrictions):
    image = "sha256:" + "0" * 64
    argv = compose(options=["--name", "x", "--interactive"], image=image,
                   arguments=["-c", "print(1)"], restrictions=restrictions)
    at = argv.index(image)
    flags = [one[0] for one in restrictions]
    checks = {
        "restrictions_precede_image": all(
            index < at for index, token in enumerate(argv) if token in flags),
        "only_arguments_follow_image": argv[at + 1:] == ["-c", "print(1)"],
        "image_named_once": argv.count(image) == 1,
    }
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
    superseded = [ENGINE, "run", "--rm", image, "-c", "print(1)"]
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


# -- absence, from the accepted R3 correction ---------------------------------


def looked_at(identity, *, engine, absent_prose):
    """PRESENT, positively ABSENT, or UNCERTAIN. Never inferred from a status."""
    done = engine([ENGINE, "inspect", identity])
    said = done.stderr.decode("utf-8", "replace") if done.stderr else ""
    if done.returncode == 0:
        try:
            record = json.loads(done.stdout.decode("utf-8", "replace"))
        except ValueError:
            return {"state": "uncertain",
                    "why": "the engine's inspection is not JSON",
                    "engine_said": said[:400]}
        if type(record) is not list or len(record) != 1:
            return {"state": "uncertain",
                    "why": f"the engine answered about {len(record)} objects "
                           f"for one exact identity",
                    "engine_said": said[:400]}
        return {"state": "present", "record": record[0]}
    if absent_prose(ENGINE, said, identity):
        return {"state": "absent",
                "why": "the engine's own absence sentence names this identity",
                "engine_said": said[:400]}
    return {"state": "uncertain",
            "why": "the engine refused to inspect and did not say this "
                   "identity is absent",
            "engine_said": said[:400]}


def name_is_free(name, *, engine, absent_prose):
    """A CONVENIENCE, and the review is explicit that it is only that.

    A read-only look is not a reservation: another container can take the name
    between this answer and the launch. It is kept because a collision found
    here is a clearer failure than one the engine reports, and it decides
    NOTHING about what this run may remove -- see `owned_at_creation`.
    """
    found = looked_at(name, engine=engine, absent_prose=absent_prose)
    if found["state"] == "absent":
        return found
    if found["state"] == "present":
        raise RuntimeError(
            f"{name} already names a container this run did not create; "
            f"refusing rather than removing something it does not own")
    raise RuntimeError(f"{name} could not be shown free: {found['why']} "
                       f"({found['engine_said']})")


def released(identity, *, engine, absent_prose):
    """Stop, remove and PROVE the exact OWNED id is gone. Answers evidence."""
    outcome = {"id": identity, "stop": None, "rm": None, "final": None}
    for act in ("stop", "rm"):
        argv = ([ENGINE, "stop", "--time", "5", identity] if act == "stop"
                else [ENGINE, "rm", "--force", identity])
        try:
            done = engine(argv)
            outcome[act] = {
                "returncode": done.returncode,
                "stderr": (done.stderr.decode("utf-8", "replace")[:300]
                           if done.stderr else "")}
        except Exception as failed:                        # noqa: BLE001
            outcome[act] = {"returncode": None,
                            "error": f"{type(failed).__name__}: {failed}"[:300]}
    try:
        outcome["final"] = looked_at(identity, engine=engine,
                                     absent_prose=absent_prose)
        outcome["final"].pop("record", None)
    except Exception as failed:                            # noqa: BLE001
        outcome["final"] = {"state": "uncertain",
                            "why": f"{type(failed).__name__}: {failed}"[:300]}
    outcome["proved_absent"] = outcome["final"]["state"] == "absent"
    return outcome


def absence_regression(absent_prose):
    class Answer:
        def __init__(self, returncode, stdout=b"", stderr=b""):
            self.returncode, self.stdout, self.stderr = returncode, stdout, stderr

    def fake(answer):
        return lambda argv: answer

    name = "w197661-smoke198115-example"
    cases = {
        "matching_absence": (Answer(1, b"[]\n",
                                    f"error: no such object: {name}\n".encode()),
                             "absent"),
        "daemon_unavailable": (Answer(
            1, b"[]\n",
            b"failed to connect to the docker API at unix:///var/run/docker.sock;"
            b" check if the path is correct and if the daemon is running\n"),
            "uncertain"),
        "permission_denied": (Answer(
            1, b"[]\n",
            b"permission denied while trying to connect to the Docker daemon"
            b" socket\n"), "uncertain"),
        "foreign_absence": (Answer(
            1, b"[]\n", b"error: no such object: some-other-container\n"),
            "uncertain"),
        "present": (Answer(0, json.dumps(
            [{"Id": "abc", "State": {"Running": True}}]).encode()), "present"),
        "two_objects_for_one_identity": (Answer(0, b'[{"Id":"a"},{"Id":"b"}]'),
                                         "uncertain"),
        "not_json": (Answer(0, b"not json at all"), "uncertain"),
    }
    checks = {}
    for what, (answer, expected) in cases.items():
        found = looked_at(name, engine=fake(answer), absent_prose=absent_prose)
        checks[f"{what}_is_{expected}"] = found["state"] == expected
    for what, answer, allowed in (
            ("free", cases["matching_absence"][0], True),
            ("taken", cases["present"][0], False),
            ("unknown", cases["daemon_unavailable"][0], False)):
        try:
            name_is_free(name, engine=fake(answer), absent_prose=absent_prose)
            checks[f"claims_a_{what}_name"] = allowed
        except RuntimeError:
            checks[f"claims_a_{what}_name"] = not allowed
    freed = released(name, engine=fake(cases["matching_absence"][0]),
                     absent_prose=absent_prose)
    checks["cleanup_proved_when_absent"] = freed["proved_absent"]
    checks["cleanup_refuses_a_foreign_absence_sentence"] = not released(
        "w197661-smoke198115-other", engine=fake(cases["matching_absence"][0]),
        absent_prose=absent_prose)["proved_absent"]
    unsure = released(name, engine=fake(cases["daemon_unavailable"][0]),
                      absent_prose=absent_prose)
    checks["cleanup_not_claimed_when_uncertain"] = not unsure["proved_absent"]
    checks["cleanup_retains_engine_answers"] = (
        unsure["stop"] is not None and unsure["rm"] is not None)

    def raising(argv):
        raise OSError("the engine could not be run at all")

    thrown = released(name, engine=raising, absent_prose=absent_prose)
    checks["cleanup_survives_an_unrunnable_engine"] = (
        not thrown["proved_absent"] and thrown["stop"]["returncode"] is None)
    if not all(checks.values()):
        raise RuntimeError(f"the absence regression failed: {checks}")
    return checks


# -- R3 (remaining): ownership taken at creation ------------------------------


def owned_at_creation(cidfile):
    """The container id THIS INVOCATION created, or an honest uncertainty.

    `--cidfile` at a path that did not exist is the atomic part: the engine
    refuses to start when the file is already there, and it writes the id as
    part of creating the container. An id read out of a PRIVATE per-run path is
    therefore one this run created -- which is exactly what a name lookup can
    never tell you, and what the previous episode assumed.

    ANYTHING ELSE IS `unproved`, and `unproved` is not a licence to remove
    something by name.
    """
    place = Path(cidfile)
    try:
        if not place.exists():
            return {"state": "unproved", "cidfile": str(place),
                    "why": "the engine wrote no container id, so this run "
                           "cannot show it created a container"}
        held = place.read_text().strip()
    except OSError as failed:
        return {"state": "unproved", "cidfile": str(place),
                "why": f"the container id file could not be read: "
                       f"{type(failed).__name__}"}
    if not _IDENTITY.fullmatch(held):
        return {"state": "unproved", "cidfile": str(place),
                "why": f"the container id file does not hold an id "
                       f"({held[:80]!r})"}
    return {"state": "owned", "id": held, "cidfile": str(place)}


def held_open(what, image, place, *, engine, spawn, absent_prose, restrictions,
              scratch, on_command=None, options=(), arguments=(),
              bound=EXIT_BOUND, expect_running=False, conversation=None,
              sleep=time.sleep, now=time.monotonic, name=None):
    """One container this run PROVABLY created, observed and then released.

    Lifted to module scope with its engine and process seams as operands, so
    the orchestration regression below can drive its failure paths -- which is
    where the ownership defect lived and where the previous episode's
    function-level tests could not reach.
    """
    name = name or NAME.format(what=what)
    cidfile = Path(scratch) / f"{what}.cid"
    found = {"name": name, "owned_id": None, "cidfile": str(cidfile)}
    # THE PREFLIGHT IS A CONVENIENCE. It refuses an obvious collision early and
    # decides nothing about what may be removed.
    found["name_preflight"] = name_is_free(name, engine=engine,
                                           absent_prose=absent_prose)
    argv = compose(
        options=["--name", name, "--cidfile", str(cidfile), "--interactive",
                 *options,
                 "--mount", f"type=bind,source={place},"
                            f"target={LAUNCH_TARGET},readonly=true"],
        image=image, arguments=arguments, restrictions=restrictions)
    chunks = {"stdout": [], "stderr": []}
    tick = now()
    process = None
    readers = []
    owned = {"state": "unproved", "cidfile": str(cidfile),
             "why": "the engine was never started"}
    try:
        process = spawn(argv)

        def drain(stream, into):
            try:
                for piece in iter(lambda: stream.read1(4096), b""):
                    into.append(piece)
            except Exception:                              # noqa: BLE001
                pass

        readers = [threading.Thread(
            target=drain, args=(getattr(process, one), chunks[one]),
            daemon=True) for one in ("stdout", "stderr")]
        for one in readers:
            one.start()
        # OWNERSHIP FIRST, BEFORE ANYTHING THAT CAN FAIL. The conversation
        # write is exactly where the reviewer's reproduction broke, and taking
        # the id before it is what makes the `finally` below able to name the
        # right container.
        while now() - tick < CREATION_BOUND:
            owned = owned_at_creation(cidfile)
            if owned["state"] == "owned" or process.poll() is not None:
                owned = owned_at_creation(cidfile)
                break
            sleep(0.02)
        if owned["state"] == "owned":
            found["owned_id"] = owned["id"]
        if conversation is not None:
            process.stdin.write(conversation)
            process.stdin.flush()
            answering = now()
            while now() - answering < ANSWER_BOUND and not chunks["stdout"]:
                sleep(0.02)
            process.stdin.close()
        status = None
        while now() - tick < bound:
            status = process.poll()
            if status is not None:
                break
            sleep(0.05)
        elapsed = now() - tick
        still_running = status is None
        # EVERY LATER INSPECTION NAMES THE OWNED ID, and is checked to be
        # about it. The previous episode inspected the NAME and adopted
        # whatever came back.
        seen = {"state": "unproved-ownership"}
        if found["owned_id"] is not None:
            seen = looked_at(found["owned_id"], engine=engine,
                             absent_prose=absent_prose)
            if seen["state"] == "present" \
                    and seen["record"].get("Id") != found["owned_id"]:
                seen = {"state": "uncertain",
                        "why": "the engine answered about another container"}
        if seen["state"] == "present":
            record = seen["record"]
            host = record["HostConfig"]
            found["engine_state"] = record["State"]
            found["confinement"] = {
                "NetworkMode": host.get("NetworkMode"),
                "ReadonlyRootfs": host.get("ReadonlyRootfs"),
                "CapDrop": host.get("CapDrop"),
                "SecurityOpt": host.get("SecurityOpt"),
                "PidsLimit": host.get("PidsLimit"),
                "Memory": host.get("Memory"),
                "NanoCpus": host.get("NanoCpus"),
                "Tmpfs": host.get("Tmpfs"),
                "User": record["Config"].get("User"),
                "Mounts": [{"Source": one.get("Source"),
                            "Destination": one.get("Destination"),
                            "RW": one.get("RW")}
                           for one in record.get("Mounts", [])]}
            found["inspection"] = record
        else:
            found["engine_state"] = None
            found["confinement"] = None
            found["inspection_state"] = seen
        found.update({
            "returncode": status,
            "still_running_at_bound": still_running,
            "observed_seconds": elapsed,
            "stdout_bytes": sum(len(one) for one in chunks["stdout"]),
            "stdout": b"".join(chunks["stdout"]).decode("utf-8", "replace")[:600],
            "stderr": b"".join(chunks["stderr"]).decode("utf-8", "replace")[:1200],
            "stdin_held_open_until_exit": conversation is None,
            "shape": ("the manager's send-then-close conversation"
                      if conversation is not None
                      else "an owned writer held OPEN until the observed exit")})
    finally:
        trouble = None
        try:
            if process is not None:
                if process.stdin is not None and not process.stdin.closed:
                    process.stdin.close()
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=30)
                for one in readers:
                    one.join(timeout=10)
                for pipe in (process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()
        except Exception as failed:                        # noqa: BLE001
            trouble = f"the client could not be ended: {failed}"
        found["ownership"] = owned
        if owned["state"] == "owned":
            found["removal"] = released(owned["id"], engine=engine,
                                        absent_prose=absent_prose)
        else:
            # NOTHING IS STOPPED AND NOTHING IS REMOVED. This run cannot show
            # it created a container, and removing one by NAME is how another
            # owner's container gets destroyed by a race this run lost.
            found["removal"] = {
                "proved_absent": False, "acted": False,
                "unproved_ownership": owned,
                "asked_for_name": name,
                "operator": "no stop or rm was issued: ownership was never "
                            "proved, and removing by name could destroy a "
                            "container this run did not create"}
        if trouble is not None:
            found["removal"]["client"] = trouble
        if on_command is not None:
            on_command(found)
    if expect_running and not found["still_running_at_bound"]:
        raise RuntimeError(
            f"the negative control {what} ENDED at "
            f"{found['observed_seconds']:.3f}s; the writer was not held open, "
            f"so no held-open claim beside it is established")
    if not expect_running and found["still_running_at_bound"]:
        raise RuntimeError(f"{what} was still running at {bound}s")
    if owned["state"] != "owned":
        raise RuntimeError(f"{what} could not prove it created a container: "
                           f"{owned['why']}")
    return found


def orchestration_regression(absent_prose, restrictions):
    """The three failure paths the review names, AT `held_open` ITSELF.

    Fake process and engine seams, no daemon, no container, no network. The
    previous episode tested the helper FUNCTIONS and this defect lived in how
    the orchestration used them.
    """
    class Answer:
        def __init__(self, returncode, stdout=b"", stderr=b""):
            self.returncode, self.stdout, self.stderr = returncode, stdout, stderr

    class Pipe:
        def __init__(self, data=b"", raises=None):
            self._data, self._raises, self.closed = data, raises, False

        def read1(self, count):
            out, self._data = self._data[:count], self._data[count:]
            return out

        def write(self, payload):
            if self._raises is not None:
                raise self._raises

        def flush(self):
            pass

        def close(self):
            self.closed = True

    class Process:
        def __init__(self, status=0, stdout=b"", writes=None):
            self.stdin = Pipe(raises=writes)
            self.stdout, self.stderr = Pipe(stdout), Pipe()
            self._status = status

        def poll(self):
            return self._status

        def kill(self):
            pass

        def wait(self, timeout=None):
            return self._status

    stolen = "a" * 64          # the container that WON the name race
    mine = "b" * 64            # the container this run actually created
    checks = {}

    def engine_for(calls, *, inspections):
        def engine(argv):
            calls.append(list(argv))
            if argv[1] == "inspect":
                return inspections(argv[2])
            return Answer(0)
        return engine

    def absence(identity):
        return Answer(1, b"[]\n",
                      f"error: no such object: {identity}\n".encode())

    def present(identity, running=False):
        return Answer(0, json.dumps([{
            "Id": identity, "State": {"Running": running},
            "HostConfig": {"NetworkMode": "none"}, "Config": {},
            "Mounts": []}]).encode())

    def drive(what, *, writes=None, status=0, cidfile_id=None,
              inspections=None, conversation=b"1\n{}"):
        calls = []
        scratch = Path(tempfile.mkdtemp(prefix="w197661-orchestration-"))

        def spawn(argv):
            if cidfile_id is not None:
                (scratch / f"{what}.cid").write_text(cidfile_id + "\n")
            return Process(status=status, writes=writes)

        try:
            found = held_open(
                what, "sha256:" + "0" * 64, str(scratch / "launch.json"),
                engine=engine_for(calls, inspections=inspections),
                spawn=spawn, absent_prose=absent_prose,
                restrictions=restrictions, scratch=scratch,
                conversation=conversation, bound=0.2, sleep=lambda _s: None,
                name=f"w197661-orchestration-{what}")
            failure = None
        except Exception as thrown:                        # noqa: BLE001
            found, failure = None, thrown
        return calls, found, failure

    # 1. THE NAME IS STOLEN AFTER A FREE PREFLIGHT. The launch fails, no id is
    #    ever written, and this run must issue ZERO stop or rm -- the previous
    #    episode removed the winner here.
    calls, found, failure = drive(
        "stolen", writes=BrokenPipeError("lost the name race"),
        cidfile_id=None,
        inspections=lambda identity: absence(identity))
    destructive = [one for one in calls if one[1] in ("stop", "rm")]
    checks["a_stolen_name_issues_no_stop_or_rm"] = destructive == []
    checks["a_stolen_name_refuses_rather_than_reporting_success"] = \
        failure is not None
    checks["a_stolen_name_never_adopts_an_id"] = not any(
        stolen in " ".join(one) for one in calls)

    # 2. A WRITE FAILURE AFTER AN OWNED CREATION cleans up EXACTLY that id.
    calls, found, failure = drive(
        "owned", writes=BrokenPipeError("the write failed after creation"),
        cidfile_id=mine,
        inspections=lambda identity: absence(identity))
    destructive = [one for one in calls if one[1] in ("stop", "rm")]
    checks["an_owned_failure_cleans_up"] = len(destructive) == 2
    checks["an_owned_failure_cleans_only_its_own_id"] = all(
        one[-1] == mine for one in destructive)

    # 3. AN INSPECTION FAILURE AFTER AN OWNED CREATION still cleans its own id
    #    and never adopts another container.
    def refusing(identity):
        # THE PREFLIGHT STILL ANSWERS -- it asks about the NAME, and this case
        # is about an engine that fails AFTER an owned creation. A first cut
        # refused every inspection, so the preflight raised and no container
        # was ever created, which tested nothing.
        if not _IDENTITY.fullmatch(identity):
            return absence(identity)
        return Answer(1, b"[]\n", b"failed to connect to the docker API\n")

    calls, found, failure = drive("unreadable", cidfile_id=mine,
                                  inspections=refusing, conversation=None)
    destructive = [one for one in calls if one[1] in ("stop", "rm")]
    checks["an_unreadable_engine_still_cleans_its_own_id"] = (
        len(destructive) == 2 and all(one[-1] == mine for one in destructive))
    checks["an_unreadable_engine_does_not_claim_cleanup"] = (
        failure is not None or not found["removal"]["proved_absent"])

    # 4. AN UNCERTAIN CREATION NEVER ADOPTS THE CONTAINER HOLDING THE NAME.
    calls, found, failure = drive(
        "uncertain", cidfile_id=None, conversation=None,
        inspections=lambda identity: (present(stolen)
                                      if identity.startswith("w197661")
                                      else absence(identity)))
    # The preflight itself refuses a name that is already taken, which is the
    # first of the two guards; the second is that no id was adopted.
    checks["an_uncertain_creation_adopts_nothing"] = not any(
        stolen in " ".join(one) for one in calls
        if one[1] in ("stop", "rm"))
    checks["an_uncertain_creation_refuses"] = failure is not None

    # 5. AND A CIDFILE THAT IS NOT AN ID IS NOT OWNERSHIP.
    for what, held in (("empty", ""), ("prose", "not an id"),
                       ("short", "abc")):
        place = Path(tempfile.mkdtemp(prefix="w197661-cid-")) / "cid"
        place.write_text(held)
        checks[f"a_{what}_cidfile_is_unproved"] = \
            owned_at_creation(place)["state"] == "unproved"
    place = Path(tempfile.mkdtemp(prefix="w197661-cid-")) / "cid"
    checks["a_missing_cidfile_is_unproved"] = \
        owned_at_creation(place)["state"] == "unproved"
    place.write_text(mine + "\n")
    checks["a_written_cidfile_is_ownership"] = \
        owned_at_creation(place) == {"state": "owned", "id": mine,
                                     "cidfile": str(place)}
    if not all(checks.values()):
        raise RuntimeError(f"the orchestration regression failed: "
                           f"{[k for k, v in checks.items() if not v]}")
    return checks


# -- R4's acceptance predicate, from the accepted episode ---------------------


def judge(runs):
    verdict = {}

    def held(name):
        one = runs.get(name)
        if one is None:
            verdict[f"{name}_present"] = False
        return one or {}

    def confined(name, one):
        seen = one.get("confinement") or {}
        tmpfs = seen.get("Tmpfs") or {}
        verdict[f"{name}_confined"] = (
            seen.get("NetworkMode") == "none"
            and seen.get("ReadonlyRootfs") is True
            and seen.get("CapDrop") == ["ALL"]
            and sorted(seen.get("SecurityOpt") or []) == ["label=disable",
                                                          "no-new-privileges"]
            and seen.get("PidsLimit") == 512
            and seen.get("Memory") == 2147483648
            and seen.get("NanoCpus") == 2000000000
            and "/tmp" in tmpfs and "/dev/shm" in tmpfs
            and seen.get("User") == "65532:65532")
        verdict[f"{name}_cleaned_up"] = bool(
            (one.get("removal") or {}).get("proved_absent"))
        # W197661 claim198115: AND THE CONTAINER WAS THIS RUN'S TO CLEAN UP.
        verdict[f"{name}_ownership_proved_at_creation"] = (
            (one.get("ownership") or {}).get("state") == "owned"
            and (one.get("removal") or {}).get("id")
            == (one.get("ownership") or {}).get("id"))

    for name in ("negative_control_invalid_one",
                 "provider_unreadable_generation_held_open",
                 "integration_unreadable_generation_held_open",
                 "provider_reads", "integration_reads", "provider_describe"):
        confined(name, held(name))

    one = held("negative_control_invalid_one")
    verdict["negative_control_still_running"] = (
        one.get("still_running_at_bound") is True
        and one.get("returncode") is None
        and (one.get("engine_state") or {}).get("Running") is True)
    verdict["negative_control_held_open"] = \
        one.get("stdin_held_open_until_exit") is True

    one = held("provider_unreadable_generation_held_open")
    said = one.get("stderr") or ""
    verdict["provider_five_exits_three"] = one.get("returncode") == 3
    verdict["provider_five_says_nothing_on_stdout"] = \
        one.get("stdout_bytes") == 0
    verdict["provider_five_diagnostic"] = (
        said.startswith("baton-worker: ")
        and "another generation" in said
        and all(version in said for version in SUPPORTED)
        and said.strip().count("\n") == 0)
    verdict["provider_five_held_open"] = \
        one.get("stdin_held_open_until_exit") is True

    one = held("integration_unreadable_generation_held_open")
    verdict["integration_five_exits_two"] = one.get("returncode") == 2
    verdict["integration_five_is_silent"] = (
        one.get("stdout_bytes") == 0 and not (one.get("stderr") or "").strip())
    verdict["integration_five_held_open"] = \
        one.get("stdin_held_open_until_exit") is True

    for kind in ("provider", "integration"):
        one = held(f"{kind}_reads")
        verdict[f"{kind}_reads_exits_zero"] = one.get("returncode") == 0
        try:
            answer = json.loads(one.get("stdout") or "")
        except ValueError:
            answer = {}
        verdict[f"{kind}_reads_the_four_generations"] = \
            answer.get("supported") == SUPPORTED
        verdict[f"{kind}_validates_the_managers_three"] = \
            answer.get("validated") == VALIDATED

    one = held("provider_describe")
    answers = one.get("answers") or []
    verdict["describe_exits_zero"] = one.get("returncode") == 0
    verdict["describe_is_one_correlated_answer"] = (
        len(answers) == 1 and answers[0].get("ok") is True
        and answers[0].get("session") == SESSION
        and str(answers[0].get("operation_id", "")).startswith("op-smoke-")
        and (answers[0].get("answer") or {}).get("protocol")
        == "baton.worker-entry/1")
    verdict["describe_is_a_conversation_not_a_held_open_run"] = \
        one.get("stdin_held_open_until_exit") is False
    return verdict


def judgement_regression():
    """Replay the ACCEPTED results, then mutate them and require refusals."""
    retained = json.loads((ACCEPTED / "result.json").read_text())
    inspections = {
        "negative_control_invalid_one": "negcontrol",
        "provider_unreadable_generation_held_open": "provider-five",
        "integration_unreadable_generation_held_open": "integration-five",
        "provider_reads": "provider-reads",
        "integration_reads": "integration-reads",
        "provider_describe": "provider-describe"}
    runs = copy.deepcopy(retained["runs"])
    for name, stem in inspections.items():
        record = json.loads((ACCEPTED / f"{stem}.container.inspect.json")
                            .read_text())
        runs[name]["engine_state"] = record["State"]
        runs[name]["owned_id"] = record["Id"]
        runs[name]["removal"] = {
            **runs[name]["removal"], "id": record["Id"],
            "proved_absent": runs[name]["removal"].get("absent") is True}
        # The replayed episode proved cleanup but took ownership from a name
        # lookup. Its results are replayed against the CURRENT predicate with
        # that fact stated rather than invented, and the ownership mutation
        # below is what proves the new check bites.
        runs[name]["ownership"] = {"state": "owned", "id": record["Id"]}

    accepted = judge(runs)
    checks = {"the_accepted_results_pass": all(accepted.values())}
    if not checks["the_accepted_results_pass"]:
        raise RuntimeError(f"the retained accepted results no longer pass: "
                           f"{[k for k, v in accepted.items() if not v]}")

    def mutated(name, change):
        copied = copy.deepcopy(runs)
        change(copied[name])
        return judge(copied)

    mutations = {
        "provider_five_exiting_one": (
            "provider_unreadable_generation_held_open",
            lambda one: one.update(returncode=1)),
        "provider_five_writing_to_stdout": (
            "provider_unreadable_generation_held_open",
            lambda one: one.update(stdout_bytes=12)),
        "provider_five_with_no_diagnostic": (
            "provider_unreadable_generation_held_open",
            lambda one: one.update(stderr="")),
        "provider_five_diagnostic_missing_a_version": (
            "provider_unreadable_generation_held_open",
            lambda one: one.update(
                stderr=one["stderr"].replace("baton.worker-launch/4", ""))),
        "provider_five_traceback": (
            "provider_unreadable_generation_held_open",
            lambda one: one.update(
                returncode=1, stderr="Traceback (most recent call last):")),
        "integration_five_exiting_three": (
            "integration_unreadable_generation_held_open",
            lambda one: one.update(returncode=3)),
        "integration_five_speaking": (
            "integration_unreadable_generation_held_open",
            lambda one: one.update(stderr="something")),
        "reads_missing_a_generation": (
            "provider_reads",
            lambda one: one.update(stdout=json.dumps(
                {"supported": SUPPORTED[:3], "validated": VALIDATED}))),
        "reads_not_validating_the_three": (
            "integration_reads",
            lambda one: one.update(stdout=json.dumps(
                {"supported": SUPPORTED, "validated": ["schema"]}))),
        "reads_failing": ("provider_reads",
                          lambda one: one.update(returncode=1, stdout="")),
        "negative_control_that_ended": (
            "negative_control_invalid_one",
            lambda one: one.update(still_running_at_bound=False, returncode=1)),
        "negative_control_the_engine_says_is_not_running": (
            "negative_control_invalid_one",
            lambda one: one.__setitem__("engine_state", {"Running": False})),
        "describe_refused": (
            "provider_describe",
            lambda one: one.__setitem__(
                "answers", [{**one["answers"][0], "ok": False}])),
        "describe_for_another_session": (
            "provider_describe",
            lambda one: one.__setitem__(
                "answers", [{**one["answers"][0], "session": "somebody-else"}])),
        "confinement_without_a_memory_bound": (
            "provider_reads",
            lambda one: one["confinement"].update(Memory=0)),
        "confinement_with_a_network": (
            "provider_describe",
            lambda one: one["confinement"].update(NetworkMode="bridge")),
        "confinement_with_a_writable_root": (
            "integration_reads",
            lambda one: one["confinement"].update(ReadonlyRootfs=False)),
        "confinement_without_the_tmpfs": (
            "provider_reads",
            lambda one: one["confinement"].update(Tmpfs={})),
        "a_container_left_behind": (
            "integration_reads",
            lambda one: one["removal"].update(proved_absent=False)),
        "a_held_open_run_relabelled_a_conversation": (
            "provider_unreadable_generation_held_open",
            lambda one: one.update(stdin_held_open_until_exit=False)),
        # W197661 claim198115: THE OWNERSHIP CHECK ITSELF.
        "ownership_that_was_never_proved": (
            "provider_reads",
            lambda one: one.__setitem__("ownership",
                                        {"state": "unproved"})),
        "cleanup_of_a_container_this_run_did_not_create": (
            "integration_reads",
            lambda one: one["removal"].update(id="c" * 64)),
    }
    for what, (name, change) in mutations.items():
        checks[f"refuses_{what}"] = not all(mutated(name, change).values())
    for name in ("provider_unreadable_generation_held_open",
                 "negative_control_invalid_one"):
        short = {key: one for key, one in runs.items() if key != name}
        checks[f"refuses_a_missing_{name}"] = not all(judge(short).values())
    if not all(checks.values()):
        raise RuntimeError(f"the judgement regression failed: "
                           f"{[k for k, v in checks.items() if not v]}")
    return checks


# -- the live smoke -----------------------------------------------------------


def launch_documents(work):
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.job_manager import execution_limits
    from baton_v12.worker_manager import launch

    held = execution_limits.resolved({}, execution_limits.CURRENT_GENERATION)
    documents = {
        "three": launch.launch_document(
            session=SESSION, contract="smoke", role="implementation",
            transport=None,
            job_execution={
                "job_id": "smoke-198115", "attempt_id": "attempt-smoke",
                "job_input_digest": "sha256:" + "1" * 64,
                "job_policy_digest": "sha256:" + "2" * 64,
                "runtime_input_digest": "sha256:" + "1" * 64,
                "runtime_policy_digest": "sha256:" + "2" * 64,
                "execution_limits": held,
                "execution_limits_digest": launch._digest(held)}),
        "five": {"schema": "baton.worker-launch/5", "session": SESSION,
                 "contract": "smoke", "role": "implementation"},
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
    owned = HERE / "owned-ids"
    owned.mkdir(exist_ok=False)
    report = {"claim": 198115, "corrects": "review-2026-09-17T22-50-56Z.md",
              "rebuilt": False, "selected": False, "complete": False,
              "images": CANDIDATES, "commands": [], "runs": {},
              "ownership": {}, "no_model": True}
    started = time.monotonic()

    def engine(argv, seconds=ENGINE_BOUND):
        tick = time.monotonic()
        done = subprocess.run(argv, capture_output=True, timeout=seconds)
        number = len(report["commands"])
        if done.stderr:
            (output / f"command-{number}.stderr").write_bytes(done.stderr)
        report["commands"].append({"argv": argv, "returncode": done.returncode,
                                   "wall_seconds": time.monotonic() - tick})
        return done

    absent_prose = authoritative("absent_prose")

    def spawn(argv):
        return subprocess.Popen(argv, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    def run(what, image, place, **named):
        found = held_open(what, image, place, engine=engine, spawn=spawn,
                          absent_prose=absent_prose,
                          restrictions=report["restrictions"], scratch=owned,
                          **named)
        record = found.pop("inspection", None)
        if record is not None:
            (output / f"{what}.container.inspect.json").write_text(
                json.dumps(record, indent=2, sort_keys=True) + "\n")
        report["runs"][what] = found
        report["ownership"][what] = found["ownership"]
        return found

    try:
        report["restrictions"] = authoritative("restrictions")
        report["vector_regression"] = vector_regression(report["restrictions"])
        report["absence_regression"] = absence_regression(absent_prose)
        report["orchestration_regression"] = orchestration_regression(
            absent_prose, report["restrictions"])
        report["judgement_regression"] = judgement_regression()
        places = launch_documents(work)
        for kind, image in CANDIDATES.items():
            done = engine([ENGINE, "image", "inspect", image])
            if done.returncode or json.loads(done.stdout)[0]["Id"] != image:
                raise RuntimeError(f"the {kind} candidate is not present")

        run("negative_control_invalid_one", CANDIDATES["provider"],
            places["one_invalid"], bound=BLOCKING_BOUND, expect_running=True)
        for kind, image in CANDIDATES.items():
            run(f"{kind}_unreadable_generation_held_open", image,
                places["five"])
        program = (
            "import json,sys;"
            "sys.path.insert(0,'/opt/baton');"
            "import baton_worker as w;"
            "d=json.load(open('/run/baton/launch.json'));"
            "print(json.dumps({'supported':list(w.SUPPORTED_LAUNCH_SCHEMAS),"
            "'validated':sorted(w.launched(d,'/run/baton/launch.json'))}))")
        for kind, image in CANDIDATES.items():
            run(f"{kind}_reads", image, places["three"],
                options=["--entrypoint", "python3"],
                arguments=["-c", program])
        request = {"protocol": "baton.worker-entry/1", "session": SESSION,
                   "operation_id": "op-smoke-198115", "operation": "describe"}
        body = json.dumps(request).encode("utf-8")
        spoke = run("provider_describe", CANDIDATES["provider"],
                    places["one_valid"],
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

        report["verdict"] = judge(report["runs"])
        refused = [what for what, ok in report["verdict"].items() if not ok]
        if refused:
            raise RuntimeError(f"the smoke did not satisfy: {refused}")
        report["complete"] = True
    finally:
        report["restrictions"] = [list(one) for one
                                  in report.get("restrictions", ())]
        report["wall_seconds"] = time.monotonic() - started
        (output / "result.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"complete": report["complete"], "rebuilt": False,
                      "selected": False,
                      "ownership_proved_at_creation": all(
                          one["state"] == "owned"
                          for one in report["ownership"].values()),
                      "containers_proved_absent": all(
                          one["removal"]["proved_absent"]
                          for one in report["runs"].values()),
                      "wall_seconds": report["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
