"""Probe: drive the pool loop through the implementation ending to the review
stage, with the scripted in-image worker and no version control."""
import json
import os
import subprocess

from tests.tools import test_job_task_delivery as suite
from tests.tools.test_stage_execution import ComposedOneJobCase, _ConcurrentEngine
from tests.job_manager import fixtures
from baton_v12.contracts import digest
from baton_v12.job_manager import creation, reconcile, sweep
from baton_v12.job_manager import status as projected
from tools import single_worker, stage_execution


class Probe(suite.TheCreatedJobRunsThroughThePoolServingLoop):
    quiescing = ComposedOneJobCase.quiescing

    def runTest(self):
        pass


case = Probe()
case.setUp()
try:
    jobs, control = case.stores("pool-review-probe")
    installed = single_worker._held(
        case.worker("implementation")["deployment"])
    answered = case.create(jobs, installed, task_id="pool-review",
                           statement="A reviewed pool task.")
    job_id = answered["job_id"]
    case.engine = case.quiescing()
    composed = stage_execution.operations_from(
        case.composed_document(
            checkpoint_profile=case.config["profile_name"]),
        jobs, control, engine_run=case.engine,
        credential_provider=lambda provider, reference: case.secret,
        clock=lambda: fixtures.NOW, checkout=case.checkout,
        checkpoint_profile=case.profile_seam)
    try:
        case.driven(jobs, composed, job_id)
        stage = case.stage_of(jobs, composed, job_id)
        attempt_id = stage["attempt_id"]
        print("implementation:", case.stages(jobs, composed, job_id))

        # THE IN-IMAGE TURN, scripted: no provider, no version control.
        import baton_worker
        import scripted_agent

        worker = case.worker_of(composed, "implementation")
        roots = dict(worker.stage._prepared[attempt_id]["boundary"]["roots"])
        print("mounted roots:", roots)
        delivered = single_worker.launch.adopt(
            case.config["launch_home"], attempt_id=attempt_id,
            session="session-" + digest(attempt_id)[7:31],
            contract=case.config["launch_contract"], role="implementation",
            transport=single_worker.exchange.EXCHANGE_TRANSPORT,
            job_execution=single_worker.job_execution_reader(jobs)(
                job_id=job_id, attempt_id=attempt_id,
                runtime_input_digest=__import__(
                    "baton_v12.worker_manager",
                    fromlist=["attempts"]).attempts.recorded_input_of(
                        control, attempt_id),
                runtime_policy_digest=case.config["policy_digest"]),
            workspace_group=single_worker.configured_workspace_group(control))
        held = []
        for module, name, value in (
                (baton_worker, "INPUT_ROOT", roots["inputs"]),
                (baton_worker, "OUTPUT_ROOT", roots["workspace"]),
                (scripted_agent, "OUTPUT_ROOT", roots["workspace"])):
            held.append((module, name, getattr(module, name)))
            setattr(module, name, value)
        try:
            print("turn:", baton_worker.serve_exchange(
                scripted_agent.ScriptedAgent(), delivered.document,
                delivered.document["session"],
                delivered.exchange.command_root,
                delivered.exchange.event_root))
        finally:
            for module, name, value in held:
                setattr(module, name, value)

        for tick in range(16):
            report = sweep(jobs, composed, now=fixtures.NOW)
            reconcile(jobs, composed, now=fixtures.NOW)
            states = case.stages(jobs, composed, job_id)
            acts = [(one["act"], one["outcome"],
                     (one.get("detail") or {}).get("message", "")[:150]
                     if isinstance(one.get("detail"), dict) else "")
                    for one in report["acts"]]
            print(tick, states, acts)
            if states.get("review") == "waiting":
                break
        impl = case.stage_of(jobs, composed, job_id)
        print("impl runtime:", json.dumps(impl.get("runtime"), default=str)[:300])
        print("impl exchange:", json.dumps(impl.get("exchange"), default=str)[:400])
        print("impl receipts:", [(r["act"], r["state"]) for r in impl.get("receipts", [])])
        print("impl deferral:", json.dumps(impl.get("deferral"), default=str)[:300])
        review = case.stage_of(jobs, composed, job_id, kind="review")
        print("review stage:", review["state"], review.get("attempt_id"))
        if review.get("attempt_id"):
            place = os.path.join(case.config["workspace_storage"],
                                 review["attempt_id"], "inputs", "task.json")
            print("review root:", os.path.exists(place))
            if os.path.exists(place):
                with open(place, "rb") as reading:
                    print("review task_id:",
                          json.loads(reading.read().decode())["task_id"])
    finally:
        composed.close()
finally:
    case.doCleanups()
