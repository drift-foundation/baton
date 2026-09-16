"""Readiness boundary check with owned stand-ins, never a serving deployment."""
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "v12/python"))
from tools import stack

began = time.monotonic()
children = []
evidence = {"claim": 184197, "kind": "deterministic readiness-boundary stand-ins; no actual manager initialization, provider or engine"}
with tempfile.TemporaryDirectory(prefix="w184197-ready-") as tmp:
    root = Path(tmp)
    try:
        for name in stack.PROCESSES:
            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            children.append(child)
            stack.write_record(root, name, {"schema": stack.SCHEMA, "name": name, "pid": child.pid, "started_at": stack.started_at(child.pid)})
        children[0].send_signal(signal.SIGSTOP)
        deadline = time.monotonic() + 2
        while stack._proc(children[0].pid)[0] != "T" and time.monotonic() < deadline:
            time.sleep(0.005)
        evidence["manager_process_state"] = stack._proc(children[0].pid)[0]
        assert evidence["manager_process_state"] == "T"
        stack.snapshot_path(root).write_text(json.dumps({"schema": "baton.v12.job-status/4", "canonical": True, "jobs": []}))
        observed = stack._await_ready(root, None, ready_seconds=0.1, sleep=time.sleep, monotonic=time.monotonic)
        evidence["readiness_accepted"] = observed is not None
        evidence["limitation"] = "Snapshot and processes are controlled stand-ins. Static observation_from inspection independently shows the publisher need not initialize the serving factory. This proves the admission gate requires no serving acknowledgement, not a full deployed failure."
    finally:
        for child in children:
            child.kill()
            child.wait(timeout=2)
        evidence["all_owned_children_reaped"] = all(c.poll() is not None for c in children)
evidence["seconds"] = time.monotonic() - began
target = Path(__file__).with_name("READINESS-REVIEW-EVIDENCE-184197.json")
target.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
print(json.dumps(evidence))
