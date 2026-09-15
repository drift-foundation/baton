"""Persist cumulative reviewer guard before each bounded verification child."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

record = Path(__file__).resolve().parent
root = record.parents[4]
ledger_path = record / "review-ledger-161686.json"
if ledger_path.exists() and sys.argv[1:] != ["--probe-again"]:
    raise SystemExit("Refuse to overwrite an existing review ledger")
ledger = {"work": "W161230", "claim": 161686, "slice": "slice1",
          "authority": "M161614", "reviewer_cap_seconds": 300.0,
          "prior_reviewer_seconds": 0.0, "runs": [],
          "environment": {"python": sys.version,
                          "jsonschema": importlib.metadata.version("jsonschema"),
                          "qualification": "Pinned jsonschema 4.26.0 required for final acceptance; no install authorized."}}
env = dict(os.environ, PYTHONPATH="src:tools:.")
commands = [
    [sys.executable, "-m", "unittest", "tests.manager.test_reconciliation_worker",
     "tests.manager.test_contracts_inventory"],
    [sys.executable, str(record / "probe-161686.py")],
]
if sys.argv[1:] == ["--probe-again"]:
    ledger = json.loads(ledger_path.read_text())
    commands = commands[1:]
for number, argv in enumerate(commands, len(ledger["runs"]) + 1):
    spent = ledger["prior_reviewer_seconds"] + sum(run["elapsed_seconds"] for run in ledger["runs"])
    remaining = ledger["reviewer_cap_seconds"] - spent
    expected, margin, timeout = 5.0, 2.0, min(30.0, remaining - 2.0)
    if expected + margin > remaining or timeout <= 0 or timeout >= remaining:
        raise SystemExit("Insufficient cumulative allowance")
    run = {"argv": argv, "cwd": str(root / "v12/python"),
           "guard": {"cap_seconds": 300.0, "spent_seconds_before": spent,
                     "remaining_seconds_before": remaining, "expected_seconds": expected,
                     "margin_seconds": margin, "timeout_seconds": timeout},
           "log": f"review-run-161686-{number}.log", "status": "pending"}
    ledger["runs"].append(run)
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n")
    with (record / run["log"]).open("wb") as log:
        start = time.monotonic()
        try:
            result = subprocess.run(argv, cwd=run["cwd"], env=env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=timeout)
            run.update(status="finished", exit_code=result.returncode)
        except subprocess.TimeoutExpired:
            run.update(status="timeout", exit_code=None)
        finally:
            run["elapsed_seconds"] = time.monotonic() - start
    ledger["reviewer_spent_seconds"] = sum(r["elapsed_seconds"] for r in ledger["runs"])
    ledger["reviewer_remaining_seconds"] = 300.0 - ledger["reviewer_spent_seconds"]
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n")
    print(json.dumps(run))
print(json.dumps(ledger["environment"]))
