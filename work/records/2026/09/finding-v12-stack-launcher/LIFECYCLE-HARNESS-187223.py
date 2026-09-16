"""W183883 — the installed-lifecycle harness, with its outcomes CHECKED.

Supersedes LIFECYCLE-HARNESS-187142.py. That one unwound its changes and
stopped what it started, and review 2026-09-16T14-40-22Z showed it still
reported success in four situations where nothing had been established:

  * a status that TIMED OUT was recorded and the run returned 0 with
    `failure: null` -- an outcome nobody had asked for, reported as evidence;
  * stops that exited non-zero, with a survivor named, still let the library be
    tampered with and still returned 0;
  * a FileNotFoundError on the first cleanup stop escaped, skipped the second
    instance's stop entirely, and emitted NO JSON at all, so the run that went
    wrong is the one that left no record;
  * "nothing owned is still running" was a GLOBAL `pgrep`, which answers about
    every deployment on the host rather than about the pids this harness
    started.

WHAT IT DOES NOW:

  * every step declares the outcome it expects, and an outcome that does not
    match is a FAILURE with both sides recorded;
  * the pids this harness starts are read from `start`'s own output and owned
    by pid; liveness is asked of THOSE pids, through /proc, never of a pattern;
  * the runtime is not tampered with unless both instances are PROVED stopped;
  * each cleanup action is isolated: one raising does not stop the others, and
    each records what happened;
  * the JSON is emitted from a `finally`, so the run that failed is the one
    with the fullest record;
  * the exit is non-zero when any step failed OR when cleanup did not resolve.

`W183883_INJECT` names a boundary to simulate, so all of the above is measured
rather than asserted:

    normal            python3 LIFECYCLE-HARNESS-187223.py > LIFECYCLE-187223.json
    after-starts      an exception mid-run
    timeout-status    a status that times out
    stop-nonzero      cleanup stops that exit non-zero
    cleanup-raises    an undo that raises
    survivor          an owned pid that is still alive at the end

It submits no Job, contacts no provider, runs no engine, reads no owner
credential registry, and performs no version-control operation.
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
STARTED = re.compile(r"^started: (\w+) pid (\d+)$")

ran = []
undo = []
owned = []              # instances started here
pids = {}               # pid -> what it is, for every child this run started
failures = []           # every step whose outcome was not the expected one


def digest(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


def run(argv, *, expect=0, what=None, timeout=TIMEOUT):
    """One command, with the outcome it is supposed to have.

    `expect` is an exit status, or None for "any" (only used where the point IS
    to record whatever happened). A mismatch is a failure rather than a line in
    a report nobody reads.
    """
    what = what or " ".join(str(one) for one in argv[1:3])
    started = time.monotonic()
    try:
        if INJECT == "timeout-status" and "status" in [str(one) for one in argv]:
            raise subprocess.TimeoutExpired(argv, timeout)
        done = subprocess.run([str(one) for one in argv], capture_output=True,
                              text=True, timeout=timeout, cwd=CWD,
                              env=dict(ENVIRONMENT))
        answer = {"exit": done.returncode,
                  "stdout": done.stdout.strip().splitlines(),
                  "stderr": done.stderr.strip().splitlines()[-3:]}
    except subprocess.TimeoutExpired:
        # A TIMEOUT IS AN OUTCOME, AND IT IS NOT THE EXPECTED ONE. It is
        # recorded rather than raised past the cleanup, and it FAILS the run.
        answer = {"exit": None, "timed_out": True, "stdout": [], "stderr": []}
    answer.update({"argv": [str(one) for one in argv], "cwd": CWD,
                   "env": dict(ENVIRONMENT), "timeout_seconds": timeout,
                   "what": what, "expected_exit": expect,
                   "seconds": round(time.monotonic() - started, 3)})
    if expect is not None and answer["exit"] != expect:
        answer["unexpected"] = True
        failures.append({"step": what, "expected_exit": expect,
                         "got_exit": answer["exit"],
                         "timed_out": answer.get("timed_out", False),
                         "stderr": answer["stderr"]})
    ran.append(answer)
    return answer


def stack(root, verb, *operands, expect=0, what=None):
    return run([root / "distro" / "baton-v12-stack", verb, "--instance",
                root / "instance.json", *operands],
               expect=expect, what=what or (verb + " " + root.name))


def started(root):
    """Start one instance, and own the pids it reports BY PID."""
    owned.append(root)
    said = stack(root, "start", what="start " + root.name)
    for line in said["stdout"]:
        matched = STARTED.match(line.strip())
        if matched:
            pids[int(matched.group(2))] = matched.group(1) + " of " + root.name
    said["owned_pids"] = {pid: what for pid, what in pids.items()
                          if what.endswith(root.name)}
    return said


def alive(pid):
    """Is THIS pid still a live process? Asked of /proc, never of a pattern.

    A global `pgrep` answers about every deployment on the host -- including
    another operator's -- and says nothing about the children this run
    started.
    """
    try:
        with open("/proc/%d/stat" % pid, "rb") as reading:
            fields = reading.read().rsplit(b")", 1)[1].split()
    except (OSError, IndexError):
        return False
    return fields[0] != b"Z"        # a reaped zombie is not running


def survivors():
    if INJECT == "survivor":
        return {os.getpid(): "an injected survivor (this process)"}
    return {pid: what for pid, what in pids.items() if alive(pid)}


def restoring(place, what):
    """Register the undo BEFORE the change, so a failure cannot outrun it."""
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


def stopped_now():
    """Are both instances stopped RIGHT NOW, by the pids we started?"""
    return not survivors()


def cleanup():
    """Every action isolated, every outcome recorded, and a verdict."""
    answers = {"undone": [], "stops": [], "raised": []}
    for what, undoing in reversed(undo):
        try:
            undoing()
            answers["undone"].append({"what": what, "ok": True})
        except BaseException as failure:                     # noqa: BLE001
            # ISOLATED: one undo that raises must not skip the others, and it
            # must not skip the stops either. That is exactly what escaped.
            answers["undone"].append({"what": what, "ok": False,
                                      "raised": repr(failure)})
            answers["raised"].append({"action": "undo " + what,
                                      "raised": repr(failure)})
    for root in owned:
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
    answers["owned_pids"] = {str(pid): what for pid, what in pids.items()}
    answers["still_running"] = {str(pid): what for pid, what in left.items()}
    answers["nothing_removed"] = ("the destinations and the fixture roots are "
                                  "retained; only this harness's own changes "
                                  "are undone")
    answers["resolved"] = (not left
                           and not answers["raised"]
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
    record["start_a"] = started(A)
    record["start_b"] = started(B)
    inject("after-starts")
    record["a_status"] = stack(A, "status")
    record["b_status"] = stack(B, "status")
    record["isolation"] = {
        "a_stores": sorted(os.listdir(A / "db")),
        "b_stores": sorted(os.listdir(B / "db")),
        "distinct_state_roots": [str(A / "state"), str(B / "state")],
        "distinct_stores": [str(A / "db"), str(B / "db")],
        "owned_pids": {str(pid): what for pid, what in pids.items()}}
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
    record["repeat_is_refused"]["selector_unchanged"] = (
        (A / "instance.json").read_bytes() == before)

    selector = B / "instance.json"
    kept = restoring(selector, "instance-b's selector")
    selector.write_bytes(b"{ not a document")
    record["corrupt_selector_is_refused"] = stack(
        B, "status", expect=2, what="status over a corrupt selector")
    inject("while-the-selector-is-corrupt")
    selector.write_bytes(kept)
    record["restored_selector_works"] = stack(B, "status")

    record["stop_a"] = stack(A, "stop")
    record["stop_b"] = stack(B, "stop")
    time.sleep(0.5)
    record["after_stop"] = {"a": stack(A, "status"), "b": stack(B, "status")}

    # THE RUNTIME IS NOT TOUCHED UNLESS BOTH ARE PROVED STOPPED. An earlier
    # harness rewrote a library the RUNNING manager had mapped and killed it;
    # its successor checked nothing and tampered even when the stops had failed
    # and a survivor had been named. This asks the owned pids, and if any is
    # alive the mutation does not happen and the run says why.
    left = survivors()
    record["proved_stopped_before_touching_the_runtime"] = {
        "survivors": {str(pid): what for pid, what in left.items()},
        "proceeded": not left}
    if left:
        failures.append({"step": "the runtime mutation was SKIPPED",
                         "expected_exit": "no owned pid alive",
                         "got_exit": "alive: " + json.dumps(
                             {str(pid): what for pid, what in left.items()}),
                         "timed_out": False, "stderr": []})
        return record

    library = B / "distro" / "_internal" / "libpython3.13.so.1.0"
    held = restoring(library, "instance-b's libpython")
    library.write_bytes(held[:-1] + bytes([held[-1] ^ 0xFF]))
    record["changed_runtime_is_refused"] = {
        "status": stack(B, "status", expect=2,
                        what="status over a changed runtime"),
        "start": stack(B, "start", expect=2,
                       what="start over a changed runtime")}
    inject("while-the-library-is-tampered")
    library.write_bytes(held)
    record["restored_runtime_is_accepted"] = stack(B, "status")
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
        # EMITTED WHATEVER HAPPENED. The run that went wrong is the one whose
        # record matters, and the superseded harness emitted nothing at all
        # when its cleanup raised.
        try:
            settled = cleanup()
        except BaseException as failure:                     # noqa: BLE001
            settled = {"resolved": False,
                       "raised": [{"action": "cleanup", "raised": repr(failure)}]}
        record["raised"] = raised
        record["failures"] = failures
        record["cleanup"] = settled
        record["fixtures"] = fixtures()
        record["verdict"] = {
            "steps_failed": len(failures),
            "cleanup_resolved": settled.get("resolved", False),
            "ok": not failures and raised is None and settled.get("resolved")}
        print(json.dumps({"record": record, "commands": ran,
                          "seconds": round(time.monotonic() - began, 3),
                          "harness": os.path.abspath(__file__)},
                         indent=1, sort_keys=True))
    return 0 if record["verdict"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
