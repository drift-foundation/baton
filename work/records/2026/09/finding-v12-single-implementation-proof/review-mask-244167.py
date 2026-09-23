from pathlib import Path
import sys,json,time
from unittest import mock
ROOT=Path('/home/sl/src/baton');HERE=ROOT/'work/records/2026/09/finding-v12-single-implementation-proof'
sys.path[:0]=[str(HERE),str(ROOT/'v12/python/src'),str(ROOT/'v12/python')]
from test_baseline import BaselineCase
import claude_agent
start=time.perf_counter();result={}
for mask in (0o022,0o077):
    case=BaselineCase();case.setUp()
    try:
        with mock.patch.object(claude_agent,'PROVIDER_UMASK',mask):
            _,outcome,_,_=case.supervised()
        result[oct(mask)]={'state':outcome['state'],'stopped':outcome['stopped'],'outstanding_cleanup':outcome['outstanding_cleanup']}
    finally:case.tearDown();case.doCleanups()
assert result['0o22']['state']=='held' and result['0o22']['stopped']=='no-progress'
assert result['0o77']['state']=='settled'
result['seconds']=time.perf_counter()-start
(HERE/'review-mask-244167.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
