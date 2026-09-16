"""W183883 — the retained installed-lifecycle harness, made exception-safe.

Supersedes LIFECYCLE-HARNESS-187015.py, which review 2026-09-16T14-26-38Z
showed was correct only on the happy path: a timeout after both starts escaped
with ZERO stops, and the selector and library it tampered with were restored on
the normal path only. A harness that leaves two schedulers running and a
corrupted library behind when it fails is a harness whose evidence cannot be
trusted about cleanup.

WHAT CHANGED, and it is the whole point of this file:

  * every mutation is registered with its own undo BEFORE it is made, and the
    undos run in a `finally`, in reverse order, whatever happened;
  * every instance this harness starts is registered as owned, and cleanup
    stops all of them -- twice if the first stop does not settle -- and then
    ASKS whether anything owned is still alive;
  * a failure is evidence rather than a lost run: the exception, the step it
    happened in, and the cleanup that followed are all in the output;
  * `W183883_INJECT` makes it fail on purpose, at a named step, so the
    paragraph above is a measurement rather than a claim.

WHAT IT DOES NOT DO: it submits no Job, contacts no provider, runs no engine,
reads no owner credential registry, and performs no version-control operation.
It installs nothing -- `just build` and `just bootstrap` do that.

    python3 LIFECYCLE-HARNESS-187142.py > LIFECYCLE-187142.json
    W183883_INJECT=after-starts python3 LIFECYCLE-HARNESS-187142.py   # proof
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

LIVE = pathlib.Path(os.environ.get("W183883_LIVE",
                                   "/var/tmp/w183883-live-186890"))
A = LIVE / "deployment"
B = LIVE / "deployment-b"
DISTRO = os.environ.get("W183883_DISTRO",
                        "/home/sl/src/baton/v12/python/build/out/distro")
INJECT = os.environ.get("W183883_INJECT")

# THE ENVIRONMENT IS THE CLAIM. An installed deployment reads nothing from the
# development checkout: no PYTHONPATH, no BATON_V12_* operand, no virtual
# environment on PATH. HOME is given because a process is entitled to one.
ENVIRONMENT = {"HOME": "/root", "PATH": "/usr/bin:/bin"}
CWD = "/"
TIMEOUT = 300           # seconds, per command
STOP_ATTEMPTS = 2       # bounded: a stop that will not settle is reported
MONITOR_TICKS = ("--interval", "0.2", "--ticks", "2")

ran = []
undo = []               # (what, callable), unwound in reverse in `finally`
owned = []              # every instance this harness started


def digest(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


def run(argv, *, timeout=TIMEOUT):
    started = time.monotonic()
    try:
        done = subprocess.run([str(one) for one in argv], capture_output=True,
                              text=True, timeout=timeout, cwd=CWD,
                              env=dict(ENVIRONMENT))
        answer = {"exit": done.returncode,
                  "stdout": done.stdout.strip().splitlines(),
                  "stderr": done.stderr.strip().splitlines()[-3:]}
    except subprocess.TimeoutExpired as expired:
        # RECORDED, NOT RAISED PAST THE CLEANUP. The old harness let this
        # escape mid-run, which is exactly when the stops did not happen.
        answer = {"exit": None, "timed_out": True, "stdout": [],
                  "stderr": [str(expired)]}
    answer.update({"argv": [str(one) for one in argv], "cwd": CWD,
                   "env": dict(ENVIRONMENT), "timeout_seconds": timeout,
                   "seconds": round(time.monotonic() - started, 3)})
    ran.append(answer)
    return answer


def stack(root, verb, *operands):
    return run([root / "distro" / "baton-v12-stack", verb, "--instance",
                root / "instance.json", *operands])


def started(root):
    """Start one instance and OWN it from that moment."""
    owned.append(root)
    return stack(root, "start")


def restoring(place, what):
    """Register the undo BEFORE the change, so a failure cannot outrun it."""
    place = pathlib.Path(place)
    held = place.read_bytes()
    undo.append((what, lambda: place.write_bytes(held)))
    return held


def inject(step):
    if INJECT == step:
        raise RuntimeError("injected failure at " + step)


def cleanup():
    """Bounded, and it reports what it could not settle rather than hoping."""
    answers = {"undone": [], "stops": [], "attempts": {}}
    for what, undoing in reversed(undo):
        try:
            undoing()
            answers["undone"].append(what)
        except Exception as failure:                         # noqa: BLE001
            answers["undone"].append(what + " FAILED: " + repr(failure))
    for root in owned:
        for attempt in range(1, STOP_ATTEMPTS + 1):
            said = stack(root, "stop")
            answers["stops"].append({"instance": str(root), "attempt": attempt,
                                     "exit": said["exit"],
                                     "stdout": said["stdout"]})
            answers["attempts"][str(root)] = attempt
            if said["exit"] == 0:
                break
    alive = subprocess.run(
        ["bash", "-lc", "pgrep -f 'baton-v12-stack (manager|publish)' || true"],
        capture_output=True, text=True, timeout=60)
    answers["still_running"] = alive.stdout.split()
    answers["no_owned_child_left_running"] = not answers["still_running"]
    answers["nothing_removed"] = ("the destinations and the fixture roots are "
                                  "retained; only this harness's own changes "
                                  "are undone")
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
    told = run([A / "distro" / "baton-v12-stack", "identity"])
    record["identity"] = json.loads("\n".join(told["stdout"]))
    record["start_a"] = started(A)
    record["start_b"] = started(B)
    inject("after-starts")
    record["a_status"] = stack(A, "status")
    record["b_status"] = stack(B, "status")
    record["isolation"] = {
        "a_stores": sorted(os.listdir(A / "db")),
        "b_stores": sorted(os.listdir(B / "db")),
        "distinct_state_roots": [str(A / "state"), str(B / "state")],
        "distinct_stores": [str(A / "db"), str(B / "db")]}
    record["monitor_a"] = stack(A, "monitor", *MONITOR_TICKS)
    record["repository_a"] = stack(A, "repository")
    record["repository_b"] = stack(B, "repository")
    record["cross_instance_is_refused"] = run(
        [A / "distro" / "baton-v12-stack", "status", "--instance",
         B / "instance.json"])

    before = (A / "instance.json").read_bytes()
    record["repeat_is_refused"] = run(
        [A / "distro" / "baton-v12-stack", "bootstrap", "--inputs",
         LIVE / "inputs.json", "--destination", A, "--distro", DISTRO])
    record["repeat_is_refused"]["selector_unchanged"] = (
        (A / "instance.json").read_bytes() == before)

    selector = B / "instance.json"
    kept = restoring(selector, "instance-b's selector")
    inject("before-corrupting-the-selector")
    selector.write_bytes(b"{ not a document")
    record["corrupt_selector_is_refused"] = stack(B, "status")
    inject("while-the-selector-is-corrupt")
    selector.write_bytes(kept)
    record["restored_selector_works"] = stack(B, "status")

    # THE MISMATCH IS DONE STOPPED, DELIBERATELY. An earlier attempt rewrote a
    # library the RUNNING manager had mapped and killed it: the refusal was
    # real and so was the crash, and reporting them together would report the
    # harness's own doing as a product property.
    record["stop_a"] = stack(A, "stop")
    record["stop_b"] = stack(B, "stop")
    time.sleep(0.5)
    record["after_stop"] = {"a": stack(A, "status"), "b": stack(B, "status")}

    library = B / "distro" / "_internal" / "libpython3.13.so.1.0"
    held = restoring(library, "instance-b's libpython")
    inject("before-tampering-with-the-library")
    library.write_bytes(held[:-1] + bytes([held[-1] ^ 0xFF]))
    record["changed_runtime_is_refused"] = {"status": stack(B, "status"),
                                            "start": stack(B, "start")}
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
    failure = None
    try:
        lifecycle(record)
    except BaseException as raised:                          # noqa: BLE001
        # EVIDENCE, NOT A LOST RUN. Which step, what was raised, and then the
        # cleanup below -- which is the thing the old harness could not
        # promise.
        failure = {"step": INJECT or "unknown",
                   "raised": type(raised).__name__ + ": " + str(raised),
                   "completed_before_it": sorted(record)}
    record["failure"] = failure
    record["cleanup"] = cleanup()
    record["fixtures"] = fixtures()
    print(json.dumps({"record": record, "commands": ran,
                      "seconds": round(time.monotonic() - began, 3),
                      "harness": os.path.abspath(__file__)},
                     indent=1, sort_keys=True))
    return 2 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
