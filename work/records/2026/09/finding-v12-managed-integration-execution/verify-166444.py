"""Focused deterministic reviewer child; M166331 removes cumulative gates."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

record = Path(__file__).resolve().parent
root = record.parents[4]
ledger_path = record / "review-ledger-166444.json"
if ledger_path.exists():
    raise SystemExit("Refuse overwrite")
run = {"argv": [sys.executable, str(record / "probe-166444.py")],
       "cwd": str(root / "v12/python"), "timeout_seconds": 15,
       "status": "pending", "log": "review-run-166444-1.log"}
ledger = {"work": "W161230", "claim": 166444, "authority": "M166331",
          "prior_reviewer_seconds": 22.257900130985945, "runs": [run],
          "qualification": "No cumulative gate; deterministic local files and mocks, no workload child or real signals"}
ledger_path.write_text(json.dumps(ledger, indent=2) + "\n")
with (record / run["log"]).open("wb") as output:
    started = time.monotonic()
    try:
        result = subprocess.run(run["argv"], cwd=run["cwd"],
                                env=dict(os.environ, PYTHONPATH="src:tools:."),
                                stdout=output, stderr=subprocess.STDOUT, timeout=15)
        run.update(status="finished", exit_code=result.returncode)
    except subprocess.TimeoutExpired:
        run.update(status="timeout", exit_code=None)
    finally:
        run["elapsed_seconds"] = time.monotonic() - started
ledger["reviewer_recorded_seconds"] = ledger["prior_reviewer_seconds"] + run["elapsed_seconds"]
ledger_path.write_text(json.dumps(ledger, indent=2) + "\n")
print(json.dumps(ledger))
