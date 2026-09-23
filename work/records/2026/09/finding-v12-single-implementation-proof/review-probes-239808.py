"""Reviewer probes: disposable fixtures and read-only entrypoint refusal only."""
import copy
import json
import os
from pathlib import Path
import subprocess
import time
from unittest import mock

import baseline
import baseline_bindings
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import submit
from test_baseline_bindings import TheGeneratedPacketDrivesOneImplementation

HERE = Path(__file__).resolve().parent
started = time.monotonic()
observed = {}

# No import path is specified in OPERATOR step 3. The published selections
# remain placeholders; compose imports packages before reading those operands.
environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
environment.pop("PYTHONPATH", None)
command = ["python3", "baseline_bindings.py", "--selections",
           "SELECTIONS-239528.json", "--base", "a" * 40,
           "--run-root", "/tmp/w239528-review-no-write-239808"]
answer = subprocess.run(command, cwd=HERE, env=environment,
                        capture_output=True, text=True, timeout=20)
observed["documented_composer_without_implicit_PYTHONPATH"] = {
    "command": command, "exit_code": answer.returncode,
    "stdout": answer.stdout, "stderr": answer.stderr}
assert answer.returncode != 0
assert "No module named 'baton_v12'" in answer.stderr

# Real generated submissions and the public JobStore submission boundary.
# No engine operation or provider is invoked by either submission.
case = TheGeneratedPacketDrivesOneImplementation(
    "test_the_generated_deployment_produces_one_attributed_proposal")
try:
    case.setUp()
    first, _places = case.generate()
    choices = case.selections()
    choices["run_id"] += "-fresh"
    second = baseline_bindings.compose(
        base=case.base, run_root=str(Path(case.root) / "second-run"), **choices)
    job, _control = case.stores("review-collision")
    submit(job, first["submission.json"])
    try:
        submit(job, second["submission.json"])
    except ContractRefusal as failure:
        reason = str(failure)
    else:
        raise AssertionError("expected duplicate Job identity refusal")
    observed["fresh_run_id_same_job_store"] = {
        "first_submission": first["submission.json"]["submission_id"],
        "second_submission": second["submission.json"]["submission_id"],
        "first_job": first["submission.json"]["jobs"][0]["job_id"],
        "second_job": second["submission.json"]["jobs"][0]["job_id"],
        "refusal": reason}
    assert "already recorded by another submission" in reason
finally:
    case.doCleanups()

# Scope of accounting: an old Job is not an attempt of the selected Job.
status = {"jobs": [
    {"job_id": "old-job", "stages": [{"kind": "implementation",
      "state": "exceptional", "attempt_id": "old-runtime-attempt",
      "episodes": []}]},
    {"job_id": "new-job", "stages": [{"kind": "implementation",
      "state": "completed", "attempt_id": "new-runtime-attempt",
      "episodes": []}]}]}
with mock.patch("baton_v12.job_manager.status", return_value=copy.deepcopy(status)):
    attempts, states, limits = baseline._attempts_of(None, None, "new-job")
assert attempts == {"new-runtime-attempt": "implementation"}
observed["accounting_scope"] = {"input_status": status, "attempts": attempts,
                               "states": states, "limits": limits}
observed["seconds"] = time.monotonic() - started
observed["scope"] = "No deployed store, live engine, provider, or recovery."
(HERE / "review-probes-239808.json").write_text(
    json.dumps(observed, indent=2, sort_keys=True) + "\n")
print(json.dumps(observed, indent=2, sort_keys=True))
