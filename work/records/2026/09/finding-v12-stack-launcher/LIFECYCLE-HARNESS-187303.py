"""W183883 — the installed-lifecycle harness, with OWNERSHIP established first.

Supersedes LIFECYCLE-HARNESS-187223.py. That one checked its outcomes and
cleaned up on every path, and review 2026-09-16T14-54-21Z found the remaining
hole: it decided what it owned from the text `start` happened to print.

  * `start` on an ALREADY-RUNNING instance prints no "started: … pid N" line,
    and a start that TIMED OUT prints nothing at all. Either left the pid map
    empty -- and an empty pid map read as "nothing of ours is alive", so the
    harness went on to corrupt a library while somebody else's manager was
    serving, and then claimed cleanup ownership over processes it had not
    started.
  * `alive()` turned a PermissionError into "dead". Not being allowed to look
    is not evidence of absence.
  * the repeated-bootstrap step recorded `selector_unchanged: false` and still
    exited 0: the preservation it exists to demonstrate was never asserted.

WHAT IT DOES NOW:

  * OWNERSHIP BEFORE ANYTHING. Each instance is asked for `status` first --
    the deployment's OWN four-state reader (absent / running / gone / unknown),
    not a process manager invented here. Anything but `absent` for every
    process means this run does not own that instance: it refuses, stops
    nothing, and exits non-zero.
  * IDENTITY IS COMPLETE OR IT IS UNKNOWN. A start must report a pid for every
    process the deployment runs, and `status` must then agree with those pids.
    Anything less is `unknown`, and unknown is never treated as absence.
  * NO DESTRUCTIVE STEP UNDER UNKNOWN IDENTITY. The runtime-mismatch case is
    not re-run here at all: `LIFECYCLE-187142.json` and the packaging suite
    already hold it against a real bundle, and corrupting a library is not
    something to do on the strength of a pid map that might be empty.
  * EVERY EXPECTATION IS ASSERTED, including the selector preservation the
    repeated bootstrap exists to show.

It submits no Job, contacts no provider, runs no engine, reads no owner
credential registry, and performs no version-control operation.

    python3 LIFECYCLE-HARNESS-187303.py > LIFECYCLE-187303.json
    W183883_INJECT=<boundary> python3 LIFECYCLE-HARNESS-187303.py

Boundaries: already-running, start-timeout, start-silent, alive-unknown,
after-starts, timeout-status, stop-nonzero, cleanup-raises, selector-changed.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import time

LIVE = pathlib.Path(os.environ.get("W183883_LIVE",
                                   "/var/tmp/w183883-live-186890"))
A = LIVE / "deployment"
B = LIVE / "deployment-b"
DISTRO = os.environ.get("W183883_DISTRO",
                        "/home/sl/src/baton/v12/python/build/out/distro")
INJECT = os.environ.get("W183883_INJECT")

ENVIRONMENT = {"HOME": "/root", "PATH": "/usr/bin:/bin"}
CWD = "/"
TIMEOUT = 300
STOP_ATTEMPTS = 2
MONITOR_TICKS = ("--interval", "0.2", "--ticks", "2")
# What the deployment's own `status` prints, one line per process.
PROCESSES = ("manager", "publisher")
STARTED = re.compile(r"^started: (\w+) pid (\d+)$")
REPORTED = re.compile(r"^(\w+)\s+(absent|running|gone|unknown)(?: pid (\d+))?")

ran = []
undo = []
owned = {}              # instance -> {process: pid}, only when COMPLETE
claimed = []            # instances this run is entitled to stop
failures = []


def digest(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


def note(step, expected, got, detail=None):
    failures.append({"step": step, "expected": expected, "got": got,
                     "detail": detail})


def run(argv, *, expect=0, what=None, timeout=TIMEOUT):
    what = what or " ".join(str(one) for one in argv[1:3])
    began = time.monotonic()
    try:
        if INJECT == "timeout-status" and "status" in [str(one) for one in argv]:
            raise subprocess.TimeoutExpired(argv, timeout)
        if INJECT == "start-timeout" and "start" in [str(one) for one in argv]:
            raise subprocess.TimeoutExpired(argv, timeout)
        done = subprocess.run([str(one) for one in argv], capture_output=True,
                              text=True, timeout=timeout, cwd=CWD,
                              env=dict(ENVIRONMENT))
        answer = {"exit": done.returncode,
                  "stdout": done.stdout.strip().splitlines(),
                  "stderr": done.stderr.strip().splitlines()[-3:]}
        if INJECT == "start-silent" and "start" in [str(one) for one in argv]:
            answer["stdout"] = ["already running: manager", "already running: publisher"]
    except subprocess.TimeoutExpired:
        answer = {"exit": None, "timed_out": True, "stdout": [], "stderr": []}
    answer.update({"argv": [str(one) for one in argv], "cwd": CWD,
                   "env": dict(ENVIRONMENT), "timeout_seconds": timeout,
                   "what": what, "expected_exit": expect,
                   "seconds": round(time.monotonic() - began, 3)})
    if expect is not None and answer["exit"] != expect:
        answer["unexpected"] = True
        note(what, "exit " + str(expect),
             "timed out" if answer.get("timed_out") else
             "exit " + str(answer["exit"]), answer["stderr"])
    ran.append(answer)
    return answer


def stack(root, verb, *operands, expect=0, what=None):
    return run([root / "distro" / "baton-v12-stack", verb, "--instance",
                root / "instance.json", *operands],
               expect=expect, what=what or (verb + " " + root.name))


def reported(root, *, what=None):
    """What the deployment's OWN reader says about its processes.

    Four states, and they are the product's: `absent` is a positive absence,
    `unknown` means it looked and could not tell. Nothing here re-implements
    that; it is read.
    """
    said = stack(root, "status", expect=None, what=what or ("status " + root.name))
    if said.get("timed_out") or said["exit"] != 0:
        return {name: {"state": "unknown", "pid": None} for name in PROCESSES}
    states = {}
    for line in said["stdout"]:
        matched = REPORTED.match(line.strip())
        if matched and matched.group(1) in PROCESSES:
            states[matched.group(1)] = {
                "state": matched.group(2),
                "pid": int(matched.group(3)) if matched.group(3) else None}
    for name in PROCESSES:
        states.setdefault(name, {"state": "unknown", "pid": None})
    if INJECT == "alive-unknown":
        states = {name: {"state": "unknown", "pid": None} for name in PROCESSES}
    return states


def unclaimed(root):
    """Is this instance ours to start -- every process POSITIVELY absent?"""
    states = reported(root, what="ownership preflight " + root.name)
    if INJECT == "already-running":
        states = {"manager": {"state": "running", "pid": 999999},
                  "publisher": {"state": "running", "pid": 999998}}
    unexpected = {name: one for name, one in states.items()
                  if one["state"] != "absent"}
    return (not unexpected), states, unexpected


def claim(root):
    """Start one instance, and own it ONLY if the identity is complete."""
    ok, before, unexpected = unclaimed(root)
    if not ok:
        note("ownership preflight " + root.name, "every process absent",
             json.dumps(unexpected),
             "this run does not own that instance; nothing was started and "
             "nothing of somebody else's will be stopped")
        return {"refused": True, "before": before}
    claimed.append(root)
    said = stack(root, "start", what="start " + root.name)
    pids = {}
    for line in said["stdout"]:
        matched = STARTED.match(line.strip())
        if matched:
            pids[matched.group(1)] = int(matched.group(2))
    after = reported(root, what="ownership confirmation " + root.name)
    agreed = all(after.get(name, {}).get("state") == "running"
                 and after[name]["pid"] == pids.get(name)
                 for name in PROCESSES)
    if set(pids) == set(PROCESSES) and agreed:
        owned[str(root)] = pids
        said["owned_pids"] = pids
    else:
        # PARTIAL IS UNKNOWN, NOT EMPTY. An already-running start prints no
        # pid line and a timed-out one prints nothing; reading either as "we
        # own nothing that is alive" is how a library came to be corrupted
        # under a serving manager.
        said["identity"] = "unknown"
        said["reported_after"] = after
        note("ownership of " + root.name, "a pid for " + " and ".join(PROCESSES),
             json.dumps(pids), "identity is UNKNOWN, not absent")
    return said


def restoring(place, what):
    place = pathlib.Path(place)
    held = place.read_bytes()

    def undoing():
        if INJECT == "cleanup-raises" and what.endswith("selector"):
            raise OSError("injected cleanup failure for " + what)
        place.write_bytes(held)

    undo.append((what, undoing))
    return held


def inject(step):
    if INJECT == step:
        raise RuntimeError("injected failure at " + step)


def survivors():
    """Anything this run started that is not POSITIVELY absent, by the
    deployment's own reader."""
    left = {}
    for root in claimed:
        states = reported(root, what="survivor check " + root.name)
        for name, one in states.items():
            if one["state"] != "absent":
                left["%s/%s" % (root.name, name)] = one
    return left


