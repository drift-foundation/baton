"""W385227 deterministic stack verification; no build, live instance or engine."""
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[6]
command = ["/home/sl/.local/state/baton-v12-venv/bin/python", "-m", "unittest", "-v", "tests.tools.test_stack"]
env = dict(os.environ, PYTHONPATH="src:.", TMPDIR="/var/tmp", BATON_V12_DISK_ROOT="/var/tmp", PYTHONDONTWRITEBYTECODE="1")
start = time.monotonic()
with Path(__file__).with_name("focused-final.log").open("w") as log:
    result = subprocess.run(command, cwd=ROOT / "v12/python", env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
record = {"command": command, "cwd": "v12/python", "timeout_seconds": 180, "exit_code": result.returncode, "wall_seconds": time.monotonic() - start, "environment_overrides": {k:env[k] for k in ("PYTHONPATH", "TMPDIR", "BATON_V12_DISK_ROOT", "PYTHONDONTWRITEBYTECODE")}}
Path(__file__).with_name("focused-final-run.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record))
raise SystemExit(result.returncode)
