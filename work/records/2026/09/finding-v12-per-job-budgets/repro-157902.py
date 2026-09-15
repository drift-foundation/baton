"""Measure literal delivery bytes and actual reopen sweep answers independently."""
import json,pathlib
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
from baton_v12.worker_manager import launch
from baton_v12.job_manager import sweep,stages_of
case=tests.AReopenedServingKeepsBothJobsLaunchesUntouched('test_a_reopened_serving_adopts_the_same_two_deliveries')
original=launch.adopt
snapshots={};answers=[]
def adopting(*args,**kwargs):
    result=original(*args,**kwargs)
    if result is not None and result.document.get('job_execution'):
        key=result.document['job_execution']['job_id']
        snapshots.setdefault(key,[]).append((result.place,pathlib.Path(result.place).read_bytes()))
    return result
def ticking(job,composed,**kwargs):
    result=sweep(job,composed,**kwargs)
    answers.append({'answer':result,'stages':{name:stages_of(job,name) for name in ('job-a','job-b')}})
    return result
try:
    case.setUp()
    with patch.object(launch,'adopt',adopting),patch('baton_v12.job_manager.sweep',ticking):
        case.test_a_reopened_serving_adopts_the_same_two_deliveries()
    assert sorted(snapshots)==['job-a','job-b'],snapshots.keys()
    for name,items in snapshots.items():
        assert len(items)>1,(name,len(items))
        assert all(item==items[0] for item in items),(name,'delivery bytes changed')
    print(json.dumps({'literal_delivery_adoptions':{name:len(items) for name,items in snapshots.items()},'all_delivery_places_and_bytes_identical':True,'sweeps':answers},default=str,indent=2))
finally:
    case.doCleanups()
