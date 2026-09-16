"""Bound and record exactly one selected focused process group."""
import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

packet = Path(__file__).resolve().parent
mode = sys.argv[1]
label = sys.argv[2]
root = packet.parents[5]
base = json.loads((packet / "base.json").read_text())
hashes = {row["path"]: hashlib.sha256((root / row["path"].removeprefix("baton:")).read_bytes()).hexdigest() for row in base["files"]}
command = [sys.executable, str(packet / "run-focused.py"), mode]
started = time.monotonic()
receipt = {"command": command, "mode": mode, "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "python": sys.version, "input_hashes": hashes,
           "dependencies": {p: importlib.metadata.version(p) for p in ("jsonschema", "referencing", "jsonschema-specifications", "attrs", "rpds-py")},
           "timeout_seconds": 180, "terminated": False}
with (packet / (label + ".log")).open("w") as log:
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, cwd=root / "v12/python")
    receipt["pid"] = process.pid
    receipt["pgid"] = process.pid
    try:
        receipt["exit_code"] = process.wait(timeout=180)
    except subprocess.TimeoutExpired:
        receipt["terminated"] = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        receipt["exit_code"] = process.returncode
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        receipt["process_group_absent"] = True
    else:
        receipt["process_group_absent"] = False
        os.killpg(process.pid, signal.SIGTERM)
        receipt["remaining_group_terminated"] = True
receipt["elapsed_seconds"] = time.monotonic() - started
receipt["log_sha256"] = hashlib.sha256((packet / (label + ".log")).read_bytes()).hexdigest()
(packet / (label + ".json")).write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({k: receipt[k] for k in ("exit_code", "elapsed_seconds", "process_group_absent", "terminated")}))
print((packet / (label + ".log")).read_text()[-10000:])
