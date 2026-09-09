"""Read durable integration output and observe ordinary scheduling only."""
import json
from pathlib import Path
from unittest.mock import patch

from baton_v12.integration import entries_of, runtime
from tests.tools.test_stage_execution import OrdinaryTerminalLifecycle

case = OrdinaryTerminalLifecycle("test_one_job_completes_correction_integration_and_terminal_handoff")
evidence = {}
try:
    case.setUp()
    held = case.accepted_correction()
    case.connect_integration(held)
    evidence["start"] = case.tick(held)
    [started] = [one for one in evidence["start"]["started"] if one["stage_id"] == "job-a/integration"]
    evidence["worker_exit"] = case.integration_turn(held, started["attempt_id"])
    deployment = case.deployment_of(held)
    delivery = runtime.adopt_delivery(deployment.integration_root, attempt_id=started["attempt_id"], workspace_group=deployment.workspace_group)
    assignment = runtime.published_assignment(delivery)
    evidence["worker_observation"] = runtime.observed_delivery(delivery, assignment)
    case.engine.stopped = True
    with patch.object(held.composed.integrator, "run", wraps=held.composed.integrator.run) as consumer:
        evidence["ticks"] = [case.tick(held) for _ in range(3)]
        evidence["integration_consumer_calls_after_result"] = consumer.call_count
    evidence["stage_states"] = case.states(held.job, held.composed)
    evidence["entries"] = entries_of(deployment.integration, deployment.given["canonical_target_id"])
    evidence["work"] = case.projected()
    evidence["target_harness"] = Path(case.source, "harness.py").read_text()
finally:
    Path(__file__).with_name("probe.json").write_text(json.dumps(evidence, indent=2, default=str) + "\n")
    case.doCleanups()
print(json.dumps(evidence, indent=2, default=str))
