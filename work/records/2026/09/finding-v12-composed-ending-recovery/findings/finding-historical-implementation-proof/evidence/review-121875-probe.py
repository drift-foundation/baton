import contextlib,copy,json,signal,sqlite3,time
from pathlib import Path
from unittest.mock import patch
from tests.job_manager import test_review_driver as t
from baton_v12.integration import driver
start=time.monotonic()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('eight-second review budget')))
signal.setitimer(signal.ITIMER_REAL,8)
case=t.TheImplementationResumeReadsRealCommittedCustody();case.setUp()
results={}
def observe(call):
    try:
        result=call()
        return {'accepted':True,'published':result['published']}
    except Exception as e:
        return {'accepted':False,'exception':type(e).__name__,'message':str(e)}
try:
    held=case.implemented();later=case.later_round(held);case.reopened()
    case.publication=t._RealPublication(case,case.publisher)
    case.publisher.target='c3'*20
    connection=case.control._connection
    denied=[]
    def authorizer(action,*args):
        if action in (sqlite3.SQLITE_INSERT,sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE,sqlite3.SQLITE_TRANSACTION,sqlite3.SQLITE_SAVEPOINT):
            denied.append(action);return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    connection.set_authorizer(authorizer)
    try:
        with case.no_remote(held):
            ordinary=case.resume(held)
            assert ordinary==held['ended']
            assert ordinary['checkpoint_id']!=later['checkpoint_id']
            results['cold_actual_later_round']={'whole_return_equal':True,'no_external_or_sql_act':not denied}
            receipt=case.publication.published_of(attempt_id=case.ATTEMPT)
            variants={}
            for key,value in [('proposal_id','proposal-elsewhere'),('proposal_manifest_digest','sha256:'+'3'*64),('candidate_digest','c3'*20),('target','c3'*20)]:
                changed=copy.deepcopy(receipt);changed[key]=value;variants['receipt_'+key]=changed
            for key,value in [('candidate_digest','c3'*20),('target','c3'*20),('input_digest','sha256:'+'3'*64),('policy_digest','sha256:'+'3'*64)]:
                changed=copy.deepcopy(receipt);changed['published'][key]=value;variants['answer_'+key]=changed
            for key in ['assignment','published']:
                changed=copy.deepcopy(receipt)
                assignment=changed[key] if key=='assignment' else changed[key]['assignment_ref']
                assignment['generation']=True
                variants[key+'_bool_generation']=changed
            for name,value in variants.items():
                with patch.object(case.publication,'published_of',return_value=value):
                    results[name]=observe(lambda:case.resume(held))
            assert not denied
    finally:connection.set_authorizer(None)
finally:
    case.tearDown();case.doCleanups();signal.setitimer(signal.ITIMER_REAL,0)
    report={'work':'W120425','claim':121875,'results':results,'seconds':time.monotonic()-start}
    with Path(__file__).with_suffix('.json').open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({'seconds':report['seconds'],'results':{k:({x:y for x,y in v.items() if x!='published'}) for k,v in results.items()}},indent=2))
