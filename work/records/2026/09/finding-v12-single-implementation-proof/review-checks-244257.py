from pathlib import Path
import sys,json,time,unittest,tempfile
ROOT=Path('/home/sl/src/baton');HERE=ROOT/'work/records/2026/09/finding-v12-single-implementation-proof'
sys.path[:0]=[str(HERE),str(ROOT/'v12/python/src'),str(ROOT/'v12/python')]
import test_successor_packet as tests
from unittest import mock
start=time.perf_counter()
with (HERE/'review-tests-244257.log').open('w') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(tests.TheCorrectedImageIsWhatThePacketBinds))
checks={'checks':result.testsRun,'errors':len(result.errors),'failures':len(result.failures)}
# Replay the referenced preparation prefix only, stopping BEFORE Authority.open.
old=(HERE/'OPERATOR-SUCCESSOR-243284.md').read_text()
block=old.split('## Step 5a',1)[1].split('```python',1)[1].split('```',1)[0]
prefix=block.split('authority = Authority.open',1)[0]
with tempfile.TemporaryDirectory(prefix='review-244257-preparation-') as temp:
    sel=Path(temp)/'selections.json'
    sel.write_bytes((HERE/'SELECTIONS-SUCCESSOR-244216.json').read_bytes())
    prefix=prefix.replace('SEL = "/home/sl/baton-runs/single-implementation-243284/selections.json"','SEL = '+repr(str(sel)))
    try:exec(compile(prefix,'referenced-step5a-prefix','exec'),{});failure=None
    except AssertionError as exc:failure=str(exc)
    checks['step5a_refusal_after_selecting_new_file']=failure
    assert failure=='/home/sl/baton-runs/single-implementation-244216/db/authority.sqlite3'
checks['seconds']=time.perf_counter()-start
(HERE/'review-checks-244257.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks))
