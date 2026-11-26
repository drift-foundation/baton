"""Project named owner-facing assignments from the same snapshot as their executions."""
from . import documents


def _stage(job, phase, execution, states):
    job_id = job["job_id"]
    doc = phase["document"]
    gates = [documents.dependency_gate(stage_id=f"{job_id}/{key}", state=states[key], open=states[key] == "completed")
             for key in doc["depends_on"]]
    if execution:
        stage, = execution["stages"]
        stage = dict(stage)
    else:
        stage = dict(episode=None, offer_id=None, attempt_id=None, episodes=[], corrections=0,
                     allocation=None, allocations=[], receipts=[], deferral=None, runtime=None,
                     exchange=None, artifacts=None, state="queued", work_id=doc["work_id"],
                     profile_name=doc["profile_name"], profile_digest=doc["profile_digest"])
    state = phase["state"]
    if state in ("exceptional", "completed"):
        stage["state"] = state
    elif stage["state"] == "completed":
        stage["state"] = "answering"  # The research custody check is still outstanding.
    elif any(not gate["open"] for gate in gates):
        stage["state"] = "blocked"
    if not stage["artifacts"] and phase["result"]:
        stage["artifacts"] = phase["result"].get("artifacts")
    stage.update(job_id=job_id, stage_id=f'{job_id}/{phase["phase"]}', kind=doc["kind"], gates=gates,
                 selected_at=phase["selected_at"], settled_at=phase["settled_at"], result=phase["result"],
                 execution_job_id=phase["execution_job_id"], execution_cancellation=execution.get("cancellation") if execution else None)
    return documents.stage_status(**stage)


def combine(jobs, owner_jobs):
    ordinary = {job["job_id"]: job for job in jobs}
    manual = []
    for job in owner_jobs:
        states = {phase["phase"]: phase["state"] for phase in job["phases"]}
        stages = []
        for phase in job["phases"]:
            execution = ordinary.pop(phase["execution_job_id"], None)
            stages.append(_stage(job, phase, execution, states))
        manual.append(documents.job_status(job_id=job["job_id"], submission_id=None,
                                           input_digest=None, policy_digest=None, test_scope=[], terminal_policy="owner-close",
                                           execution_limits=None, stages=stages, cancellation=None, mode="MANUAL",
                                           lifecycle=job["lifecycle"], budget=job["budget"], created_at=job["created_at"],
                                           closed_at=job["closed_at"]))
    return list(ordinary.values()) + manual
