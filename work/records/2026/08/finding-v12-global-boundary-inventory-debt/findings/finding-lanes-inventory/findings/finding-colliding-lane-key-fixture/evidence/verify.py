"""Bounded fixture controls, followed by the lane-only regression sweep."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = next(path for path in HERE.parents if (path / "v12/python").is_dir())
environment = dict(os.environ, PYTHONPATH="src", PYTHONDONTWRITEBYTECODE="1")
started = time.monotonic()
results = []
sweep = '''
from tests.manager.test_boundary_inventory import EveryProbeProvesItArrived
case = EveryProbeProvesItArrived()
try:
    case.setUp()
    keys = sorted(case.lane_probes())
finally:
    case.doCleanups()
assert keys
for key in keys:
    try:
        case.setUp()
        label, probe = case.lane_probes()[key]
        case.assertIn(key[1], label)
        case.refusing(label, probe)
        print(repr(key), "PASS")
    finally:
        case.doCleanups()
print("lane probes:", len(keys))
'''
for name, arguments in (
        ("focused", ["-m", "unittest", "-v", "tests.manager.test_boundary_inventory.TheCollidingLaneKeyProbeReachesAdoption"]),
        ("lanes", ["-c", sweep])):
    command = [sys.executable, *arguments]
    before = time.monotonic()
    completed = subprocess.run(command, cwd=ROOT / "v12/python", env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=max(0.1, 15 - (before - started)))
    (HERE / (name + ".txt")).write_text(completed.stdout)
    results.append({"name": name, "command": command, "seconds": time.monotonic() - before, "exit_code": completed.returncode})
    print(completed.stdout)
    if completed.returncode:
        break
(HERE / "verification.json").write_text(json.dumps({"budget_seconds": 15, "seconds": time.monotonic() - started, "results": results}, indent=2) + "\n")
sys.exit(any(result["exit_code"] for result in results))
