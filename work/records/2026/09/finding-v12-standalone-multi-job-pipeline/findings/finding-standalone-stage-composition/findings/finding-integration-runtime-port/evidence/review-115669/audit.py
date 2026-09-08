"""Bounded delta probes: active preparation replay and failed witness read.

Budget: two disposable attempts, under 10 seconds. Deterministic engine and
synthetic credentials only; no suite, real daemon, network or provider call.
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

root = Path.cwd()
here = Path(__file__).resolve().parent
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager.attempts import attempt_runtime_of
from tests.tools.test_integration_worker import TheWholeIntegrationRunsThroughThisPort, ATTEMPT
from tools import integration_worker

candidate = {}
for relative in ["tools/integration_worker.py", "tests/tools/test_integration_worker.py", "tools/parallel_test.py", "src/baton_v12/integration/driver.py", "src/baton_v12/integration/__init__.py", "tests/integration/test_driver.py"]:
    name = "v12/python/" + relative
    data = (root / name).read_bytes()
    target = here / "candidate" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    candidate[name] = hashlib.sha256(data).hexdigest()
gate = Path("/tmp/w110774-gate5.txt").read_bytes()
(here / "gate.txt").write_bytes(gate)

def attempt(action):
    try:
        action()
        return {"succeeded": True}
    except Exception as error:
        return {"succeeded": False, "exception": type(error).__name__, "message": str(error)}

def lifecycle(home):
    state = home.read_state(ATTEMPT)
    return None if state is None else {key: state.get(key) for key in ("runtime_id", "lifecycle_state")}

probes = {}
case = TheWholeIntegrationRunsThroughThisPort("run")
try:
    case.setUp()
    port, answer = case.started()
    probes["initial_runtime"] = attempt_runtime_of(case.world.manager, ATTEMPT)["execution_runtime"]
    probes["initial_credential_lifecycle"] = lifecycle(case.credential_home)
    minted_before = len(case.minted)
    home_type = type(case.credential_home)
    real_discard = home_type.discard_orphan
    with mock.patch.object(home_type, "discard_orphan", autospec=True, side_effect=real_discard) as discarded:
        probes["prepare_running_attempt"] = attempt(lambda: port.prepare(case.stage(), None))
        probes["discard_calls_on_running_attempt"] = discarded.call_count
    probes["additional_provider_calls"] = len(case.minted) - minted_before
    probes["credential_lifecycle_after_reprepare"] = lifecycle(case.credential_home)
    probes["runtime_after_reprepare"] = attempt_runtime_of(case.world.manager, ATTEMPT)["execution_runtime"]
    with mock.patch.object(integration_worker.runtime, "prior_runtime_witness", side_effect=ContractRefusal("refused", "precondition", "review witness read unavailable")):
        probes["refresh_witness_failure"] = attempt(lambda: port.refresh(ATTEMPT))
    probes["marker_after_witness_failure"] = port.may_continue(answer["assignment"])
finally:
    case.doCleanups()

case = TheWholeIntegrationRunsThroughThisPort("run")
try:
    case.setUp()
    def unavailable(name, reference):
        raise ContractRefusal("policy", "denied", "review synthetic provider unavailable")
    port = case.port(credential_provider=unavailable)
    probes["unavailable_preparation"] = attempt(lambda: port.prepare(case.stage(), None))
    from baton_v12.integration import entries_of
    probes["entries_after_unavailable_preparation"] = len(entries_of(case.world.coordinator, case.world.target))
    probes["runtime_after_unavailable_preparation"] = attempt_runtime_of(case.world.manager, ATTEMPT)["execution_runtime"]
finally:
    case.doCleanups()

result = {"claim": 115669, "at": datetime.now(timezone.utc).isoformat(), "candidate": candidate, "gate_sha256": hashlib.sha256(gate).hexdigest(), "gate_tail": gate.decode().splitlines()[-4:], "probes": probes}
(here / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
