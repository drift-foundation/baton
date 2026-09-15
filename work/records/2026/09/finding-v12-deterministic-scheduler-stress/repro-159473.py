"""Independent binding readback and exact eligibility refusal; no owner mutation."""
import json
from tests.tools import test_scheduler_trace as T
from baton_v12.job_manager.submission import stage_rows
import stage_execution

for method in ("test_four_jobs_do_bind_and_serve_across_two_repositories",
               "test_two_repositories_do_not_make_two_slots_servable"):
    case = T.TheComposedOwnersSupplyAuthorizedTransitions(method)
    case.setUp()
    original = case.served
    captured = []
    def served(given):
        held = original(given)
        captured.append(held)
        return held
    case.served = served
    try:
        getattr(case, method)()
        held = captured[0]
        deployment = case.case.deployment_of(held.composed)
        workers = {row['worker_id']: row for row in deployment.given['workers']}
        bindings = deployment.given['job_bindings']
        sources = {row['job_id']: str(workers[row['source_worker_id']]['deployment']['nominated_source']) for row in bindings}
        assert len(set(sources.values())) == 2, sources
        result = {'case': method, 'sources': sources, 'allocations': case.producers_of(held)}
        if method.endswith('two_slots_servable'):
            refusals = {}
            for row in stage_rows(held.job):
                if row['stage_id'] not in ('job-c/implementation', 'job-d/implementation'):
                    continue
                try:
                    stage_execution._job_workers(deployment, row)
                except Exception as exc:
                    detail = str(getattr(exc, 'message', exc))
                    assert 'no worker this deployment configures' in detail, detail
                    refusals[row['stage_id']] = detail
                else:
                    raise AssertionError('Unexpected eligible worker: ' + row['stage_id'])
            assert len(refusals) == 2
            result['eligibility_refusals'] = refusals
        print(json.dumps(result, sort_keys=True))
    finally:
        case.doCleanups()
