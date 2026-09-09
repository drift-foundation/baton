import contextlib
import hashlib
import json
import signal
import sqlite3
import time
from pathlib import Path
from unittest.mock import patch
from tests.job_manager.test_review_driver import TheImplementationResumeReadsRealCommittedCustody as Case
from baton_v12.integration import driver

start=time.monotonic()
signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError("five-second review budget")))
signal.setitimer(signal.ITIMER_REAL,5)
case=Case()
case.setUp()
report={"work":"W121793","claim":121826}
try:
    held=case.implemented()
    expected=held['ended']['published']
    case.reopened()
    case.publication.retained.clear()
    case.publisher.target='c3'*20
    connection=case.control._connection
    before=connection.total_changes
    statements=[]
    denied=[]
    forbidden={sqlite3.SQLITE_INSERT,sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE,sqlite3.SQLITE_TRANSACTION,sqlite3.SQLITE_SAVEPOINT,sqlite3.SQLITE_CREATE_TABLE,sqlite3.SQLITE_DROP_TABLE,sqlite3.SQLITE_ALTER_TABLE,sqlite3.SQLITE_ATTACH,sqlite3.SQLITE_DETACH}
    def authorize(action,*args):
        if action in forbidden:
            denied.append([action,*args])
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    connection.set_authorizer(authorize)
    connection.set_trace_callback(statements.append)
    try:
        with contextlib.ExitStack() as stack:
            for method in ('publish','proposal','canonical_target'):
                stack.enter_context(patch.object(case.publisher,method,side_effect=AssertionError('external '+method)))
            stack.enter_context(patch.object(driver,'retain_proposal',side_effect=AssertionError('serving proposal retention')))
            answer=driver.publication_for_attempt(case.control,attempt_id=case.ATTEMPT)
            assert answer['published']==expected
            assert answer==driver.publication_for_attempt(case.control,attempt_id=case.ATTEMPT)
            assert driver.publication_for_attempt(case.control,attempt_id='absent-attempt') is None
            assert not denied
            assert connection.total_changes==before
        report.update(successful=True,exact_ordinary_publication_recovered=True,absent_attempt_none=True,publisher_and_retention_forbidden=True,sql_writes_and_transactions_denied=True,denied_attempts=denied,sql_statements=len(statements),fixture='Actual consumer ordinary ending, real frozen output/assignment/retention/publication; reopened manager and forgotten selector; deterministic physical/Authority transports')
    finally:
        connection.set_authorizer(None)
        connection.set_trace_callback(None)
finally:
    case.tearDown()
    case.doCleanups()
    signal.setitimer(signal.ITIMER_REAL,0)
    report['seconds']=time.monotonic()-start
    with Path(__file__).with_suffix('.json').open('x') as output:
        json.dump(report,output,indent=2)
    print(json.dumps(report,indent=2))
