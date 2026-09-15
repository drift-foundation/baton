"""Configured A/B launches through actual serving and observation factories.

Read-only ControlStore is reopened publicly. JobStore has no public read-only
opener: retain its already-open current-schema handle and reject writes during
observation. This does not claim a new read-only Job opener or fresh process.
"""
import contextlib,copy,hashlib,json,pathlib,sqlite3
from unittest.mock import patch
from tests.tools import test_stage_execution as fixtures
from baton_v12.authority import Authority
from baton_v12.integration import IntegrationStore
from baton_v12.job_manager import documents,stages_of,episodes_of
from baton_v12.worker_manager import ControlStore,launch
from tools import stage_execution as stage

class Configured(fixtures.TwoBoundJobsTraverseServingAndCorrection):
    def both_jobs(self):
        document=copy.deepcopy(super().both_jobs());document['schema']=documents.SUBMISSION_SCHEMA
        for job in document['jobs']:
            job['execution_limits']={'provider_turn_seconds':31 if job['job_id']=='job-a' else 67,
                                     'verification_command_seconds':29 if job['job_id']=='job-a' else 43}
        return document

case=Configured()
try:
    case.setUp();held=case.coding()
    stages={}
    for job_id in ('job-a','job-b'):
        row=next(one for one in stages_of(held.job,job_id) if one['kind']=='implementation')
        stages[job_id]=dict(row,**{key:value for key,value in episodes_of(held.job,row['stage_id'])[-1].items() if key not in row})
    expected={job_id:held.composed.observe_exchange(value) for job_id,value in stages.items()}
    assert all(value is not None and value.get('state')!='unreadable' for value in expected.values()),expected
    document=case.composed_document(line_declared_base=case.base,**case.traversing())
    held.composed.close();held.control.close()
    protected=[pathlib.Path(name) for name in (case.job_path,case.control_path,case.authority_path,case.integration_store)]
    def hashes():
        return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.exists()}
    before=hashes();changes=held.job._connection.total_changes;captured=[]
    denied={sqlite3.SQLITE_INSERT,sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE,sqlite3.SQLITE_CREATE_TABLE,
            sqlite3.SQLITE_DROP_TABLE,sqlite3.SQLITE_ALTER_TABLE,sqlite3.SQLITE_CREATE_INDEX,sqlite3.SQLITE_DROP_INDEX}
    held.job._connection.set_authorizer(lambda action,*args:sqlite3.SQLITE_DENY if action in denied else sqlite3.SQLITE_OK)
    case.addCleanup(held.job._connection.set_authorizer,None)
    original=launch.adopt
    def adopting(*args,**kwargs):
        answered=original(*args,**kwargs)
        assert answered is not None
        context=answered.document['job_execution'];assert context==kwargs['job_execution']
        bounds=context['execution_limits']['boundaries'];job=context['job_id']
        assert bounds['provider_turn']['seconds']==(31 if job=='job-a' else 67)
        assert bounds['ordinary_verification']['seconds']==(29 if job=='job-a' else 43)
        captured.append({'job_id':job,'attempt_id':context['attempt_id'],'boundaries':bounds})
        return answered
    with ControlStore.open_readonly(case.control_path,incarnation='review-readonly',clock=lambda:fixtures.NOW) as control,contextlib.ExitStack() as guards:
        for owner,name in ((Authority,'open'),(Authority,'session'),(IntegrationStore,'open'),(stage,'operations_from'),
                           (stage.scheduler,'activate_pool'),(stage.review_cycles,'create_line'),(stage.single_worker,'worker_preflight')):
            guards.enter_context(patch.object(owner,name,side_effect=AssertionError('observation acted: '+name)))
        guards.enter_context(patch.object(launch,'adopt',side_effect=adopting))
        for _ in range(2):
            reader=stage.observation_from(document,held.job,control,checkout=case.checkout)
            for job_id in ('job-a','job-b','job-a'):
                assert reader.observe_exchange(stages[job_id])==expected[job_id]
    assert held.job._connection.total_changes==changes
    assert hashes()==before
    print(json.dumps({'case':'real-configured-readonly-adoption','observed':captured,'database_bytes_unchanged':True,
                      'job_writes_rejected':True,'control_public_readonly_open':True,'serving_closed':True,
                      'limits':'already-open Job handle; no fresh process, absent-artifact or full serving reopen proof'},indent=2))
finally:
    case.doCleanups()
