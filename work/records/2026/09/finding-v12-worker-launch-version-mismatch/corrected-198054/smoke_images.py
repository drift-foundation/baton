"""Bounded smoke whose CLEANUP and ACCEPTANCE are themselves proved.

W197661 claim198054, correcting `review-2026-09-17T22-39-55Z.md` R3 and R4
under the authority owner seq197881 already selected. `corrected-197975/` is
preserved unchanged; its R1/R2 corrections were accepted and its observations
stand. Nothing here rebuilds an image.

R3 — ABSENCE WAS ASSUMED FROM A FAILURE. The previous `gone()` answered
`absent=true` for EVERY non-zero `docker inspect`, and this engine exits 1 with
`[]` on stdout for a missing object AND for an unreachable daemon; only the
stderr prose tells them apart. So a daemon outage during cleanup would have
been recorded as "removed, confirmed absent". `remove()` ignored the stop and
rm statuses. `held_open` had no enclosing `finally` after `Popen`, so a failed
write, a failed inspection or a failed wait skipped removal entirely. And it
began by removing ANY container holding the name, which is deleting something
whose ownership it had not established.

Here absence is POSITIVE or it is `uncertain`, decided by the manager's own
`_absent_prose` rather than a second copy of that rule; a name already taken is
a REFUSAL rather than something to delete; the container is owned by the ID the
engine reports after launch and every later act names that ID; cleanup is in a
`finally`, records the engine's own answers, and attaches itself to a primary
failure instead of replacing it.

R4 — `complete` ONLY REQUIRED THAT THE RUNS ENDED. It never asserted exit 3
with an empty stdout and a bounded diagnostic for the provider's refusal, exit
2 for the integration's, the supported/validated payloads of either reads run,
or the negative control's state as the ENGINE sees it. Four of the six runs
could have ended in a traceback and the preparation would still have said
complete. `judge` below is now the single acceptance predicate, it is applied
to every run before `complete`, and it is proved by REPLAYING the retained
`corrected-197975` results -- which must pass -- and a set of MUTATIONS of
them, each of which must be refused.

Every regression runs BEFORE any container starts and fails the whole
preparation, because a helper whose failure paths are untested is what the last
two reviews were about.
"""
import copy
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
ACCEPTED = RECORD / "corrected-197975" / "smoke"

CANDIDATES = json.loads((PREPARED / "candidate-images.json").read_text())

ENGINE = "docker"
LAUNCH_TARGET = "/run/baton/launch.json"
SESSION = "session-w197661-smoke"
NAME = "w197661-smoke198054-{what}"

EXIT_BOUND = 60.0
BLOCKING_BOUND = 15.0
ANSWER_BOUND = 15.0
ENGINE_BOUND = 60.0

# The four generations the manager authors and both candidates must read.
SUPPORTED = ["baton.worker-launch/1", "baton.worker-launch/2",
             "baton.worker-launch/3", "baton.worker-launch/4"]
# The members a valid `/3` validates to.
VALIDATED = ["contract", "job_execution", "role", "schema", "session",
             "transport"]


def authoritative(what):
    """The manager's OWN rule, or nothing at all -- for BOTH rules this needs.

    R1 established that the restriction table has no fallback. R3 adds the
    absence sentence to that: a second copy of "what does this engine say when
    an object is missing" is a second thing to keep true, and the manager
    already owns it and already distinguishes a missing object from a daemon
    that cannot be reached.
    """
    sys.path.insert(0, str(REPO / "v12/python/src"))
    from baton_v12.worker_manager import oci

    if what == "restrictions":
        return tuple(oci.RESTRICTIONS)
    if what == "absent_prose":
        return oci._absent_prose
    raise RuntimeError(f"no authoritative source for {what!r}")


# -- the vector, unchanged from the accepted R1 correction --------------------


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


# -- R3: what the engine actually said ---------------------------------------


def looked_at(identity, *, engine, absent_prose):
    """PRESENT, positively ABSENT, or UNCERTAIN. Never inferred from a status.

    R3. `docker inspect` exits 1 with `[]` on stdout both for an object that
    does not exist and for a daemon it could not reach, so a helper reading the
    status alone cannot tell "this container is gone" from "I could not ask".
    Only the engine's own absence sentence, naming THIS exact identity, is
    positive absence -- which is the manager's rule, imported rather than
    copied.
    """
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


