"""Read-only review probe of retained candidate; only new fixture stores mutate."""
from pathlib import Path
import json
import sys
import tempfile
from unittest.mock import patch
candidate = Path(sys.argv[1])
sys.path[:0] = [str(candidate / 'v12/python'), str(candidate / 'v12/python/src')]
from baton_v12.job_manager import JobStore, submit, sweep, projection, delegation
from tests.job_manager.fixtures import UUID, NOW, FakeOperations, submission
place = Path(tempfile.mkdtemp(prefix='w319114-boundary-'))
store = JobStore.open(str(place / 'jobs'), authority_uuid=UUID,
                      incarnation='probe', clock=lambda: NOW)
operations = FakeOperations()
submit(store, submission())
sweep(store, operations, now=NOW)
real = delegation.observation_of
seen = []
def observation(*args, **kwargs):
    seen.append(store._connection.in_transaction)
    return real(*args, **kwargs)
try:
    with patch.object(delegation, 'observation_of', observation):
        with store.read_snapshot():
            projection.status(store, operations, observed_at=NOW)
    print(json.dumps(dict(fixture=str(place), observation_transaction_states=seen,
                          released_after=not store._connection.in_transaction)))
    assert seen and all(seen), 'candidate no longer reproduces; revalidate'
finally:
    store.close()
