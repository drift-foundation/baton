"""Capture assertions for the emitting lifecycle. W202663, review208890 item 2.

PREPARED BEFORE THE RUN THAT SATISFIES IT. After the next lifecycle executes
with the emitting producer image (`compose-verification-208217.py
--emitting`), this asserts what "usable logs" actually means, through the
SUPPORTED reader only:

  1. the implementation attempt's `worker.stdout` and `worker.stderr` are
     PRESENT and NONEMPTY;
  2. the bytes read back through `tools.attempt_logs_command read` carry the
     emitting fixture's deterministic marker lines -- content, not mere
     existence;
  3. the streams survive after the runtime is gone: this is run AFTER the
     container exited (and can be re-run after cleanup), so what it proves is
     RETENTION.

It asserts nothing about provider-native session files -- the fixture enters
no provider and its `native` room is expected empty -- and exits nonzero the
moment any assertion fails, naming it.

READ ONLY. It discovers the newest implementation attempt under the selected
instance's launch logs, calls the supported locators and read commands as
subprocesses, and writes nothing anywhere.
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTHON = Path("/home/sl/src/baton/v12/python")
MARK = "w202663-emitting-fixture"

# THE WORK-PHASE LINES ONLY, because `consider` IS NOT REACHABLE in this
# workload -- review209080's source correction, superseding my earlier
# "per-phase overwrite" explanation. `baton_worker.py` serves
# `OPERATIONS = (describe, work)`; `handle` refuses `consider` with an
# entitlement refusal before any `agent.consider` runs, so
# `EmittingAgent.consider`'s markers were an unreachable expectation, not
# lost capture (the writer opens O_APPEND; no truncation was demonstrated).
# capture-assert-1-208996.log is preserved as the record of that mistaken
# expectation. If some other path is alleged to emit those lines, that path
# must be demonstrated independently before any loss claim is made.
REQUIRED_LINES = {
    "worker.stdout": [
        f"{MARK}: work begins on the frozen task",
        f"{MARK}: work ends disposition=completed",
    ],
    "worker.stderr": [
        f"{MARK}: work stderr closing line",
    ],
}


def _command(argv):
    return subprocess.run(argv, capture_output=True, text=True, timeout=120,
                          cwd=str(PYTHON),
                          env={"PATH": "/usr/bin:/bin", "PYTHONPATH": "src:."})


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        instance = Path(argv[0])
    else:
        selected = HERE / "selected-instance.txt"
        if not selected.is_file():
            print(f"refused: no instance named and {selected} is not here",
                  file=sys.stderr)
            return 2
        instance = Path(selected.read_text().strip())
    logs = instance / "workers/implementation/launch/logs"
    attempts = sorted((one for one in logs.iterdir() if one.is_dir()),
                      key=lambda one: one.stat().st_mtime) \
        if logs.is_dir() else []
    if not attempts:
        print(f"refused: {logs} holds no attempt; run the emitting lifecycle "
              f"first", file=sys.stderr)
        return 2
    attempt = attempts[-1].name
    print(f"instance: {instance}\nattempt:  {attempt}")

    failures = []

    done = _command(["python3", "-m", "tools.attempt_logs_command",
                     "--logs", str(logs), "--attempt", attempt, "locators"])
    if done.returncode != 0:
        print(f"FAIL locators exited {done.returncode}: {done.stderr[:400]}",
              file=sys.stderr)
        return 1
    located = json.loads(done.stdout)
    streams = {one["stream"]: one for one in located["streams"]}
    for name in REQUIRED_LINES:
        held = streams.get(name)
        ok = held is not None and held["state"] not in ("absent",) \
            and held["bytes"] > 0
        print(("ok   " if ok else "FAIL ")
              + f"{name} present and nonempty "
              + f"(state={held['state'] if held else 'missing'}, "
                f"bytes={held['bytes'] if held else 0})")
        if not ok:
            failures.append(name + " empty or absent")

    for name, needed in REQUIRED_LINES.items():
        done = _command(["python3", "-m", "tools.attempt_logs_command",
                         "--logs", str(logs), "--attempt", attempt,
                         "read", "--stream", name, "--text"])
        if done.returncode != 0:
            print(f"FAIL read {name} exited {done.returncode}",
                  file=sys.stderr)
            failures.append(name + " unreadable")
            continue
        for line in needed:
            ok = line in done.stdout
            print(("ok   " if ok else "FAIL ")
                  + f"{name} carries {line[:60]!r}")
            if not ok:
                failures.append(f"{name} missing {line!r}")

    if failures:
        print(f"\n{len(failures)} capture assertion(s) failed",
              file=sys.stderr)
        return 1
    print("all capture assertions passed: nonempty retained worker streams "
          "with the deterministic fixture content, read through the "
          "supported reader")
    return 0


if __name__ == "__main__":
    sys.exit(main())
