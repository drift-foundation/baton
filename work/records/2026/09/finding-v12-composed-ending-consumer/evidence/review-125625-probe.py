"""Diagnostic only: contrast ordinary ticks with the missing integration call.

The defect is recorded in takeover-125537/FINDING.md before this stopgap.
This injection is not a production repair or ordinary lifecycle acceptance.
"""
import json
from pathlib import Path
from unittest.mock import patch

from baton_v12.integration import entries_of, runtime
from baton_v12.worker_manager import attempt_activity_of, frozen_output_of
from tests.tools.test_stage_execution import OrdinaryTerminalLifecycle

case = OrdinaryTerminalLifecycle("test_one_job_completes_correction_integration_and_terminal_handoff")
evidence = {}
try:
    case.setUp()
    held = case.accepted_correction()
    case.connect_integration(held)
    evidence["start"] = case.tick(held)
    [started] = [one for one in evidence["start"]["started"] if one["stage_id"] == "job-a/integration"]
    attempt_id = started["attempt_id"]
    evidence["worker_exit"] = case.integration_turn(held, attempt_id)
    deployment = case.deployment_of(held)
    delivery = runtime.adopt_delivery(deployment.integration_root, attempt_id=attempt_id, workspace_group=deployment.workspace_group)
    evidence["worker_result"] = runtime.observed_delivery(delivery, runtime.published_assignment(delivery))
    case.engine.stopped = True
    with patch.object(held.composed.integrator, "run", wraps=held.composed.integrator.run) as consumer:
        evidence["ordinary_tick"] = case.tick(held)
        evidence["ordinary_consumer_calls"] = consumer.call_count
    dispatch = held.composed.dispatch

    def diagnostic_dispatch(stage, job):
        if stage["kind"] == "integration":
            return held.composed.integrator.run(stage, job)
        return dispatch(stage, job)

    with patch.object(held.composed, "dispatch", diagnostic_dispatch):
        evidence["diagnostic_tick"] = case.tick(held)
    evidence["after_driver_stage_states"] = case.states(held.job, held.composed)
    evidence["after_driver_entries"] = entries_of(deployment.integration, deployment.given["canonical_target_id"])
    evidence["after_driver_work"] = case.projected()
    evidence["after_driver_activity"] = attempt_activity_of(held.control, attempt_id)
    evidence["after_driver_frozen_output"] = frozen_output_of(held.control, attempt_id)
    evidence["next_ordinary_tick"] = case.tick(held)
finally:
    Path(__file__).with_suffix(".json").write_text(json.dumps(evidence, indent=2, default=str) + "\n")
    case.doCleanups()
