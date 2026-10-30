"""Reviewer counterexamples; real token store, deterministic fake engine only."""
import json
from tests.manager.test_authoring_enforcement import LateLaunch, UnboundLaunch, ATTEMPT
from baton_v12.worker_manager import tokens

results = []
for cause in ('deadline', 'operator-cancellation', 'recovery'):
    case = LateLaunch('test_token_bound_before_attempt_attachment_is_stopped_but_held')
    case.setUp()
    try:
        lane = case.lane()
        if cause == 'deadline':
            case.clock.advance(240)
        elif cause == 'operator-cancellation':
            lane.stopping.set()
        else:
            lane = case.lane()
        report = lane.tick()['attempts'][ATTEMPT]
        results.append({'cause': cause, 'stopping': lane.stopping.is_set(),
                        'engine_calls': case.engine.calls, 'cancellations': case.cancellations,
                        'observation': report['observation'], 'revoked': case.current()['revoked'],
                        'returned': case.current()['returned']})
        assert lane.stopping.is_set()
        assert report['observation']['state'] == 'running'
        assert not case.cancellations
        assert all(argv[1] != 'stop' for argv, seconds in case.engine.calls)
    finally:
        case.tearDown()
        case.doCleanups()

case = UnboundLaunch('test_expired_unbound_launch_stays_revoked_and_has_no_invented_stop_target')
case.setUp()
try:
    lane = case.lane()
    case.clock.advance(240)
    lane.tick()
    # An already-entered launch is not subject to Operations._dispatch's
    # check again. Exercise its public bind/admission cut after durable halt.
    tokens.bind_container(case.store, case.token, 'runtime-1', launch=case.operation)
    tokens.admit_activation(case.store, case.token, container='runtime-1')
    report = lane.tick()['attempts'][ATTEMPT]
    results.append({'cause': 'late-bind-and-activation-after-halt',
                    'stopping': lane.stopping.is_set(), 'token': case.current(),
                    'observation': report['observation'], 'cancellations': case.cancellations})
    assert case.current()['activating']
    assert report['observation']['state'] == 'running'
finally:
    case.tearDown()
    case.doCleanups()
print(json.dumps(results, indent=2))
