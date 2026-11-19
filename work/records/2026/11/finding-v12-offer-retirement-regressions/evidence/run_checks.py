"""Explicit deterministic selections for W385251; no engine/build/full suite."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
PYTHON = "/home/sl/.local/state/baton-v12-venv/bin/python"
IDS = """tests.job_manager.test_scheduling
 tests.job_manager.test_accepted_offer_retirement
 tests.manager.test_offers
 tests.tools.test_dogfood_operator.TheArcMaterializesBetweenActivationAndRuntimeCreation
 tests.tools.test_job_task_delivery.TwoRequestedJobsThroughOneServingLoop
 tests.tools.test_retry_task_lineage.TheRetriedJobIsServedItsOwnTask
 tests.tools.test_stage_execution.TheRestartOverAnAdvancedPoolPreservesSettledHistory
 tests.tools.test_stage_execution.AAcceptedPRSeedsTheSuccessorOnTheSameStores
 tests.tools.test_stage_execution.ANewJobCreatedAfterAFollowsTheAdvancedTarget
 tests.tools.test_parallel_runner.TheDeclaredInputsCoverWhatTheTestsRead""".split()
mode = sys.argv[1]
if mode == "focused":
    command = [PYTHON, "-m", "unittest", "-v", *IDS]
    limit = 180
elif mode == "tools-pure":
    command = [PYTHON, "tools/parallel_test.py", "--group", "tools-pure", "--account", "--keep-going", "--jobs", "8", "--summary", str(HERE / "tools-pure-ledger.json")]
    limit = 900
else:
    raise SystemExit("select focused or tools-pure")
env = dict(os.environ, PYTHONPATH="src:.", TMPDIR="/var/tmp", BATON_V12_DISK_ROOT="/var/tmp", PYTHONDONTWRITEBYTECODE="1")
start = time.monotonic()
with (HERE / (mode + "-final.log")).open("w") as log:
    result = subprocess.run(["timeout", "--kill-after=10s", str(limit) + "s", *command], cwd=ROOT / "v12/python", env=env, stdout=log, stderr=subprocess.STDOUT)
record = {"command": command, "cwd": "v12/python", "timeout_seconds": limit, "kill_grace_seconds": 10, "exit_code": result.returncode, "wall_seconds": time.monotonic() - start, "environment_overrides": {k:env[k] for k in ("PYTHONPATH", "TMPDIR", "BATON_V12_DISK_ROOT", "PYTHONDONTWRITEBYTECODE")}}
(HERE / (mode + "-run.json")).write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record))
raise SystemExit(result.returncode)
