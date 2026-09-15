"""Bounded review probe: observe two imports, then read their real receipt chains."""
import json
from pathlib import Path
from tests.tools import test_scheduler_trace as T
from baton_v12.integration import reconciliation
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures

record = Path(__file__).resolve().parent
results = []
for order, method in [('a_before_c', 'test_the_opened_edge_and_one_integrator_serialize_four_jobs'), ('c_before_a', 'test_the_alternate_schedule_reaches_the_same_completions')]:
    case = T.TheComposedOwnersSupplyAuthorizedTransitions(method)
    case.setUp()
    original = case.b_and_terminal
    read_terminal = case.terminal_receipts
    pending = []
    def defer_receipts(held, trace, job_id):
        pending.append(job_id)
    case.terminal_receipts = defer_receipts
    def continue_then_read(held, trace):
        original(held, trace)
        deployment = case.case.deployment_of(held.composed)
        seen = trace.__dict__.setdefault('_seen', set())
        def tick():
            sweep(held.job, held.composed, now=fixtures.NOW)
            trace._tick += 1
            case.observed(held, trace, trace._tick, case.FOUR, seen)
        for _ in range(12):
            tick()
            if len(deployment.judges) == 3:
                break
        assert len(deployment.judges) == 3, len(deployment.judges)
        result_id = next(iter(deployment.judges))[0]
        result = reconciliation.result_of(deployment.integration, result_id)
        second = result['job_id']
        assert second not in pending
        for execution in list(deployment.judges.values()):
            case.case.judgment_turn(held, execution)
        for _ in range(12):
            tick()
            if case.case.states_for(held.job, held.composed, second)['integration'] == 'completed':
                break
        result = reconciliation.result_of(deployment.integration, result_id)
        assert result['state'] == 'imported', result['state']
        trace.result(result_id, **{key: result.get(key) for key in T.scheduler_trace.RESULT_CONTEXT})
        # Receipt readback happens after ALL observed sweeps. Preserve actual
        # timestamps and append the earlier import chain before the later one.
        assert len(pending) == 1
        read_terminal(held, trace, pending[0])
        case.proposal_receipts(held, trace, second, result['derived_proposal_id'], trace._tick)
        case._review_trace = trace
        case._review_completed = pending + [second]
    case.b_and_terminal = continue_then_read
    try:
        getattr(case, method)()
        artifact = case._review_trace.artifact(T.SOURCES)
        violations = T.scheduler_trace.validate(artifact)
        assert not violations, violations
        path = record / ('review-159828-' + order + '.json')
        path.write_text(json.dumps(artifact, indent=2)+'\n')
        results.append({'order': order, 'completed_integrations': case._review_completed, 'census': case.completion_census(artifact), 'ticks': case._review_trace._tick, 'violations': violations, 'artifact': path.name})
    finally:
        case.doCleanups()
print(json.dumps(results, indent=2))
