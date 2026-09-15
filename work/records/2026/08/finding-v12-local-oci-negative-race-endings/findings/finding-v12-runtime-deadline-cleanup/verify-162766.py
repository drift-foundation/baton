"""Persist the selected W32577 cumulative author budget around every test child."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
ledger = root / "verification-162766.json"
rows = json.loads(ledger.read_text()) if ledger.exists() else []
spent = sum(row.get("elapsed", row["timeout"]) for row in rows)
remaining = 120 - spent
expected, margin, timeout = 5, 5, min(25, remaining - 1)
if remaining <= expected + margin or timeout <= expected + margin:
    raise SystemExit("W32577 verification budget cannot fit another child")
command = [sys.executable, "-W", "error", "-m", "unittest", *sys.argv[1:]]
row = {"command": command, "cap": 120, "spent_before": spent,
       "remaining_before": remaining, "expected": expected, "margin": margin,
       "timeout": timeout, "state": "running", "python": sys.version,
       "jsonschema": importlib.metadata.version("jsonschema")}
rows.append(row)
ledger.write_text(json.dumps(rows, indent=2) + "\n")
log = root / f"verification-162766-{len(rows)}.log"
start = time.monotonic()
try:
    with log.open("w") as output:
        result = subprocess.run(command, cwd="/home/sl/src/baton/v12/python",
            env={**os.environ, "PYTHONPATH": "/home/sl/src/baton/v12/python/src:" + str(root)},
            stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
    row["returncode"] = result.returncode
    row["state"] = "completed"
except subprocess.TimeoutExpired:
    row["returncode"] = 124
    row["state"] = "timed-out"
finally:
    row["elapsed"] = time.monotonic() - start
    row["log"] = log.name
    ledger.write_text(json.dumps(rows, indent=2) + "\n")
print(log.read_text()[-6000:])
print(json.dumps({"spent": sum(one["elapsed"] for one in rows), "cap": 120,
                  "python": row["python"], "jsonschema": row["jsonschema"]}))
raise SystemExit(row["returncode"])
