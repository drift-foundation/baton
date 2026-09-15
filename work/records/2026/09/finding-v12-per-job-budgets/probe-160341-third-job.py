"""Why the third Job does not reach its own derived result after the second is
blocked. Read-only intent: the drive is the candidate test's own helper and this
only prints what the owners answer, tick by tick."""
import json

from tests.tools.test_execution_limits import (
    TheComposedHostVerificationUsesTheJobsCeiling as Case)
from baton_v12.integration import queue, reconciliation
from tests.job_manager import fixtures
from tools import stage_execution

case = Case("test_three_jobs_bind_three_ceilings_and_three_tasks")
case.setUp()
try:
    held = case._three_job_serving()
    deployment = case.case.deployment_of(held.composed)
    integration = stage_execution.Integration(deployment)
    commands = [integration.required_tests(one)["argv"]
                for one in ("job-b", "job-c")]
    case._watching(argvs=commands, home=deployment.integration_root,
                   failing=True)
    case.case.drive_job(held.job, held.composed, "job-a", "integration",
                        "integrating")
    attempt = case.case.attempted(held.job, "job-a/integration")["attempt_id"]
    assert case.case.integration_turn(held, attempt) == 0
    case.case.engine.stopped = True
    case.case.drive_job(held.job, held.composed, "job-a", "integration",
                        "completed", ticks=6)
    case.case.engine.stopped = False
    trace = []
    recoveries = []
    for tick in range(40):
        if tick in (12, 20):
            # DOES THE PUBLIC STAGE RECOVERY FREE THE INTEGRATOR that job-b's
            # blocked result left `exceptional`? Asked, not assumed.
            try:
                recoveries.append(held.composed.recover(now=fixtures.NOW))
            except Exception as refused:                   # noqa: BLE001
                recoveries.append({"refused": str(refused)})
        report = case.case.tick(held)
        rows = [dict(one) for one in
                deployment.integration._connection.execute(
                    "SELECT result_id, job_id, state FROM integration_results"
                ).fetchall()]
        states = {one: case.case.states_for(held.job, held.composed, one)
                  .get("integration")
                  for one in ("job-a", "job-b", "job-c")}
        acts = [(one.get("stage_id"), one.get("act"), one.get("outcome"),
                 (one.get("detail") or {}).get("message"))
                for one in report.get("acts", [])]
        trace.append({"tick": tick, "states": states,
                      "results": [(one["job_id"], one["state"])
                                  for one in rows],
                      "commands": len(case.seen),
                      "acts": acts[:4]})
        if len([one for one in rows if one["state"] == "blocked"]) == 2:
            break
    target = queue.target_of(
        deployment.integration,
        reconciliation.result_of(
            deployment.integration,
            [one["result_id"] for one in
             deployment.integration._connection.execute(
                 "SELECT result_id FROM integration_results").fetchall()][0]
        )["canonical_target_id"])
    print(json.dumps({
        "last_five": trace[-3:],
        "recoveries": recoveries,
        "ticks": len(trace),
        "commands": len(case.seen),
        "target_state": target["state"],
        "target_reason": target.get("blocked_reason"),
        "entries": [(one["result_id"][:24], one["state"])
                    for one in queue.entries_of(
                        deployment.integration,
                        target["canonical_target_id"])],
        "retained": [[list(key[0]), list(key[1]), key[3]]
                     for key in stage_execution._host_retention(deployment)],
    }, indent=1, default=str))
finally:
    case.doCleanups()