def cleanup():
    answers = {"undone": [], "stops": [], "raised": [],
               "claimed": [str(one) for one in claimed],
               "owned_pids": {name: pids for name, pids in owned.items()}}
    for what, undoing in reversed(undo):
        try:
            undoing()
            answers["undone"].append({"what": what, "ok": True})
        except BaseException as failure:                     # noqa: BLE001
            answers["undone"].append({"what": what, "ok": False,
                                      "raised": repr(failure)})
            answers["raised"].append({"action": "undo " + what,
                                      "raised": repr(failure)})
    # ONLY WHAT THIS RUN CLAIMED. An instance it refused to claim is somebody
    # else's and is not stopped, whatever state it is in.
    for root in claimed:
        for attempt in range(1, STOP_ATTEMPTS + 1):
            try:
                said = stack(root, "stop", expect=None,
                             what="cleanup stop " + root.name)
                if INJECT == "stop-nonzero":
                    said = dict(said, exit=1)
                answers["stops"].append({"instance": str(root),
                                         "attempt": attempt,
                                         "exit": said["exit"],
                                         "stdout": said["stdout"]})
                if said["exit"] == 0:
                    break
            except BaseException as failure:                 # noqa: BLE001
                answers["stops"].append({"instance": str(root),
                                         "attempt": attempt, "exit": None,
                                         "raised": repr(failure)})
                answers["raised"].append({"action": "stop " + root.name,
                                          "raised": repr(failure)})
    left = survivors()
    answers["still_not_absent"] = left
    answers["nothing_removed"] = ("the destinations and the fixture roots are "
                                  "retained; only this run's own changes are "
                                  "undone, and only instances it claimed are "
                                  "stopped")
    answers["resolved"] = (not left and not answers["raised"]
                           and all(one["exit"] == 0 for one in answers["stops"])
                           and all(one["ok"] for one in answers["undone"]))
    return answers


