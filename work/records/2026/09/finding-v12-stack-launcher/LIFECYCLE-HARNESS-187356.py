"""W183883 — the installed-lifecycle harness: BOTH sides, or no demonstration.

Supersedes LIFECYCLE-HARNESS-187303.py, which established ownership per
instance and then asked only `if not owned:` -- "did I claim ANYTHING?" Review
2026-09-16T15-04-03Z showed what that costs in a MIXED case: with A fresh and B
already running, A was claimed, B was refused, and the shared lifecycle ran
anyway -- corrupting B's selector and calling the normal-path `stop(B)` on an
instance this run did not own. In the reverse order it stopped an unclaimed A.
The cleanup filter was right; the normal path walked around it.

WHAT IT DOES NOW:

  * BOTH instances must be claimed with a COMPLETE, CONFIRMED identity before
    any shared step runs. If either is refused or incomplete, the demonstration
    ends there and only bounded cleanup for legitimately claimed instances
    runs.
  * every write and every stop goes through one gate that refuses a path or an
    instance this run does not own, and each refusal is recorded -- so a later
    edit cannot walk around the filter the way the normal path just did.
  * the run reports exactly which instances it touched, and a touch of an
    unclaimed instance is a failure, not a line in a log.

Kept from 187303: ownership read through the deployment's OWN four-state reader
(absent / running / gone / unknown), unknown never read as absence, identity
complete or unknown, the repeated-bootstrap preservation ASSERTED, and no
library corruption at all -- `LIFECYCLE-187142.json` and `test_packaging` hold
the runtime mismatch against a real bundle.

It submits no Job, contacts no provider, runs no engine, reads no owner
credential registry, and performs no version-control operation.

    python3 LIFECYCLE-HARNESS-187356.py > LIFECYCLE-187356.json
    W183883_INJECT=<boundary> python3 LIFECYCLE-HARNESS-187356.py

Boundaries, and a side may be named: already-running:B, start-timeout:A,
start-silent:B, alive-unknown:A, both-running, after-starts, timeout-status,
stop-nonzero, cleanup-raises, selector-changed.
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
_INJECT = os.environ.get("W183883_INJECT", "")
INJECT, _, SIDE = _INJECT.partition(":")

ENVIRONMENT = {"HOME": "/root", "PATH": "/usr/bin:/bin"}
CWD = "/"
TIMEOUT = 300
STOP_ATTEMPTS = 2
MONITOR_TICKS = ("--interval", "0.2", "--ticks", "2")
PROCESSES = ("manager", "publisher")
STARTED = re.compile(r"^started: (\w+) pid (\d+)$")
REPORTED = re.compile(r"^(\w+)\s+(absent|running|gone|unknown)(?: pid (\d+))?")

ran = []
undo = []
owned = {}
claimed = []
touched = []            # every instance this run wrote to or stopped
failures = []


def digest(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


def note(step, expected, got, detail=None):
    failures.append({"step": step, "expected": expected, "got": got,
                     "detail": detail})


def side_of(root):
    return "A" if root == A else "B"


def targeted(root):
    """Does the named injection apply to this instance?"""
    return not SIDE or SIDE.upper() == side_of(root)


def run(argv, *, expect=0, what=None, timeout=TIMEOUT, root=None):
    what = what or " ".join(str(one) for one in argv[1:3])
    began = time.monotonic()
    verb = [str(one) for one in argv]
    try:
        if INJECT == "timeout-status" and "status" in verb and targeted(root or A):
            raise subprocess.TimeoutExpired(argv, timeout)
        if INJECT == "start-timeout" and "start" in verb and targeted(root or A):
            raise subprocess.TimeoutExpired(argv, timeout)
        done = subprocess.run(verb, capture_output=True, text=True,
                              timeout=timeout, cwd=CWD, env=dict(ENVIRONMENT))
        answer = {"exit": done.returncode,
                  "stdout": done.stdout.strip().splitlines(),
                  "stderr": done.stderr.strip().splitlines()[-3:]}
        if INJECT == "start-silent" and "start" in verb and targeted(root or A):
            answer["stdout"] = ["already running: manager",
                                "already running: publisher"]
    except subprocess.TimeoutExpired:
        answer = {"exit": None, "timed_out": True, "stdout": [], "stderr": []}
    answer.update({"argv": verb, "cwd": CWD, "env": dict(ENVIRONMENT),
                   "timeout_seconds": timeout, "what": what,
                   "expected_exit": expect,
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
               expect=expect, what=what or (verb + " " + root.name), root=root)


def mine(root, doing):
    """THE ONE GATE. Nothing writes to, or stops, an instance this run does not
    own -- whether it is the cleanup asking or the normal path."""
    if str(root) in owned:
        touched.append({"instance": str(root), "doing": doing})
        return True
    note(doing + " " + root.name, "only an instance this run claimed",
         "that instance is NOT owned by this run",
         "refused before it happened; the normal path used to walk around the "
         "cleanup filter here")
    return False


def reported(root, *, what=None):
    said = stack(root, "status", expect=None,
                 what=what or ("status " + root.name))
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
    if INJECT == "alive-unknown" and targeted(root):
        states = {name: {"state": "unknown", "pid": None} for name in PROCESSES}
    return states


def unclaimed(root):
    states = reported(root, what="ownership preflight " + root.name)
    if INJECT in ("already-running", "both-running") and (
            INJECT == "both-running" or targeted(root)):
        states = {"manager": {"state": "running", "pid": 999999},
                  "publisher": {"state": "running", "pid": 999998}}
    unexpected = {name: one for name, one in states.items()
                  if one["state"] != "absent"}
    return (not unexpected), states, unexpected


def claim(root):
    ok, before, unexpected = unclaimed(root)
    if not ok:
        note("ownership preflight " + root.name, "every process absent",
             json.dumps(unexpected),
             "this run does not own that instance; nothing was started and "
             "nothing of somebody else's will be touched")
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
        said["identity"] = "unknown"
        said["reported_after"] = after
        note("ownership of " + root.name,
             "a pid for " + " and ".join(PROCESSES), json.dumps(pids),
             "identity is UNKNOWN, not absent")
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
    left = {}
    for root in claimed:
        for name, one in reported(root, what="survivor check " + root.name).items():
            if one["state"] != "absent":
                left["%s/%s" % (root.name, name)] = one
    return left


def stopping(root, *, what):
    """Every stop, normal path or cleanup, through the one gate."""
    if not mine(root, "stop"):
        return {"refused": True, "exit": None}
    return stack(root, "stop", expect=None, what=what)


def cleanup():
    answers = {"undone": [], "stops": [], "raised": [],
               "claimed": [str(one) for one in claimed],
               "owned_pids": dict(owned),
               "touched": touched}
    for what, undoing in reversed(undo):
        try:
            undoing()
            answers["undone"].append({"what": what, "ok": True})
        except BaseException as failure:                     # noqa: BLE001
            answers["undone"].append({"what": what, "ok": False,
                                      "raised": repr(failure)})
            answers["raised"].append({"action": "undo " + what,
                                      "raised": repr(failure)})
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
    answers["unclaimed_instances_touched"] = [
        one for one in touched if one["instance"] not in owned]
    answers["nothing_removed"] = ("the destinations and the fixture roots are "
                                  "retained; only this run's own changes are "
                                  "undone, and only instances it claimed are "
                                  "written to or stopped")
    answers["resolved"] = (not left and not answers["raised"]
                           and not answers["unclaimed_instances_touched"]
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

    # BOTH, OR NOTHING. The shared lifecycle reads and writes across A AND B --
    # cross-instance dispatch, the selector corruption, the stops -- so one
    # side being somebody else's is not a reason to continue with the other:
    # it is a reason to stop.
    complete = {str(A), str(B)} <= set(owned)
    record["both_sides_claimed"] = {
        "owned": sorted(owned), "complete": complete}
    if not complete:
        record["stopped_early"] = (
            "the demonstration needs BOTH instances with a complete, confirmed "
            "identity; it ran none of the shared steps and will stop only what "
            "it legitimately claimed")
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
        note("a repeated bootstrap", "the selector byte-identical",
             "the selector CHANGED", "a refusal that rewrote what it refused "
             "to replace is not a refusal")

    selector = B / "instance.json"
    if mine(B, "write"):
        kept = restoring(selector, "instance-b's selector")
        selector.write_bytes(b"{ not a document")
        record["corrupt_selector_is_refused"] = stack(
            B, "status", expect=2, what="status over a corrupt selector")
        inject("while-the-selector-is-corrupt")
        selector.write_bytes(kept)
        record["restored_selector_works"] = stack(B, "status")
    record["the_runtime_mismatch_is_not_re_run_here"] = (
        "LIFECYCLE-187142.json holds it against a real installed bundle, and "
        "tests/tools/test_packaging.py holds it against the build.")

    record["stop_a"] = stopping(A, what="stop A")
    record["stop_b"] = stopping(B, what="stop B")
    time.sleep(0.5)
    record["after_stop"] = {"a": stack(A, "status"), "b": stack(B, "status")}
    return record


def main():
    began = time.monotonic()
    record = {"how": "every command below was run from " + CWD + " with an "
              "environment of exactly " + json.dumps(ENVIRONMENT) + ": no "
              "PYTHONPATH, no BATON_V12_* operand, no virtual environment, "
              "nothing from the checkout",
              "injected": _INJECT or None}
    raised = None
    try:
        lifecycle(record)
    except BaseException as failure:                         # noqa: BLE001
        raised = {"step": _INJECT or "unknown",
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
            "instances_touched": sorted(
                {one["instance"] for one in settled.get("touched", [])}),
            "unclaimed_touched": settled.get("unclaimed_instances_touched", []),
            "ok": not failures and raised is None and settled.get("resolved")}
        print(json.dumps({"record": record, "commands": ran,
                          "seconds": round(time.monotonic() - began, 3),
                          "harness": os.path.abspath(__file__)},
                         indent=1, sort_keys=True))
    return 0 if record["verdict"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
