"""Public-owner probes using a disposable Job fixture; no live store access."""
import json
from unittest.mock import patch
from baton_v12.job_manager import JobStore, submit, documents, projection
from baton_v12.job_manager import execution_limits as limits
from tests.job_manager.fixtures import JobManagerCase, NOW, UUID
from tests.job_manager.test_execution_limits import limited

case=JobManagerCase()
case.setUp()
try:
    store=JobStore.open(case.job_path, authority_uuid=UUID, incarnation='review-156392', clock=case.clock)
    case.addCleanup(store.close)
    document=limited(verification_command_seconds=120)
    first=submit(store,document)
    def status():
        return projection.status(store,case.operations(),observed_at=NOW)['jobs'][0]['execution_limits']
    before=status()
    changed=dict(limits.BOUNDARIES)
    changed['provider_turn']=('provider_turn_seconds',7200)
    with patch.dict(limits.BOUNDARIES,changed):
        after=status()
        replay=submit(store,document)
    assert first == replay
    print(json.dumps({'unchanged_job_replayed':True,'before':before,'after_default_change':after},sort_keys=True))
    null_document=limited()
    null_document['jobs'][0]['execution_limits']=None
    print(json.dumps({'explicit_null_normalized':documents.owned_submission(null_document)},sort_keys=True))
finally:
    case.doCleanups()