def claim_the_name(name, *, engine, absent_prose):
    """A name this run may use, or a REFUSAL.

    R3: the previous helper began by REMOVING whatever held the name. That is
    deleting an object whose ownership it had not established -- an operator's
    container, or another run's. A name already taken is a collision and this
    refuses it.
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
    """Stop, remove and PROVE the exact owned id is gone. Answers evidence.

    Every engine answer is retained. A cleanup that could not be shown to have
    worked is reported as such rather than asserted.
    """
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
    """R3's focused fake-engine cases. No daemon, no container, no network."""
    class Answer:
        def __init__(self, returncode, stdout=b"", stderr=b""):
            self.returncode, self.stdout, self.stderr = returncode, stdout, stderr

    def fake(answer):
        return lambda argv: answer

    name = "w197661-smoke198054-example"
    cases = {
        # The engine's own absence sentence for THIS identity.
        "matching_absence": (Answer(1, b"[]\n",
                                    f"error: no such object: {name}\n".encode()),
                             "absent"),
        # A daemon that could not be reached is NOT absence. This is the exact
        # reproduction the reviewer ran against the previous helper.
        "daemon_unavailable": (Answer(
            1, b"[]\n",
            b"failed to connect to the docker API at unix:///var/run/docker.sock;"
            b" check if the path is correct and if the daemon is running\n"),
            "uncertain"),
        "permission_denied": (Answer(
            1, b"[]\n",
            b"permission denied while trying to connect to the Docker daemon"
            b" socket\n"), "uncertain"),
        # An absence sentence about SOMEBODY ELSE is evidence about them.
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
    # AND THE NAME IS CLAIMED ONLY WHEN IT IS PROVABLY FREE.
    for what, answer, allowed in (
            ("free", cases["matching_absence"][0], True),
            ("taken", cases["present"][0], False),
            ("unknown", cases["daemon_unavailable"][0], False)):
        try:
            claim_the_name(name, engine=fake(answer), absent_prose=absent_prose)
            checks[f"claims_a_{what}_name"] = allowed
        except RuntimeError:
            checks[f"claims_a_{what}_name"] = not allowed
    # AND A CLEANUP THAT CANNOT BE PROVED IS NOT PROVED. The identity is the
    # one the absence sentence NAMES: a first cut of this case freed `abc`
    # against a sentence about `name` and the rule refused it, which is the
    # rule working -- an absence sentence about somebody else is not this
    # container's absence.
    freed = released(name, engine=fake(cases["matching_absence"][0]),
                     absent_prose=absent_prose)
    checks["cleanup_proved_when_absent"] = freed["proved_absent"]
    checks["cleanup_refuses_a_foreign_absence_sentence"] = not released(
        "w197661-smoke198054-other", engine=fake(cases["matching_absence"][0]),
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


# -- R4: the acceptance predicate --------------------------------------------


def judge(runs):
    """What every run must actually SAY, not merely that it ended.

    R4. The previous helper's `complete` required the runs to finish and the
    confinement to look right; four of the six could have ended in a traceback
    and it would still have declared success. This is the single predicate, it
    is applied to the live runs and REPLAYED against the retained accepted
    results and against mutations of them, so a criterion that would accept a
    broken run fails this preparation rather than a later reader.
    """
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

    for name in ("negative_control_invalid_one",
                 "provider_unreadable_generation_held_open",
                 "integration_unreadable_generation_held_open",
                 "provider_reads", "integration_reads", "provider_describe"):
        confined(name, held(name))

    # 1. THE NEGATIVE CONTROL, as the ENGINE saw it and not only as the client
    #    polled it: a container the engine reports Running at the bound, under
    #    the id this run owns.
    one = held("negative_control_invalid_one")
    verdict["negative_control_still_running"] = (
        one.get("still_running_at_bound") is True
        and one.get("returncode") is None
        and (one.get("engine_state") or {}).get("Running") is True)
    verdict["negative_control_held_open"] = \
        one.get("stdin_held_open_until_exit") is True

    # 2. THE CORRECTION ITSELF, at the provider artefact.
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

    # 3. THE RECORDED LIMIT, asserted as the limit it is.
    one = held("integration_unreadable_generation_held_open")
    verdict["integration_five_exits_two"] = one.get("returncode") == 2
    verdict["integration_five_is_silent"] = (
        one.get("stdout_bytes") == 0 and not (one.get("stderr") or "").strip())
    verdict["integration_five_held_open"] = \
        one.get("stdin_held_open_until_exit") is True

    # 4. WHAT EACH IMAGE READS, from its own answer rather than its status.
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

    # 5. AND THE FRAMED CHANNEL, correlated.
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
    """Replay the ACCEPTED results, then mutate them and require refusals.

    R4 asks for exactly this: prove the criterion refuses a broken run rather
    than asserting that it would. The accepted input is
    `corrected-197975/smoke/result.json`, enriched with the engine inspections
    that episode retained beside it -- the negative control's `State.Running`
    lives there rather than in the summary, and it is the fact R4 requires.
    """
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
        place = ACCEPTED / f"{stem}.container.inspect.json"
        record = json.loads(place.read_text())
        runs[name]["engine_state"] = record["State"]
        runs[name]["owned_id"] = record["Id"]
        # The retained summary trimmed its cleanup record to `absent`; the
        # predicate reads `proved_absent`, so the replay states the same fact
        # in the shape this helper writes.
        runs[name]["removal"] = {
            **runs[name]["removal"],
            "proved_absent": runs[name]["removal"].get("absent") is True}

    accepted = judge(runs)
    checks = {"the_accepted_results_pass": all(accepted.values())}
    if not checks["the_accepted_results_pass"]:
        raise RuntimeError(f"the retained accepted results no longer pass the "
                           f"criterion: "
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
    }
    for what, (name, change) in mutations.items():
        checks[f"refuses_{what}"] = not all(mutated(name, change).values())
    # AND A MISSING RUN IS NOT A PASS.
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
                "job_id": "smoke-198054", "attempt_id": "attempt-smoke",
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
    report = {"claim": 198054, "corrects": "review-2026-09-17T22-39-55Z.md",
              "rebuilt": False, "selected": False, "complete": False,
              "images": CANDIDATES, "commands": [], "runs": {},
              "cleanup": {}, "no_model": True}
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

    def checked(argv, seconds=ENGINE_BOUND):
        done = engine(argv, seconds)
        if done.returncode:
            raise RuntimeError(
                f"{argv!r} failed ({done.returncode}): "
                f"{done.stderr.decode('utf-8', 'replace')[:400]}")
        return done.stdout

    def held_open(what, image, place, *, options=(), arguments=(),
                  bound=EXIT_BOUND, expect_running=False, conversation=None):
        """One owned container: claimed name, owned ID, cleanup in a `finally`."""
        name = NAME.format(what=what)
        claim_the_name(name, engine=engine, absent_prose=absent_prose)
        argv = compose(
            options=["--name", name, "--interactive", *options,
                     "--mount", f"type=bind,source={place},"
                                f"target={LAUNCH_TARGET},readonly=true"],
            image=image, arguments=arguments,
            restrictions=report["restrictions"])
        chunks = {"stdout": [], "stderr": []}
        found = {"name": name, "owned_id": None}
        tick = time.monotonic()
        process = subprocess.Popen(argv, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        readers = []
        try:
            def drain(stream, into):
                try:
                    for piece in iter(lambda: stream.read1(4096), b""):
                        into.append(piece)
                except Exception:                          # noqa: BLE001
                    pass

            readers = [threading.Thread(
                target=drain, args=(getattr(process, one), chunks[one]),
                daemon=True) for one in ("stdout", "stderr")]
            for one in readers:
                one.start()
            if conversation is not None:
                process.stdin.write(conversation)
                process.stdin.flush()
                answering = time.monotonic()
                while time.monotonic() - answering < ANSWER_BOUND \
                        and not chunks["stdout"]:
                    time.sleep(0.02)
                process.stdin.close()
            status = None
            while time.monotonic() - tick < bound:
                status = process.poll()
                if status is not None:
                    break
                time.sleep(0.05)
            elapsed = time.monotonic() - tick
            still_running = status is None
            # THE OWNED ID, AND THE ENGINE'S OWN VIEW OF IT. R4: the negative
            # control's claim is about a RUNNING CONTAINER, and only the engine
            # can say that; a client poll says only that a client has not
            # reaped anything.
            seen = looked_at(name, engine=engine, absent_prose=absent_prose)
            if seen["state"] == "present":
                found["owned_id"] = seen["record"]["Id"]
                found["engine_state"] = seen["record"]["State"]
                host = seen["record"]["HostConfig"]
                found["confinement"] = {
                    "NetworkMode": host.get("NetworkMode"),
                    "ReadonlyRootfs": host.get("ReadonlyRootfs"),
                    "CapDrop": host.get("CapDrop"),
                    "SecurityOpt": host.get("SecurityOpt"),
                    "PidsLimit": host.get("PidsLimit"),
                    "Memory": host.get("Memory"),
                    "NanoCpus": host.get("NanoCpus"),
                    "Tmpfs": host.get("Tmpfs"),
                    "User": seen["record"]["Config"].get("User"),
                    "Mounts": [{"Source": one.get("Source"),
                                "Destination": one.get("Destination"),
                                "RW": one.get("RW")}
                               for one in seen["record"].get("Mounts", [])]}
                (output / f"{what}.container.inspect.json").write_text(
                    json.dumps(seen["record"], indent=2, sort_keys=True) + "\n")
            else:
                found["engine_state"] = None
                found["confinement"] = None
                found["inspection"] = seen
            found.update({
                "returncode": status,
                "still_running_at_bound": still_running,
                "observed_seconds": elapsed,
                "stdout_bytes": sum(len(one) for one in chunks["stdout"]),
                "stdout": b"".join(chunks["stdout"]).decode("utf-8",
                                                            "replace")[:600],
                "stderr": b"".join(chunks["stderr"]).decode("utf-8",
                                                            "replace")[:1200],
                "stdin_held_open_until_exit": conversation is None,
                "shape": ("the manager's send-then-close conversation"
                          if conversation is not None
                          else "an owned writer held OPEN until the observed "
                               "exit")})
        finally:
            # R3: THE CLEANUP IS IN A `finally` AND NAMES THE OWNED ID. A
            # failed write, a failed inspection or a failed wait above used to
            # skip removal entirely.
            trouble = None
            try:
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
            except Exception as failed:                    # noqa: BLE001
                trouble = f"the client could not be ended: {failed}"
            freed = released(found["owned_id"] or name, engine=engine,
                             absent_prose=absent_prose)
            if trouble is not None:
                freed["client"] = trouble
            found["removal"] = freed
            report["cleanup"][what] = freed
            report["runs"][what] = found
        if expect_running and not found["still_running_at_bound"]:
            raise RuntimeError(
                f"the negative control {what} ENDED at "
                f"{found['observed_seconds']:.3f}s; the writer was not held "
                f"open, so no held-open claim beside it is established")
        if not expect_running and found["still_running_at_bound"]:
            raise RuntimeError(f"{what} was still running at {bound}s")
        return found

    try:
        report["restrictions"] = authoritative("restrictions")
        report["vector_regression"] = vector_regression(report["restrictions"])
        report["absence_regression"] = absence_regression(absent_prose)
        report["judgement_regression"] = judgement_regression()
        places = launch_documents(work)
        for kind, image in CANDIDATES.items():
            if json.loads(checked([ENGINE, "image", "inspect", image]))[0]["Id"] \
                    != image:
                raise RuntimeError(f"the {kind} candidate is not present")

        held_open("negative_control_invalid_one", CANDIDATES["provider"],
                  places["one_invalid"], bound=BLOCKING_BOUND,
                  expect_running=True)
        for kind, image in CANDIDATES.items():
            held_open(f"{kind}_unreadable_generation_held_open", image,
                      places["five"])
        program = (
            "import json,sys;"
            "sys.path.insert(0,'/opt/baton');"
            "import baton_worker as w;"
            "d=json.load(open('/run/baton/launch.json'));"
            "print(json.dumps({'supported':list(w.SUPPORTED_LAUNCH_SCHEMAS),"
            "'validated':sorted(w.launched(d,'/run/baton/launch.json'))}))")
        for kind, image in CANDIDATES.items():
            held_open(f"{kind}_reads", image, places["three"],
                      options=["--entrypoint", "python3"],
                      arguments=["-c", program])
        request = {"protocol": "baton.worker-entry/1", "session": SESSION,
                   "operation_id": "op-smoke-198054", "operation": "describe"}
        body = json.dumps(request).encode("utf-8")
        spoke = held_open(
            "provider_describe", CANDIDATES["provider"], places["one_valid"],
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

        # R4: THE SAME PREDICATE THE REGRESSION PROVED, applied to what just
        # happened. `complete` is this and nothing looser.
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
                      "containers_proved_absent": all(
                          one["proved_absent"]
                          for one in report["cleanup"].values()),
                      "wall_seconds": report["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
