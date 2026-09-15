"""Persist the fifth independent W32577 deterministic guard before its child."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

record = Path(__file__).resolve().parent
root = record.parents[6]
path = record / "review-ledger-163385.json"
if path.exists():
    raise SystemExit("Refuse overwrite")
cap, spent, expected, margin, timeout = 60.0, 4.757895970993559, 10.0, 3.0, 35.0
assert expected + margin <= cap - spent and timeout < cap - spent
run = {"argv": [sys.executable, "-W", "error", str(record / "probe-163385.py")],
       "cwd": str(root / "v12/python"), "status": "pending",
       "guard": {"cap_seconds": cap, "spent_seconds_before": spent,
                 "remaining_seconds_before": cap - spent,
                 "expected_seconds": expected, "margin_seconds": margin,
                 "timeout_seconds": timeout}, "log": "review-run-163385-1.log"}
ledger = {"work": "W32577", "claim": 163385, "cap_seconds": cap,
          "authority": "review-2026-09-13T18-26-19Z.md",
          "prior_reviewer_seconds": spent, "runs": [run],
          "python": sys.version, "jsonschema": importlib.metadata.version("jsonschema"),
          "qualification": "Deterministic only; pinned4.26.0 and Docker gate not satisfied"}
path.write_text(json.dumps(ledger, indent=2) + "\n")
with (record / run["log"]).open("wb") as output:
    start = time.monotonic()
    try:
        result = subprocess.run(run["argv"], cwd=run["cwd"],
            env=dict(os.environ, PYTHONPATH="src:tools:."),
            stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
        run.update(status="finished", exit_code=result.returncode)
    except subprocess.TimeoutExpired:
        run.update(status="timeout", exit_code=None)
    finally:
        run["elapsed_seconds"] = time.monotonic() - start
ledger["reviewer_spent_seconds"] = spent + run["elapsed_seconds"]
ledger["reviewer_remaining_seconds"] = cap - ledger["reviewer_spent_seconds"]
path.write_text(json.dumps(ledger, indent=2) + "\n")
print(json.dumps(ledger))
