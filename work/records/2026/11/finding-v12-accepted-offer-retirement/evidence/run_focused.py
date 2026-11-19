"""Bounded deterministic W385222 verification; no engine/build/live selection."""
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[6]
PYTHON = "/home/sl/.local/state/baton-v12-venv/bin/python"
IDS = """tests.job_manager.test_accepted_offer_retirement
 tests.job_manager.test_delegation
 tests.job_manager.test_recovery
 tests.job_manager.test_job_cancellation
 tests.manager.test_offers
 tests.job_manager.test_scheduling
 tests.job_manager.test_job_control
 tests.tools.test_single_worker.TheManagerClaimSessionMapsOneRefusalAndNothingElse
 tests.tools.test_stage_execution.TheWrongRouteClaimDefersInsteadOfStoppingTheSweep
 tests.tools.test_stage_execution.OneRefusedClaimLeavesEveryOtherJobAlone
 tests.tools.test_stage_execution.TwoIndependentlyBoundWorkersShareOneSweep
 tests.tools.test_parallel_runner.TheRealRegistryDescribesTheRealTree
 tests.tools.test_parallel_runner.TheGroupsAreAnExactPartitionOfTheRealTree""".split()
command = [PYTHON, "-m", "unittest", "-v", *IDS]
env = dict(os.environ, PYTHONPATH="src:.", TMPDIR="/var/tmp", BATON_V12_DISK_ROOT="/var/tmp", PYTHONDONTWRITEBYTECODE="1")
start = time.monotonic()
with Path(__file__).with_name("focused-final.log").open("w") as log:
    result = subprocess.run(command, cwd=ROOT / "v12/python", env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
record = {"command": command, "cwd": "v12/python", "timeout_seconds": 180, "exit_code": result.returncode, "wall_seconds": time.monotonic() - start, "environment_overrides": {key:env[key] for key in ("PYTHONPATH", "TMPDIR", "BATON_V12_DISK_ROOT", "PYTHONDONTWRITEBYTECODE")}}
Path(__file__).with_name("focused-final-run.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record))
raise SystemExit(result.returncode)
