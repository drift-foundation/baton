"""Reproduce W81115 against the production single-worker composition.

Run from ``v12/python`` with ``PYTHONPATH=src:.``.  The production fixture
starts the exact composition with its recording OCI engine; this probe then
asks the certified Claude adapter's own task reader about the mounted root.
"""

import json
import os
import pathlib
import sys

from baton_v12.job_manager import submit
from tests.tools import test_single_worker as cases
from tools import single_worker


REPOSITORY = pathlib.Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPOSITORY / "v12" / "worker"))

import claude_agent  # noqa: E402


case = cases.TheProductionCompositionIsRestartSafe(methodName="runTest")
case.setUp()
try:
    engine = cases.Engine()
    job, control = case.stores("w81115-missing-inputs")
    submit(job, case.submission)
    operations = case.operations(job, control, engine)
    projected = case.running(job, operations)
    stage = projected["jobs"][0]["stages"][0]
    inputs = os.path.join(case.storage, stage["attempt_id"], "inputs")
    task = os.path.join(inputs, claude_agent.TASK_DOCUMENT)
    source = os.path.join(inputs, claude_agent.SOURCE_ROOT)
    try:
        claude_agent._task(task)
    except claude_agent.TaskRefusal as refusal:
        task_read = str(refusal)
    else:
        task_read = "accepted"
    print(json.dumps({
        "configured_source_destination":
            case.config["input_manifest"]["sources"][0]["destination"],
        "engine_starts": len(engine.starts),
        "source_at_worker_path": os.path.exists(source),
        "stage_state": stage["state"],
        "task_at_worker_path": os.path.exists(task),
        "worker_task_read": task_read,
    }, sort_keys=True))
    operations.close()
finally:
    case.doCleanups()