def fixtures():
    held = {}
    for name in ("inputs.json", "inputs-b.json", "credential-sources.json",
                 "fixture-credential.txt"):
        place = LIVE / name
        if place.exists():
            held[str(place)] = {"sha256": digest(place),
                                "bytes": place.stat().st_size,
                                "mode": oct(place.stat().st_mode & 0o777)}
    return {"digests": held,
            "what_they_are": "an inputs document per instance, composed from "
                             "the accepted stage fixtures; a FIXTURE "
                             "credential registry naming a fixture bearer "
                             "file. No owner registry was read and no provider "
                             "was contacted.",
            "retained_fixture_material":
                (LIVE / "fixture-root.txt").read_text().split()
                if (LIVE / "fixture-root.txt").exists() else []}


def lifecycle(record):
    told = run([A / "distro" / "baton-v12-stack", "identity"], what="identity")
    record["identity"] = json.loads("\n".join(told["stdout"]) or "{}")
    record["claim_a"] = claim(A)
    record["claim_b"] = claim(B)
    inject("after-starts")
    if not owned:
        # NOTHING IS OWNED, SO NOTHING IS DEMONSTRATED. The rest of this run
        # would be reading somebody else's deployment.
        record["stopped_early"] = ("no instance was claimed with a complete "
                                   "identity; the run does not continue over "
                                   "processes it does not own")
        return record
    record["a_status"] = stack(A, "status")
    record["b_status"] = stack(B, "status")
    record["isolation"] = {
        "a_stores": sorted(os.listdir(A / "db")),
        "b_stores": sorted(os.listdir(B / "db")),
        "distinct_state_roots": [str(A / "state"), str(B / "state")],
        "distinct_stores": [str(A / "db"), str(B / "db")],
        "owned_pids": dict(owned)}
    record["monitor_a"] = stack(A, "monitor", *MONITOR_TICKS)
    record["repository_a"] = stack(A, "repository")
    record["repository_b"] = stack(B, "repository")
    record["cross_instance_is_refused"] = run(
        [A / "distro" / "baton-v12-stack", "status", "--instance",
         B / "instance.json"], expect=2, what="A's command, B's selector")

    before = (A / "instance.json").read_bytes()
    record["repeat_is_refused"] = run(
        [A / "distro" / "baton-v12-stack", "bootstrap", "--inputs",
         LIVE / "inputs.json", "--destination", A, "--distro", DISTRO],
        expect=2, what="a repeated bootstrap")
    after = (A / "instance.json").read_bytes()
    if INJECT == "selector-changed":
        after = before + b"\n"
    unchanged = after == before
    record["repeat_is_refused"]["selector_unchanged"] = unchanged
    if not unchanged:
        # ASSERTED, NOT RECORDED. Preservation is the whole point of the step,
        # and the superseded harness reported it false and still exited 0.
        note("a repeated bootstrap", "the selector byte-identical",
             "the selector CHANGED", "a refusal that rewrote what it refused "
             "to replace is not a refusal")

    selector = B / "instance.json"
    kept = restoring(selector, "instance-b's selector")
    selector.write_bytes(b"{ not a document")
    record["corrupt_selector_is_refused"] = stack(
        B, "status", expect=2, what="status over a corrupt selector")
    inject("while-the-selector-is-corrupt")
    selector.write_bytes(kept)
    record["restored_selector_works"] = stack(B, "status")
    record["the_runtime_mismatch_is_not_re_run_here"] = (
        "LIFECYCLE-187142.json holds it against a real installed bundle, and "
        "tests/tools/test_packaging.py holds it against the build. Corrupting "
        "a library is not a thing to do on the strength of a pid map that "
        "might be empty.")

    record["stop_a"] = stack(A, "stop")
    record["stop_b"] = stack(B, "stop")
    time.sleep(0.5)
    record["after_stop"] = {"a": stack(A, "status"), "b": stack(B, "status")}
    return record


