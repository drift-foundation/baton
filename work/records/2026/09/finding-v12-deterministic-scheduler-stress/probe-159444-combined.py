"""W103525 claim159444: the COMBINED two-repository / two-effective-slot setup,
asked of the legal public fixture seams. Owner 159440 ordered this first.

Four shapes are offered, each through `held_configuration` and then a real
serving sweep. Nothing is inserted; every answer is an owner's own."""
import copy, json, sys, traceback
sys.path[:0] = ["src", "tools", "."]
from tests.tools import test_scheduler_trace as T
from baton_v12.job_manager import sweep, episodes
from baton_v12.job_manager.submission import stage_rows
from baton_v12.job_manager.scheduler import allocation_of
from tests.job_manager import fixtures


def producers(case, held):
    answer = {}
    for row in stage_rows(held.job):
        if row["kind"] != "implementation":
            continue
        live = episodes.live_of(held.job, row["stage_id"])
        attempt = (episodes.attempting(row, live)["attempt_id"]
                   if live else None)
        allocation = allocation_of(held.job, attempt) if attempt else None
        answer[row["stage_id"]] = (allocation or {}).get("worker_id")
    return answer


def attempt(name, build):
    case = T.TheComposedOwnersSupplyAuthorizedTransitions(
        "test_four_jobs_two_teams_claim_three_producers_at_once")
    case.setUp()
    try:
        held = build(case)
        print("==", name, "SERVED", json.dumps(producers(case, held)))
    except Exception as failed:
        print("==", name, "REFUSED", type(failed).__name__)
        print("   ", str(getattr(failed, "message", failed))[:400])
    finally:
        case.doCleanups()


def two_repositories(case):
    """C and D on the SECOND repository, each declaring that repository's base.

    `traversing` binds every Job to one canonical target because the Authority
    holds one target revision. This asks for the other shape directly: C and D
    keep their own producers but nominate `second_source` and declare
    `second_base`, which is the two-repository half of the contract.
    """
    case.four_works()
    case.current_policy()
    given = case.four_jobs(own_workers=True)
    by_id = {one["worker_id"]: one for one in given["workers"]}
    for job in ("job-c", "job-d"):
        worker = by_id["implementation-worker-" + job[-1]]
        worker["deployment"]["nominated_source"] = case.case.second_source
        for binding in given["job_bindings"]:
            if binding["job_id"] == job:
                binding["line_declared_base"] = case.case.second_base
                binding["canonical_target_id"] = "target-b"
    from baton_v12.job_manager import submit

    job, control, composed = case.case.serving_two(**given)
    submit(job, case.four_submission())
    held = T.SimpleNamespace(job=job, control=control, composed=composed)
    for _ in range(7):
        sweep(job, composed, now=fixtures.NOW)
    return held


def two_repositories_two_slots(case):
    """THE COMBINED CONTRACT: two repositories AND two producer records.

    C names A's producer as its source and D names B's, so the deployment holds
    two implementation records for four Jobs -- and B's producer nominates the
    second repository, so the two repositories are still there.
    """
    from baton_v12.job_manager import submit

    case.four_works()
    case.current_policy()
    given = case.four_jobs(own_workers=False)
    by_id = {one["worker_id"]: one for one in given["workers"]}
    by_id["implementation-worker-b"]["deployment"]["nominated_source"] = \
        case.case.second_source
    for binding in given["job_bindings"]:
        if binding["job_id"] in ("job-b", "job-d"):
            binding["line_declared_base"] = case.case.second_base
            binding["canonical_target_id"] = "target-b"
    job, control, composed = case.case.serving_two(**given)
    submit(job, case.four_submission())
    held = T.SimpleNamespace(job=job, control=control, composed=composed)
    for _ in range(7):
        sweep(job, composed, now=fixtures.NOW)
    return held


for name, build in (("four Jobs over TWO REPOSITORIES", two_repositories),
                    ("TWO REPOSITORIES and TWO SLOTS",
                     two_repositories_two_slots)):
    attempt(name, build)
