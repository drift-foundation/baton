import json
import os
from pathlib import Path
import threading
from unittest.mock import patch
from tests.job_manager.test_recovery import OneAbandonedCorrectionEpisodeIsReplaced as Case
from baton_v12.job_manager import JobStore, episodes
from baton_v12.worker_manager import ControlStore

case = Case()
case.setUp()
results = {}
ready = threading.Event()
start = threading.Event()
arrived_at_begin = threading.Event()
original = JobStore.transact

def other():
    try:
        with JobStore.open(os.path.join(case.root, 'jobs.sqlite3'),
                           authority_uuid=case.jobs.authority_uuid,
                           incarnation='independent-second', clock=case.clock) as jobs:
            with ControlStore.open(os.path.join(case.root, 'control.sqlite3'),
                                   incarnation='independent-second', clock=case.clock) as custody:
                jobs._connection.set_trace_callback(
                    lambda sql: arrived_at_begin.set() if sql == 'BEGIN IMMEDIATE' else None)
                ready.set()
                assert start.wait(1), 'first action did not start'
                results['second'] = episodes.restart_abandoned_correction(
                    jobs, custody, job_id='job-a', attempt_id=case.abandoned_attempt,
                    generation=2)
    except BaseException as ex:
        results['error'] = repr(ex)
        ready.set()

def holding(store, operation_id, kind, signature, action):
    if store is not case.jobs or kind != episodes.RESTART_KIND:
        return original(store, operation_id, kind, signature, action)
    def inside(connection):
        results['first_holds_transaction'] = connection.in_transaction
        start.set()
        assert arrived_at_begin.wait(1), 'second did not reach BEGIN while first held the lock'
        results['second_begin_during_first_action'] = connection.in_transaction
        return action(connection)
    return original(store, operation_id, kind, signature, inside)

try:
    case.abandoned()
    runner = threading.Thread(target=other)
    runner.start()
    assert ready.wait(1), 'second connections did not open'
    with patch.object(JobStore, 'transact', holding):
        results['first'] = case.restart()
        runner.join(1)
    assert not runner.is_alive(), 'second did not finish'
    assert 'error' not in results, results
    assert results['second'] == results['first'], results
    results['identical_answers'] = True
    results['endings'] = sum(row['ended_state'] == 'abandoned-after-exclusion'
                             for row in case.history('implementation'))
    assert results['endings'] == 1
finally:
    case.doCleanups()
Path(__file__).with_suffix('.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps({key: value for key, value in results.items()
                  if key not in ('first', 'second')}, indent=2))
