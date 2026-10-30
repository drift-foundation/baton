"""Does a REAL composed diagnostic's absent_records reach the report?

Drives the accepted producer through the real status seam -- no hand-built
diagnostic -- and compares the report's `absent_records` with the producer's
own `failure_cause.absent_of` over the same document.
"""
import json, sys
sys.path[:0] = ['src', '.', 'tests/job_manager']
from unittest import TestLoader, TextTestRunner
from tests.tools import test_attempt_diagnostics as suite
from tools import attempt_diagnostics
from baton_v12.worker_manager import failure_cause

case = suite.RealStatusReportSeam('test_real_durable_expiry_reaches_status_and_report_unchanged')
case.setUp()
try:
    case.outcome()
    snapshot = case.snapshot()
    stage = snapshot['jobs'][0]['stages'][0]
    diagnostic = stage['attempt_diagnostics']
    produced = failure_cause.absent_of(diagnostic)
    row = attempt_diagnostics.report(json.dumps(snapshot).encode())['rows'][0]
    reported = tuple(row['absent_records'] or ())
    print(json.dumps({
        'producer_absent_of': list(produced),
        'report_absent_records': list(reported),
        'dropped_by_the_report': [one for one in produced if one not in reported],
        'equal': list(produced) == list(reported),
    }, indent=1))
finally:
    case.doCleanups()
