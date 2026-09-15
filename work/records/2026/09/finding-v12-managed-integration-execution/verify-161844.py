"""Bounded review with carried slice1 spending; no product mutation."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

record = Path(__file__).resolve().parent
root = record.parents[4]
prior = json.loads((record / "review-ledger-161769.json").read_text())
spent_before = prior["prior_reviewer_seconds"] + sum(r["elapsed_seconds"] for r in prior["runs"])
path = record / "review-ledger-161844.json"
if path.exists():
    raise SystemExit("Refuse overwrite")
ledger = {"work": "W161230", "claim": 161844, "authority": "M161614",
          "cap_seconds": 300.0, "prior_ledger": "review-ledger-161769.json",
          "prior_reviewer_seconds": spent_before, "runs": [],
          "python": sys.version, "jsonschema": importlib.metadata.version("jsonschema"),
          "qualification": "Pinned4.26.0 final acceptance remains outstanding"}
commands = [[sys.executable, "-m", "unittest", "tests.manager.test_reconciliation_worker",
             "tests.manager.test_contracts_inventory"],
            [sys.executable, str(record / "probe-161769.py")],
            [sys.executable, str(record / "probe-161844.py")]]
for number, argv in enumerate(commands, 1):
    spent = spent_before + sum(r["elapsed_seconds"] for r in ledger["runs"])
    remaining = 300.0 - spent
    expected, margin, timeout = 5.0, 2.0, min(30.0, remaining - 2.0)
    if expected + margin > remaining or not 0 < timeout < remaining:
        raise SystemExit("Budget guard refused")
    run = {"argv": argv, "cwd": str(root / "v12/python"),
           "guard": {"cap_seconds": 300.0, "spent_seconds_before": spent,
                     "remaining_seconds_before": remaining, "expected_seconds": expected,
                     "margin_seconds": margin, "timeout_seconds": timeout},
           "log": f"review-run-161844-{number}.log", "status": "pending"}
    ledger["runs"].append(run)
    path.write_text(json.dumps(ledger, indent=2) + "\n")
    with (record / run["log"]).open("wb") as output:
        start = time.monotonic()
        try:
            result = subprocess.run(argv, cwd=run["cwd"],
                                    env=dict(os.environ, PYTHONPATH="src:tools:."),
                                    stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
            run.update(status="finished", exit_code=result.returncode)
        except subprocess.TimeoutExpired:
            run.update(status="timeout", exit_code=None)
        finally:
            run["elapsed_seconds"] = time.monotonic() - start
    ledger["reviewer_spent_seconds"] = spent_before + sum(r["elapsed_seconds"] for r in ledger["runs"])
    ledger["reviewer_remaining_seconds"] = 300.0 - ledger["reviewer_spent_seconds"]
    path.write_text(json.dumps(ledger, indent=2) + "\n")
    print(json.dumps(run))
print(json.dumps({"spent": ledger["reviewer_spent_seconds"],
                  "remaining": ledger["reviewer_remaining_seconds"]}))
