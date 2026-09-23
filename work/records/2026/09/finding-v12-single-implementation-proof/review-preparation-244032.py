from pathlib import Path
import sys,json,tempfile,time
from unittest import mock
ROOT=Path('/home/sl/src/baton'); HERE=ROOT/'work/records/2026/09/finding-v12-single-implementation-proof'
sys.path[:0]=[str(HERE),str(ROOT/'v12/python/src'),str(ROOT/'v12/python')]
from test_successor_packet import TheSuccessorSelectionsCompose
from baton_v12.authority import Authority
real=tempfile.mkdtemp
start=time.perf_counter()
def named(suffix=None,prefix=None,dir=None):
    return real(suffix=suffix or '',prefix='single-implementation-243284-review-'+(prefix or ''),dir=dir)
case=TheSuccessorSelectionsCompose()
with mock.patch.object(tempfile,'mkdtemp',named): case.setUp()
try:
    chosen=case.selections()
    chosen['participants']['work_id']=case.work.rsplit('-W',1)[0]+'-W9999'
    sel=Path(case.root)/'preparation-selections.json'
    sel.write_text(json.dumps({'compose':chosen}))
    doc=(HERE/'OPERATOR-SUCCESSOR-243284.md').read_text()
    block=doc.split('## Step 5a',1)[1].split('```python',1)[1].split('```',1)[0]
    block=block.replace('SEL = "/home/sl/baton-runs/single-implementation-243284/selections.json"','SEL = '+repr(str(sel)))
    block=block.replace('BASE = "<the HEAD the command bound -- the same value>"','BASE = '+repr(case.base))
    exec(compile(block,'OPERATOR-SUCCESSOR-243284.md:step5a','exec'),{})
    authority=Authority.open(chosen['instance']['authority_store'],expected_authority_uuid=case.config['authority_uuid'])
    try:
        result={'work':authority.project_work(chosen['participants']['work_id']),'canonical_target':authority.canonical_target(),'expected_base':case.base,'store':chosen['instance']['authority_store']}
        assert result['canonical_target']==case.base
        assert result['work'] is not None
    finally: authority.dispose()
    result['seconds']=time.perf_counter()-start
    (HERE/'review-preparation-244032.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
finally:
    case.tearDown(); case.doCleanups()
