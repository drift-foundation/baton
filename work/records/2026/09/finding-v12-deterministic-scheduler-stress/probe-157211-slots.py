"""W103525 claim157211: does the SHARED-SLOT four-Job shape actually SERVE?

The PLAN asks for four Jobs over "two implementation and two review slots".
Binding is not serving, so this drives the shared shape through the real owners
and records what they say. Nothing is inserted and no receipt is fabricated."""
import copy, sys, traceback
sys.path[:0] = ["src", "tools", "."]

from tests.tools import test_stage_execution as composed
from baton_v12.authority import Authority
from baton_v12.job_manager import submit
from tests.job_manager import fixtures

THIRD_WORK, FOURTH_WORK = "0000000a-W3", "0000000a-W4"

case = composed.TwoBoundJobsTraverseServingAndCorrection(
    "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
case.setUp()

authority = Authority.open(case.authority_path,
                           expected_authority_uuid=case.config["authority_uuid"])
try:
    from baton_v12.authority import V12
    for index, work in enumerate((THIRD_WORK, FOURTH_WORK)):
        authority.create_work(work, "baton.impl", contract=V12,
                              operation_id="create-four-job-%d" % index)
    print("WORKS CREATED", [authority.project_work(w)["route"]
                            for w in (THIRD_WORK, FOURTH_WORK)])
finally:
    authority.dispose()

given = case.traversing()
import os as _os
OWN = _os.environ.get("FOUR_JOB_OWN_WORKERS") == "1"
if OWN:
    # THE CONTRAST: C and D get their OWN producers and reviewers, two per
    # repository. Everything else -- the Works, the submission, the edge, the
    # ticks -- is identical, so what differs is the worker binding alone.
    import copy as _copy
    held_by_id = {one["worker_id"]: one for one in given["workers"]}
    workers = list(given["workers"])
    for job, work, source_of, who in (
            ("job-c", THIRD_WORK, "implementation-worker", "third"),
            ("job-d", FOURTH_WORK, "implementation-worker-b", "fourth")):
        producer = _copy.deepcopy(held_by_id[source_of])
        producer["worker_id"] = "implementation-worker-" + job[-1]
        case.bound_worker(producer, work)
        producer["deployment"]["participant"] = "baton." + who
        producer["deployment"]["principal"] = "principal:baton." + who
        workers.append(producer)
        workers.append(case.role_worker(
            "review", work, "review-worker-" + job[-1],
            participant="baton.reviewer-" + job[-1],
            principal="principal:baton.reviewer-" + job[-1],
            review_route=case.INTEGRATION_ROUTE))
    given["workers"] = workers
given["job_bindings"] = given["job_bindings"] + [
    {"job_id": "job-c", "job_work_id": THIRD_WORK, "review_work_id": THIRD_WORK,
     "line_declared_base": case.base, "canonical_target_id": "target-a",
     "source_worker_id": ("implementation-worker-c" if OWN
                          else "implementation-worker")},
    {"job_id": "job-d", "job_work_id": FOURTH_WORK,
     "review_work_id": FOURTH_WORK, "line_declared_base": case.second_base,
     "canonical_target_id": "target-b",
     "source_worker_id": ("implementation-worker-d" if OWN
                          else "implementation-worker-b")}]

job, control, composed_deployment = case.serving_two(**given)
held = fixtures.submission(jobs=[
    copy.deepcopy(case.submission["jobs"][0]),
    fixtures.job("job-b",
                 input_digest=case.manifest_over(
                     composed.SECOND_WORK, case.shared_task_bytes)["manifest_digest"],
                 policy_digest=fixtures.POLICY_DIGEST,
                 stages=[fixtures.stage("implementation", composed.SECOND_WORK,
                                        depends_on=[{"job_id": "job-a",
                                                     "kind": "review"}]),
                         fixtures.stage("review", composed.SECOND_WORK,
                                        depends_on=[{"job_id": "job-b",
                                                     "kind": "implementation"}]),
                         fixtures.stage("integration", composed.SECOND_WORK,
                                        depends_on=[{"job_id": "job-b",
                                                     "kind": "review"}])]),
    fixtures.job("job-c",
                 input_digest=case.manifest_for(THIRD_WORK)["manifest_digest"],
                 policy_digest=fixtures.POLICY_DIGEST,
                 stages=[fixtures.stage("implementation", THIRD_WORK),
                         fixtures.stage("review", THIRD_WORK,
                                        depends_on=[{"job_id": "job-c",
                                                     "kind": "implementation"}])]),
    fixtures.job("job-d",
                 input_digest=case.manifest_for(FOURTH_WORK)["manifest_digest"],
                 policy_digest=fixtures.POLICY_DIGEST,
                 stages=[fixtures.stage("implementation", FOURTH_WORK),
                         fixtures.stage("review", FOURTH_WORK,
                                        depends_on=[{"job_id": "job-d",
                                                     "kind": "implementation"}])])])
submit(job, held)
print("SUBMITTED four jobs")

from baton_v12.job_manager import sweep
for tick in range(3):
    try:
        answer = sweep(job, composed_deployment, now=fixtures.NOW)
        print("TICK", tick, "ok")
    except Exception as failed:
        print("TICK", tick, "REFUSED", type(failed).__name__)
        print("   ", str(getattr(failed, "message", failed))[:500])
        break

from baton_v12.job_manager.submission import stage_rows
from baton_v12.job_manager.scheduler import allocation_of
from baton_v12.job_manager import episodes
for row in stage_rows(job):
    live = episodes.live_of(job, row["stage_id"])
    attempt = (episodes.attempting(row, live)["attempt_id"] if live else None)
    allocation = allocation_of(job, attempt) if attempt else None
    print("STAGE", row["stage_id"], row["kind"],
          "worker=", (allocation or {}).get("worker_id"))

# WHY C AND D ARE NOT ALLOCATED: the owner's own recorded refusal, if any.
from baton_v12.job_manager.scheduler import allocation_refusal_of
for row in stage_rows(job):
    live = episodes.live_of(job, row["stage_id"])
    if not live:
        continue
    attempt = episodes.attempting(row, live)["attempt_id"]
    refusal = allocation_refusal_of(job, attempt)
    if refusal:
        print("REFUSAL", row["stage_id"], str(refusal)[:300])

from baton_v12.job_manager.projection import stage_states
states = stage_states(job, composed_deployment)
import json as _json
print("STATES", _json.dumps(states, default=str)[:1400])
