"""Run one declared selector within W122060's cumulative 20-second budget."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

here = Path(__file__).resolve().parent
repo = next(parent for parent in here.parents if (parent / "v12/python/src").is_dir())
history = here / "verification.json"
runs = json.loads(history.read_text()) if history.exists() else []
remaining = 20 - sum(run["elapsed_seconds"] for run in runs)
if remaining <= 0:
    raise SystemExit("Verification budget exhausted")
command = [sys.executable, "-m", "unittest", "-v", *sys.argv[1:]]
if sys.argv[1:] == ["--probe"]:
    command = [sys.executable, str(here / "probe.py")]
    remaining = min(remaining, 3)
started = time.monotonic()
try:
    result = subprocess.run(command, cwd=repo / "v12/python", env={**os.environ, "PYTHONPATH": "src:."},
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=remaining)
    output, code = result.stdout, result.returncode
except subprocess.TimeoutExpired as error:
    output, code = error.stdout or "", 124
    if isinstance(output, bytes):
        output = output.decode()
elapsed = time.monotonic() - started
log = f"verification-{len(runs) + 1}.log"
(here / log).write_text(output)
runs.append({"command": command, "cwd": "v12/python", "PYTHONPATH": "src:.", "elapsed_seconds": elapsed,
             "returncode": code, "log": log})
history.write_text(json.dumps(runs, indent=2) + "\n")
print(output[-6000:])
print(json.dumps({"elapsed_seconds": elapsed, "cumulative_seconds": sum(run["elapsed_seconds"] for run in runs), "returncode": code}))
raise SystemExit(code)
