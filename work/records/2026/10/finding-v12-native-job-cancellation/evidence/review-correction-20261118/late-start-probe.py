"""Deterministic interruption after adapter start, before attachment."""
import json
from unittest import mock
from baton_v12.worker_manager import oci
from tests.tools.test_job_cancellation_command import InstalledCancellation

class Interrupted(BaseException):
    pass
case = InstalledCancellation()
case.setUp()
try:
    original = oci.OciAdapter.start
    def lost_reply(adapter, request, **kw):
        original(adapter, request, **kw)
        raise Interrupted()
    try:
        with mock.patch.object(oci.OciAdapter, 'start', lost_reply):
            case.drive(case.jobs, case.composed, 'implementation', 'waiting')
    except Interrupted:
        pass
    print('BEFORE', json.dumps(case.axes(), sort_keys=True))
    case.cancel()
    replies = [case.tick() for _ in range(3)]
    print(json.dumps({'cancellations':[r.get('cancelled') for r in replies], 'axes':case.axes(), 'stops':len(case.stops()), 'report':case.report()},indent=2))
    direct = case.composed.cancel_attempt(attempt_id=case.attempt_id(), reason='the operator ends this Job before its deadline')
    print('EXISTING OWNER', json.dumps({'stops':len(case.stops()),'answer':direct},sort_keys=True))
finally:
    case.tearDown()
    case.doCleanups()
