"""Deterministic consumer diagnostic; use test_baseline_bindings on PYTHONPATH."""
import json
import time
from test_baseline_bindings import TheFreshPacket
from tools import single_worker
case = TheFreshPacket("test_fresh_positive_one_proposal_without_context")
started = time.monotonic()
try:
    case.setUp()
    _, outcome, job, control = case.supervised(packet=case.packet_for())
    print(json.dumps({k: outcome.get(k) for k in ("state", "held_because", "stage_states", "cancellation", "cleanup", "workload")}, default=str))
    print("failures", [(single_worker.attempt_preparation_failure_of(control,a), single_worker.attempt_start_failure_of(control,a)) for a in outcome["admitted_attempts"]])
finally:
    case.doCleanups()
    print("elapsed", time.monotonic()-started)
