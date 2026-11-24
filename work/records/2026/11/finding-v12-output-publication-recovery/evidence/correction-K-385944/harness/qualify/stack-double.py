#!/usr/bin/env python3
"""THE STACK DOUBLE for the dry runs. It keeps the PRODUCT'S OWN process records and answers with the product's
own text: every record is written by the reviewed `tools.stack._spawn` (pid AND start time, the caller's
environment handed on), `status` is the reviewed `tools.stack.status`, and `stop` is the reviewed
`tools.stack.stop`. Only what a "manager" and a "publisher" ARE is doubled: each is a `sleep`.

  stack-double.py STATE-ROOT WORLD start|stop|status
WORLD/start-mode selects how a start goes:
  ok | fail-clean | fail-partial | slow-before:N | slow-after:N | foreign | unrecorded | ok+corrupt-record | ok+status-down
WORLD/stop-mode `refuses` makes stop answer failure and stop nothing.
"""
import os, subprocess, sys, time
from pathlib import Path
REPO = os.environ.get("HARNESS_TREE", "/home/sl/src/baton/work/scratch/w385695-K-385897/repo")
sys.path[:0] = [REPO + "/v12/python", REPO + "/v12/python/src"]
from tools import stack

root, world, verb = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
read = lambda name, default: (world / name).read_text().strip() if (world / name).exists() else default


def spawn(name, environ=None):
    return stack._spawn(root, name, ["sleep", "600"], dict(os.environ if environ is None else environ))


if verb == "start":
    (world / "started").touch()
    mode = read("start-mode", "ok")
    if mode == "fail-clean":
        print("could not start"); sys.exit(1)
    if mode.startswith("slow-before:"):
        time.sleep(float(mode.split(":")[1]))
    if mode == "foreign":
        # ANOTHER START WON: live processes that do not carry this caller's token, reported as already running.
        clean = {k: v for k, v in os.environ.items() if k != "W385695_STACK_START"}
        for name in stack.PROCESSES:
            print("already running: %s pid %d" % (name, spawn(name, clean)["pid"]))
        sys.exit(0)
    if mode == "unrecorded":
        # KILLED BETWEEN STARTING A PROCESS AND RECORDING IT: a process of this start that no record names.
        subprocess.Popen(["sleep", "600"], start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sys.exit(1)
    for name in stack.PROCESSES[:1] if mode == "fail-partial" else stack.PROCESSES:
        print("started: %s pid %d" % (name, spawn(name)["pid"]))
    (world / "effect").touch()
    if mode == "fail-partial":
        sys.exit(1)
    if mode.startswith("slow-after:"):
        time.sleep(float(mode.split(":")[1]))
    if mode == "ok+corrupt-record":
        (root / "manager.json").write_text("{ not a record")
    if mode == "ok+status-down":
        (world / "status-down").touch()
    sys.exit(0)
if verb == "status":
    if (world / "status-down").exists():
        print("status: cannot reach the state root", file=sys.stderr); sys.exit(1)
    sys.exit(stack.status(root, environ={}))
if verb == "stop":
    with open(world / "stops", "a") as out:
        out.write("stopped\n")
    if read("stop-mode", "") == "refuses":
        print("did not stop"); sys.exit(1)
    sys.exit(stack.stop(root))
