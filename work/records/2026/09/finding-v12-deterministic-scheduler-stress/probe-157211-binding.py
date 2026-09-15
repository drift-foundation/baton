"""W103525 claim157211: which FOUR-JOB shape the public configuration owner
actually binds. Two candidate shapes are offered to `held_configuration` and
whatever it says is recorded. No durable state is written."""
import copy, sys, traceback
sys.path[:0] = ["src", "tools", "."]

from tests.tools import test_stage_execution as composed
from tools import stage_execution

THIRD_WORK, FOURTH_WORK = "0000000a-W3", "0000000a-W4"

case = composed.TwoBoundJobsTraverseServingAndCorrection(
    "test_two_accepted_jobs_share_one_integrator_one_at_a_time")
case.setUp()

given = case.two_jobs()
held = {one["worker_id"]: one for one in given["workers"]}


def shape_shared():
    """FOUR Jobs on the EXISTING two producers and two reviewers: two teams,
    two repositories, two implementation and two review slots exactly as the
    plan's sentence reads."""
    answer = copy.deepcopy(given)
    answer["job_bindings"] = answer["job_bindings"] + [
        {"job_id": "job-c", "job_work_id": THIRD_WORK,
         "review_work_id": THIRD_WORK,
         "line_declared_base": case.base, "canonical_target_id": "target-a",
         "source_worker_id": "implementation-worker"},
        {"job_id": "job-d", "job_work_id": FOURTH_WORK,
         "review_work_id": FOURTH_WORK,
         "line_declared_base": case.second_base,
         "canonical_target_id": "target-b",
         "source_worker_id": "implementation-worker-b"}]
    return answer


def shape_own_workers():
    """FOUR Jobs each with its OWN producer and reviewer, two per repository:
    four implementation and four review records, two nominated sources."""
    answer = copy.deepcopy(given)
    workers = list(answer["workers"])
    for job, work, base, target, source_of, who in (
            ("job-c", THIRD_WORK, case.base, "target-a", "implementation-worker",
             "third"),
            ("job-d", FOURTH_WORK, case.second_base, "target-b",
             "implementation-worker-b", "fourth")):
        producer = copy.deepcopy(held[source_of])
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
        answer["job_bindings"] = answer["job_bindings"] + [
            {"job_id": job, "job_work_id": work, "review_work_id": work,
             "line_declared_base": base, "canonical_target_id": target,
             "source_worker_id": producer["worker_id"]}]
    answer["workers"] = workers
    return answer


for name, build in (("shared two slots", shape_shared),
                    ("own worker per job", shape_own_workers)):
    try:
        document = build()
    except Exception:
        print("== %s: FIXTURE FAILED" % name)
        traceback.print_exc()
        continue
    try:
        stage_execution.held_configuration(
            case.composed_document(**document), checkout=case.checkout)
        print("== %s: BOUND" % name)
    except Exception as failed:
        print("== %s: REFUSED %s" % (name, type(failed).__name__))
        print("   ", str(getattr(failed, "message", failed))[:400])
