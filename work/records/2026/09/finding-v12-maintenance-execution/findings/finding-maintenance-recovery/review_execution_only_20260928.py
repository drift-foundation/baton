"""Independent completion probe: scans forbidden after fixture preparation."""
from contextlib import ExitStack
from unittest.mock import patch
from tests.manager import test_intake as fixture
from baton_v12.worker_manager import intake, runtime_lane
from baton_v12.worker_manager import workspaces
case = fixture.RetainedAndCompleteAreDifferentEndings('test_material_kept_by_policy_ends_retained')
case.setUp()
try:
    case.retained_ready('discard-after-intake')
    case.ended()
    with ExitStack() as stack:
        for owner, name in ((intake, 'inaccessible_output'), (intake, '_output_root_identities'),
                            (workspaces, 'discard_execution_roots')):
            stack.enter_context(patch.object(owner, name, side_effect=AssertionError('forbidden completion act: '+name)))
        args = dict(attempt_id=fixture.ATTEMPT, retention_policy_digest=fixture.RETENTION)
        answer = intake.authorize_cleanup(case.store, case.port, fixture.Custodian(), **args)
        assert answer['cleanup'] == 'retained', answer
        assert runtime_lane(case.store, fixture.ATTEMPT)['holder'] is None
        assert intake.authorize_cleanup(case.store, case.port, fixture.Custodian(), **args) == answer
        record = intake.historical_writer_cessation(case.store, answer['operation'])
        assert record['state'] == 'absent' and record['exit_status'] is None
        print('PASS: scan/removal sentinels untouched; retained; lane released; exact replay; unknown exit recorded')
finally:
    case.tearDown()
