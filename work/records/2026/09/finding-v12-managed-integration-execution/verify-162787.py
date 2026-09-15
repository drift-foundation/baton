"""Persist cumulative review guard before one deterministic research child."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

record = Path(__file__).resolve().parent
root = record.parents[4]
prior = json.loads((record / "review-ledger-162696.json").read_text())
spent = prior["prior_reviewer_seconds"] + sum(r["elapsed_seconds"] for r in prior["runs"])
remaining = 300.0 - spent
expected, margin, timeout = 10.0, 3.0, 30.0
if expected + margin > remaining or not 0 < timeout < remaining:
    raise SystemExit("Budget guard refused")
path = record / "review-ledger-162787.json"
if path.exists():
    raise SystemExit("Refuse overwrite")
run = {"argv": [sys.executable, str(record / "probe-162787.py")],
       "cwd": str(root / "v12/python"), "status": "pending",
       "guard": {"cap_seconds": 300.0, "spent_seconds_before": spent,
                 "remaining_seconds_before": remaining,
                 "expected_seconds": expected, "margin_seconds": margin,
                 "timeout_seconds": timeout}, "log": "review-run-162787-1.log"}
ledger = {"work": "W161230", "claim": 162787, "authority": "M161614",
          "cap_seconds": 300.0, "prior_ledger": "review-ledger-162696.json",
          "prior_reviewer_seconds": spent, "runs": [run],
          "python": sys.version, "jsonschema": importlib.metadata.version("jsonschema"),
          "qualification": "Deterministic research, not pinned4.26.0 final acceptance"}
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
ledger["reviewer_remaining_seconds"] = 300.0 - ledger["reviewer_spent_seconds"]
path.write_text(json.dumps(ledger, indent=2) + "\n")
print(json.dumps(ledger))
