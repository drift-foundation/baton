"""Run only this dossier's explicit offline tests with owned process cleanup."""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

here = Path(__file__).resolve().parent
label = sys.argv[1]
started = time.monotonic()
command = [sys.executable, str(here / "test_qualification.py")]
with (here / (label + ".log")).open("w") as log:
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    timed_out = False
    try:
        code = process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        code = process.wait(timeout=5)
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        absent = True
    else:
        absent = False
        os.killpg(process.pid, signal.SIGKILL)
result = {"command": command, "python": sys.version, "elapsed_seconds": time.monotonic() - started, "exit_code": code,
          "timeout_seconds":30, "timed_out":timed_out, "process_group_absent":absent, "pid":process.pid,
          "manifest_sha256":hashlib.sha256((here / "qualification-manifest.json").read_bytes()).hexdigest(),
          "log_sha256":hashlib.sha256((here / (label + ".log")).read_bytes()).hexdigest(),
          "execution":"offline fake-engine tests and bounded local Python pipe fixtures only; no actual engine/model/credential"}
(here / (label + ".json")).write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result))
print((here / (label + ".log")).read_text())
