"""W81857's real-container acceptance gate, end to end, with no manager alive.

PLAN item 7. Every other piece of evidence for this Work runs against a
recording engine fixture: necessary, and not this. What has to be shown here is
that a FRESHLY BUILT IMMUTABLE IMAGE, started by the production Job Manager
composition, does its work while no manager process exists at all, publishes
its result as durable files, and is picked up by a new incarnation through a
rescan alone.

THE MANAGER IS A SEQUENCE OF SEPARATE PROCESSES, which is the strongest
available form of "the Job Manager process is absent". Every tick is
`job_manager serve --once` in its own interpreter under its own incarnation;
between ticks there is no manager anywhere on the host. The container is left
running across those gaps deliberately, and the gap in the middle is where it
reads its command, runs its provider and publishes its answer.

WHAT THIS DOES NOT PROVE, said here so nobody reads it as more than it is. The
provider in the reference image is `ScriptedAgent`, so this gate proves the
TRANSPORT, the restart boundary, the exactly-once fence and the durable result
-- not that a particular commercial provider was reached. The dogfood image
injects a real provider at the same documented seam and needs a credential this
script deliberately does not require; running it there is an operator act with
its own authorization, and the evidence document below says which image it ran.

USAGE

    PYTHONPATH=v12/python/src:v12/python python3 \\
        work/records/.../evidence/gate-real-container.py \\
        --image sha256:... --home /var/tmp/w81857-gate

It leaves the whole home in place for inspection and prints one JSON evidence
document on stdout.
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve()
DISTRIBUTION = HERE.parents[6] / "v12" / "python"
VECTORS = (HERE.parents[4] / "2026" / "08"
           / "finding-v12-isolated-agent-workers" / "findings"
           / "finding-v12-worker-contract" / "findings"
           / "finding-worker-control-api-manifests" / "evidence"
           / "vectors.json")

sys.path.insert(0, str(DISTRIBUTION / "src"))
sys.path.insert(0, str(DISTRIBUTION))

from baton_v12.authority import Authority                       # noqa: E402
from baton_v12.contracts import digest, digest_of_bytes         # noqa: E402
from baton_v12.worker_manager import exchange, launch, workspaces  # noqa: E402

AUTHORITY_UUID = "8" * 31 + "a"
WORK_ID = f"{AUTHORITY_UUID[:8]}-W81857"
PARTICIPANT = "baton.claude"
ROUTE = "baton.impl"
REVIEW_ROUTE = "baton.rview"
NOW = "2026-09-04T00:00:00.000Z"
PROFILE = "sha256:" + "b" * 64
POLICY = "sha256:" + "2" * 64
RETENTION_POLICY = "sha256:" + "5" * 64
TASK = {"schema": "baton.dogfood-task/1", "task_id": "w81857-gate",
        "instructions": "publish one bounded proposal",
        "source_root": "source",
        "verification": ["python3", "-c", "raise SystemExit(0)"]}


def sealed(document):
    """One manifest with its own digest recomputed over the rest of it."""
    held = {name: value for name, value in document.items()
            if name != "manifest_digest"}
    return {**held, "manifest_digest": digest(held)}


def compose(home, image_digest, gid):
    """Every durable input the production deployment reads, on disk."""
    for name in ("storage", "launch", "credentials", "source", "private"):
        os.makedirs(home / name, exist_ok=True)
    (home / "source" / "worker-task.txt").write_text(
        "publish one bounded proposal\n", encoding="utf-8")

    task = json.dumps(TASK, sort_keys=True).encode("utf-8")
    (home / "task.json").write_bytes(task)

    corpus = json.loads(VECTORS.read_text(encoding="utf-8"))
    by_schema = {one["document"].get("schema"): one["document"]
                 for one in corpus["valid"]}
    given = dict(by_schema["baton.worker-manifest/input"])
    given["work_ref"] = {"authority_uuid": AUTHORITY_UUID, "work_id": WORK_ID}
    given["policy_digest"] = POLICY
    given["runtime_profile_digest"] = PROFILE
    given["worker_image_digest"] = image_digest
    given["assignment_contract"] = "v12-assignment-1"
    given["human_contract"] = {"artifact_id": "w81857-task-1",
                               "media_type": "application/json",
                               "bytes": len(task),
                               "content_digest": digest_of_bytes(task),
                               "locator": "artifact://contracts/w81857-task-1"}
    source = dict(given["sources"][0])
    source["destination"] = "source"
    source["content_manifest"] = workspaces.directory_manifest(
        str(home / "source"))
    given["sources"] = [source]
    given = sealed(given)

    # THE ONE BEARER THIS DEPLOYMENT DELIVERS. The reference image's provider
    # never opens it -- an empty slot set is refused by the credential
    # contract, so a deployment that delivers nothing is not expressible, and
    # this is the smallest honest thing to deliver.
    bearer = home / "private" / "bearer.txt"
    bearer.write_text("not-a-real-credential-w81857\n", encoding="utf-8")
    os.chmod(bearer, 0o600)
    registry = home / "private" / "sources.json"
    registry.write_text(json.dumps(
        {"schema": "baton.user-credential-sources/1",
         "sources": [{"provider": "w81857-gate", "reference": "gate/one",
                      "path": str(bearer)}]}), encoding="utf-8")
    os.chmod(registry, 0o600)

    config = {
        "schema": "baton.v12.single-worker-deployment/3",
        "authority_store": str(home / "authority.sqlite3"),
        "authority_uuid": AUTHORITY_UUID,
        "participant": PARTICIPANT,
        "principal": None,
        "profile_name": "reference",
        "profile_digest": PROFILE,
        "policy_digest": POLICY,
        "adapter_name": "docker-w81857-gate",
        "adapter_digest": "sha256:" + "a" * 64,
        "engine": "docker",
        "image_digest": image_digest,
        "network": "none",
        "workspace_storage": str(home / "storage"),
        "workspace_group": gid,
        "launch_home": str(home / "launch"),
        "credential_home": str(home / "credentials"),
        "credential_sources": str(registry),
        "credential_slots": ["api"],
        "credential_profile": {"api": {"provider": "w81857-gate",
                                       "reference": "gate/one"}},
        "input_source": str(home / "source"),
        "input_manifest": given,
        "task_document": str(home / "task.json"),
        "launch_contract": "v12-assignment-1",
        "launch_role": "implementation",
        "review_route": REVIEW_ROUTE,
        "retention_policy_digest": RETENTION_POLICY,
        "retention_disposition": "retain",
    }

    authority = Authority.create(str(home / "authority.sqlite3"),
                                 authority_uuid=AUTHORITY_UUID,
                                 clock=lambda: NOW)
    try:
        config["principal"] = authority.principal_of(PARTICIPANT)
        authority.create_work(WORK_ID, ROUTE, contract="v12-assignment-1",
                              operation_id="create-w81857-gate")
        authority.add_route_handler(ROUTE, PARTICIPANT)
    finally:
        authority.dispose()

    (home / "config.json").write_text(json.dumps(config, indent=1),
                                      encoding="utf-8")
    (home / "submission.json").write_text(json.dumps({
        "schema": "baton.v12.job-submission/1",
        "submission_id": "sub-w81857-gate",
        "jobs": [{"job_id": "job-gate", "input_digest": given["manifest_digest"],
                  "policy_digest": POLICY,
                  "test_scope": ["v12/python/tests"],
                  "terminal_policy": "report-and-hold",
                  "stages": [{"kind": "implementation", "work_id": WORK_ID,
                              "profile_name": "reference",
                              "profile_digest": PROFILE,
                              "depends_on": []}]}]}), encoding="utf-8")
    return config, given


def manager(home, incarnation, *arguments, config=True):
    """ONE manager process, which exits before this function returns.

    That is the whole point of `--once`: between two of these calls there is
    no Job Manager anywhere on this host, so anything the container does in
    between it does with nobody watching it.
    """
    environment = dict(os.environ)
    environment["PYTHONPATH"] = f"{DISTRIBUTION / 'src'}:{DISTRIBUTION}"
    if config:
        environment["BATON_V12_SINGLE_WORKER_CONFIG"] = str(home
                                                            / "config.json")
    found = subprocess.run(
        [sys.executable, "-m", "tools.job_manager",
         "--store", str(home / "jobs.sqlite3"),
         "--incarnation", incarnation, *arguments],
        cwd=str(DISTRIBUTION), env=environment, capture_output=True,
        timeout=900)
    # WHEN THIS PROCESS CEASED TO EXIST, taken the instant it was reaped. The
    # gate's whole claim is about what happened after a manager exited, so the
    # moment it exited is evidence rather than bookkeeping.
    found.exited_at = time.time()
    return found


def projected(home, incarnation):
    found = manager(home, incarnation, "status",
                    "--control", str(home / "control.sqlite3"), config=False)
    if found.returncode != 0:
        raise SystemExit("status failed: " + found.stderr.decode())
    return json.loads(found.stdout.decode())["jobs"][0]["stages"][0]


def tick(home, incarnation):
    found = manager(home, incarnation, "serve",
                    "--control", str(home / "control.sqlite3"),
                    "--operations", "tools.single_worker:factory",
                    "--interval", "1", "--once")
    return found


def alive(home):
    """Every Job Manager process THIS DEPLOYMENT has, right now.

    SCOPED TO THIS GATE'S OWN STORE, and the first version was not. It matched
    every `tools.job_manager` on the host and duly found one -- the separately
    retained W71917 deployment, a different Job store, a different control
    store and no relationship to this attempt at all. A liveness claim that
    counts somebody else's process is not a claim about this one, so the
    evidence reports both: what this deployment has running, and what else was
    on the host while it ran.
    """
    # READ FROM `/proc` AND MATCHED ON ARGV, not with a shell pattern. `pgrep
    # -f` matches the whole command line of every process, so it matched this
    # very script's own shell -- which mentions the module name in a path --
    # and dragged an unreadable command line into the evidence document. What
    # this needs to recognise is `python -m tools.job_manager`, which is an
    # argv shape.
    lines = []
    for entry in sorted(pathlib.Path("/proc").glob("[0-9]*")):
        try:
            argv = (entry / "cmdline").read_bytes().decode(
                "utf-8", "replace").split("\0")
        except OSError:
            continue
        if "-m" not in argv or "tools.job_manager" not in argv:
            continue
        if argv.index("-m") + 1 != argv.index("tools.job_manager"):
            continue
        lines.append({"pid": entry.name, "argv": [one for one in argv if one]})
    mine = str(home / "jobs.sqlite3")
    return {"this_deployment": [one for one in lines
                                if mine in one["argv"]],
            "other_deployments_on_this_host":
                [one["argv"][:6] for one in lines if mine not in one["argv"]]}


def delivery_of(home, attempt_id):
    session = "session-" + digest(attempt_id)[7:31]
    return launch.adopt(str(home / "launch"), attempt_id=attempt_id,
                        session=session, contract="v12-assignment-1",
                        role="implementation",
                        transport=exchange.EXCHANGE_TRANSPORT,
                        workspace_group=_group(home))


def _group(home):
    from baton_v12.worker_manager import ControlStore
    from baton_v12.worker_manager import configured_workspace_group

    store = ControlStore.open(str(home / "control.sqlite3"),
                              incarnation="gate-read", clock=lambda: NOW)
    try:
        return configured_workspace_group(store)
    finally:
        store.close()


WORKER_IN_IMAGE = "/opt/baton/baton_worker.py"


def worker_digest(engine, image, home):
    """The SHA-256 of the worker file inside the image, measured from outside.

    `create` makes a container without starting it and `cp` copies a path out
    of its filesystem; neither runs a single byte of the image. Hashing with
    something inside the artefact would be asking the artefact whether it is
    the artefact.
    """
    made = subprocess.run([engine, "create", image], capture_output=True)
    if made.returncode != 0:
        raise SystemExit("could not create a container to measure the image: "
                         + made.stderr.decode())
    container = made.stdout.decode().strip()
    place = home / "image-worker.py"
    try:
        copied = subprocess.run(
            [engine, "cp", f"{container}:{WORKER_IN_IMAGE}", str(place)],
            capture_output=True)
        if copied.returncode != 0:
            raise SystemExit(f"could not read {WORKER_IN_IMAGE} out of the "
                             f"image: " + copied.stderr.decode())
        return digest_of_bytes(place.read_bytes())
    finally:
        subprocess.run([engine, "rm", "--force", container],
                       capture_output=True)


# EVERY ACCEPTANCE MEMBER, AND THE GATE FAILS CLOSED ON ALL OF THEM.
#
# Review 2026-09-04T07-00-54Z [P1]: this script computed each of these and then
# printed JSON and exited zero whatever they said, so a run with a surviving
# runtime, a second receipt, an opened channel or an exceptional ending
# succeeded exactly like a passing one. A file named an acceptance gate whose
# exit code does not depend on the acceptance is a file that will one day bless
# the regression it was written to catch.
ACCEPTANCE = (
    ("image_carries_the_reviewed_worker", lambda held: held is True),
    ("provider_turn_began_after_the_commanding_manager_exited",
     lambda held: held is True),
    ("no_channel_was_ever_opened", lambda held: held is True),
    ("one_command", lambda held: held is True),
    ("one_receipt", lambda held: held is True),
    ("no_staging_residue", lambda held: held is True),
    ("output_json_present", lambda held: held is True),
    ("exchange_removed_by_the_ending", lambda held: held is True),
    ("still_removed_after_three_more_incarnations", lambda held: held is True),
    ("final_state", lambda held: held == "completed"),
    ("state_after_three_more_incarnations", lambda held: held == "completed"),
    ("runtime_after_cleanup", lambda held: held == "absent"),
    ("container_exit", lambda held: held.startswith("exited 0 ")),
    ("manager_alive_while_the_worker_worked",
     lambda held: held["this_deployment"] == []),
    ("manager_alive_at_the_end_of_the_gap",
     lambda held: held["this_deployment"] == []),
    ("event_files",
     lambda held: held == ["receipt.json", "state-describe.json",
                           "state-work.json", "terminal.json"]),
)


def unmet(evidence):
    """Every acceptance member this run did not satisfy, with what it said."""
    failed = []
    for name, holds in ACCEPTANCE:
        if name not in evidence:
            failed.append({"member": name, "value": "absent"})
            continue
        try:
            passed = holds(evidence[name])
        except Exception as failure:                       # noqa: BLE001
            failed.append({"member": name,
                           "value": f"unreadable: {type(failure).__name__}"})
            continue
        if not passed:
            failed.append({"member": name, "value": evidence[name]})
    return failed


def main(argv=None):
    parser = argparse.ArgumentParser(prog="gate-real-container")
    parser.add_argument("--image", required=True,
                        help="the freshly built immutable image digest")
    parser.add_argument("--home", required=True)
    parser.add_argument("--engine", default="docker")
    # THE SOURCE BINDING, AS OPERANDS. Review 2026-09-04T07-00-54Z [P1]: this
    # recorded which image ran and nothing tied that image to the bytes review
    # signed off, so it proved that AN immutable image ran rather than that
    # THIS candidate's worker did. Both are required, and the run is refused
    # without them.
    parser.add_argument("--expect-worker-digest", required=True,
                        help="the proposal's candidate digest for "
                             "v12/worker/baton_worker.py")
    parser.add_argument("--expect-proposal", required=True,
                        help="the source-approved proposal digest this run "
                             "is evidence for")
    taken = parser.parse_args(argv)
    home = pathlib.Path(taken.home)
    if home.exists():
        raise SystemExit(f"{home} exists; this gate composes a fresh home so "
                         f"that nothing it proves comes from an earlier run")
    os.makedirs(home)

    evidence = {"image_digest": taken.image, "ticks": [],
                "source_approved_proposal": taken.expect_proposal,
                "expected_worker_digest": taken.expect_worker_digest,
                "manager_alive_while_the_worker_worked": None}
    # THE IMAGE IS BOUND TO THE SOURCE BEFORE ANYTHING RUNS, and the worker
    # bytes are copied OUT of the image rather than hashed by something inside
    # it: `create` plus `cp` executes nothing from the artefact, so the
    # measurement does not depend on trusting the thing being measured.
    evidence["image_worker_digest"] = worker_digest(taken.engine, taken.image,
                                                    home)
    evidence["image_carries_the_reviewed_worker"] = (
        evidence["image_worker_digest"] == taken.expect_worker_digest)
    if not evidence["image_carries_the_reviewed_worker"]:
        print(json.dumps(evidence, indent=1, sort_keys=True))
        raise SystemExit(
            f"the selected image carries {evidence['image_worker_digest']} at "
            f"/opt/baton/baton_worker.py and this proposal's candidate is "
            f"{taken.expect_worker_digest}; a gate that ran a different worker "
            f"is evidence about a different worker")
    compose(home, taken.image, os.getgid())

    submitted = manager(home, "gate-submit", "submit",
                        "--document", str(home / "submission.json"),
                        config=False)
    if submitted.returncode != 0:
        raise SystemExit("submit failed: " + submitted.stderr.decode())

    # -- ticks until a real container is up and has been commanded ----------
    #
    # THE STATUS COMMAND CANNOT SEE THE EXCHANGE, and that is correct rather
    # than a gap in this gate: `job_manager status` is the READ-ONLY surface
    # and is given no deployment factory, so it holds no exchange read and
    # says so by answering `exchange: null`. What this gate needs is the
    # durable files themselves, which is also the thing under test -- so it
    # reads them off the launch delivery exactly as a restarted manager does.
    held = None
    for number in range(1, 8):
        found = tick(home, f"gate-tick-{number}")
        if found.returncode != 0:
            raise SystemExit("tick failed: " + found.stderr.decode())
        stage = projected(home, f"gate-status-{number}")
        view = None
        if stage["attempt_id"] is not None and held is None:
            held = delivery_of(home, stage["attempt_id"])
        if held is not None and held.exchange is not None:
            view = exchange.observation(held.exchange)
        evidence["ticks"].append({
            "incarnation": f"gate-tick-{number}", "status": found.returncode,
            "state": stage["state"],
            "exchange": None if view is None else view["state"],
            "runtime": (stage["runtime"] or {}).get("runtime_id")})
        evidence["ticks"][-1]["exited_at"] = found.exited_at
        if view is not None and view["command"] is not None:
            break
    else:
        raise SystemExit("the pipeline never commanded a worker: "
                         + json.dumps(evidence["ticks"], indent=1))

    attempt_id = stage["attempt_id"]
    runtime_id = stage["runtime"]["runtime_id"]
    evidence["attempt_id"] = attempt_id
    evidence["runtime_id"] = runtime_id
    evidence["commanded_at_tick"] = len(evidence["ticks"])
    evidence["exchange_when_commanded"] = exchange.observation(held.exchange)

    # -- NO MANAGER AT ALL while the container does its work ----------------
    #
    # This is the gate. Every tick above was its own process and every one of
    # them has exited; nothing is watching the container, nothing holds its
    # stdin, and what happens next happens because the command is a FILE.
    evidence["manager_alive_while_the_worker_worked"] = alive(home)
    evidence["gap_opened_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime())
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        view = exchange.observation(held.exchange)
        if view["terminal"] is not None or view["state"] == "unreadable":
            break
        time.sleep(2)
    evidence["exchange_after_the_gap"] = exchange.observation(held.exchange)
    evidence["manager_alive_at_the_end_of_the_gap"] = alive(home)
    evidence["gap_closed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime())
    # THE WORKER'S OWN FILES, WITH THE INSTANT EACH LANDED. The gap above is
    # bounded by two stamps this script took; these are when the container
    # actually wrote, so the ordering is checkable rather than asserted.
    written = {name: os.stat(os.path.join(held.exchange.event_root,
                                          name)).st_mtime
               for name in sorted(os.listdir(held.exchange.event_root))}
    evidence["written_during_the_gap"] = {
        name: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(when))
        for name, when in written.items()}
    # THE ONE DERIVED CLAIM, and it is derived rather than asserted. The worker
    # publishes its receipt BEFORE it dispatches the provider, so a receipt
    # written after the commanding tick's process was reaped means the whole
    # provider turn happened with no manager of this deployment in existence.
    commanding = evidence["ticks"][evidence["commanded_at_tick"] - 1]
    evidence["commanding_tick_exited_at"] = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(commanding["exited_at"]))
    evidence["provider_turn_began_after_the_commanding_manager_exited"] = (
        written.get(exchange.RECEIPT_DOCUMENT, 0) >= commanding["exited_at"])
    # THE RAW EPOCH SECONDS BESIDE THE RENDERED INSTANTS. The comparison above
    # is made on floats and the strings are second-granular, so a reader who
    # only had the strings could not see the margin -- and a margin nobody can
    # see is a claim rather than a measurement.
    evidence["margin_seconds"] = round(
        written.get(exchange.RECEIPT_DOCUMENT, 0) - commanding["exited_at"], 3)
    evidence["provider_turn_seconds"] = round(
        written.get(exchange.TERMINAL_DOCUMENT, 0)
        - written.get(exchange.RECEIPT_DOCUMENT, 0), 3)
    # THE FACT THAT DOES NOT DEPEND ON A CLOCK AT ALL.
    #
    # The margin above is real and it is SMALL, because the reference image's
    # provider answers instantly -- so on its own it is a thin thing to rest
    # "the manager was not driving this" on. What settles that question
    # structurally is that the manager never opened a channel into the
    # container: `worker_entry.converse` would have run `docker exec`, and the
    # engine records every exec it has ever created against a runtime. An
    # empty list is the production composition holding no channel at all,
    # which is the supersession's actual requirement.
    execs = subprocess.run(
        [taken.engine, "inspect", "--format", "{{json .ExecIDs}}", runtime_id],
        capture_output=True)
    evidence["engine_exec_ids"] = (
        execs.stdout.decode().strip() if execs.returncode == 0
        else "unreadable: " + execs.stderr.decode().strip())
    evidence["no_channel_was_ever_opened"] = evidence["engine_exec_ids"] in (
        "null", "[]")
    # AND WHAT BECAME OF PID 1. `serve_exchange` returns 0 once it has
    # published its terminal, so the container is expected to have ENDED here
    # of its own accord -- not to have been stopped, and not to be idling the
    # way the defect this Work corrects left it. `docker top` cannot answer
    # about a process that has exited, so what is recorded is the engine's own
    # account of the exit.
    ended = subprocess.run(
        [taken.engine, "inspect", "--format",
         "{{.State.Status}} {{.State.ExitCode}} {{.State.FinishedAt}}",
         runtime_id], capture_output=True)
    evidence["container_exit"] = (
        ended.stdout.decode().strip() if ended.returncode == 0
        else "unreadable: " + ended.stderr.decode().strip())
    evidence["epochs"] = {"commanding_tick_exited_at":
                          round(commanding["exited_at"], 3),
                          **{name: round(when, 3)
                             for name, when in written.items()}}
    # EXACTLY ONE TURN, COUNTED BEFORE THE ENDING REMOVES THE EVIDENCE. The
    # successful ending authorizes cleanup, and cleanup discards the launch
    # delivery -- exchange namespaces and all -- so the count has to be taken
    # here, while the files the worker wrote are still on disk.
    evidence["command_files"] = sorted(
        one for one in os.listdir(held.exchange.command_root)
        if not one.startswith("."))
    evidence["event_files"] = sorted(os.listdir(held.exchange.event_root))
    evidence["one_command"] = len(evidence["command_files"]) == 1
    evidence["one_receipt"] = evidence["event_files"].count(
        exchange.RECEIPT_DOCUMENT) == 1
    evidence["no_staging_residue"] = not [
        one for one in os.listdir(held.exchange.event_root)
        + os.listdir(held.exchange.command_root) if one.startswith(".")]
    # THE WORKER'S OWN OUTPUT, on the host, written with nobody watching.
    output = (home / "storage" / attempt_id / "workspace" / "output.json")
    evidence["output_json_present"] = output.exists()
    if output.exists():
        evidence["output_json_digest"] = digest_of_bytes(output.read_bytes())
        evidence["output_manifest_digest"] = json.loads(
            output.read_text(encoding="utf-8"))["manifest_digest"]

    # -- a NEW incarnation picks it up by rescanning alone ------------------
    for number in range(8, 16):
        found = tick(home, f"gate-tick-{number}")
        if found.returncode != 0:
            raise SystemExit("tick failed: " + found.stderr.decode())
        stage = projected(home, f"gate-status-{number}")
        evidence["ticks"].append({
            "incarnation": f"gate-tick-{number}", "status": found.returncode,
            "state": stage["state"],
            "exchange": exchange.observation(held.exchange)["state"],
            "runtime": (stage["runtime"] or {}).get("runtime_id")})
        if stage["state"] in ("completed", "exceptional"):
            break

    evidence["final_state"] = stage["state"]
    evidence["artifacts"] = stage["artifacts"]
    # THE RUNTIME IS GONE, because `authorize_cleanup` is the last step of the
    # ending and it removes the container it was authorized to remove.
    engine = subprocess.run(
        [taken.engine, "inspect", "--format", "{{.State.Status}}", runtime_id],
        capture_output=True)
    evidence["runtime_after_cleanup"] = (
        "absent" if engine.returncode != 0
        else engine.stdout.decode().strip())

    # -- and the delivery is gone, because the ending removed it ------------
    #
    # `authorize_cleanup` is the last step and it discards the launch root
    # after proving the runtime absent, so an exchange that still existed here
    # would mean the ending stopped short of its own last act.
    evidence["exchange_removed_by_the_ending"] = not os.path.lexists(
        held.exchange.root)
    # AND ASKING AGAIN CHANGES NOTHING. A settled stage owes no act, so these
    # extra incarnations must start no second turn and must not re-create a
    # delivery the ending removed.
    for number in range(16, 19):
        found = tick(home, f"gate-tick-{number}")
        if found.returncode != 0:
            raise SystemExit("a tick after the ending failed: "
                             + found.stderr.decode())
    evidence["still_removed_after_three_more_incarnations"] = (
        not os.path.lexists(held.exchange.root))
    evidence["state_after_three_more_incarnations"] = projected(
        home, "gate-status-final")["state"]
    evidence["home"] = str(home)
    # THE VERDICT IS PART OF THE EVIDENCE, and it is also the exit code. A
    # reader of the JSON and a reader of `$?` must not be able to disagree.
    evidence["unmet_acceptance"] = unmet(evidence)
    evidence["gate"] = "passed" if not evidence["unmet_acceptance"] \
        else "failed"
    print(json.dumps(evidence, indent=1, sort_keys=True))
    return 0 if evidence["gate"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