def main():
    began = time.monotonic()
    record = {"how": "every command below was run from " + CWD + " with an "
              "environment of exactly " + json.dumps(ENVIRONMENT) + ": no "
              "PYTHONPATH, no BATON_V12_* operand, no virtual environment, "
              "nothing from the checkout",
              "injected": INJECT}
    raised = None
    try:
        lifecycle(record)
    except BaseException as failure:                         # noqa: BLE001
        raised = {"step": INJECT or "unknown",
                  "raised": type(failure).__name__ + ": " + str(failure),
                  "completed_before_it": sorted(record)}
    finally:
        try:
            settled = cleanup()
        except BaseException as failure:                     # noqa: BLE001
            settled = {"resolved": False,
                       "raised": [{"action": "cleanup",
                                   "raised": repr(failure)}]}
        record["raised"] = raised
        record["failures"] = failures
        record["cleanup"] = settled
        record["fixtures"] = fixtures()
        record["verdict"] = {
            "steps_failed": len(failures),
            "cleanup_resolved": settled.get("resolved", False),
            "instances_claimed": settled.get("claimed", []),
            "ok": not failures and raised is None and settled.get("resolved")}
        print(json.dumps({"record": record, "commands": ran,
                          "seconds": round(time.monotonic() - began, 3),
                          "harness": os.path.abspath(__file__)},
                         indent=1, sort_keys=True))
    return 0 if record["verdict"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
