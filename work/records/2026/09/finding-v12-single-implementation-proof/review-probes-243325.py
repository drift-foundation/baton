import sys, pathlib, signal, json, time, tempfile, contextlib, io
from unittest import mock
ROOT=pathlib.Path('/home/sl/src/baton')
HERE=ROOT/'work/records/2026/09/finding-v12-single-implementation-proof'
sys.path[:0]=[str(HERE),str(ROOT/'v12/python/src'),str(ROOT/'v12/python')]
import baseline, snapshot_242687 as builder
from test_baseline import BaselineCase
started=time.perf_counter()
results={}
for mode in ('sigint','keyboard_interrupt'):
    case=BaselineCase()
    case.setUp()
    real=baseline._cleanups
    calls=[]
    def interrupted(*args,**kwargs):
        if not calls:
            calls.append({'turned_at_interrupt':len(case.turned)})
            if mode=='sigint': signal.raise_signal(signal.SIGINT)
            else: raise KeyboardInterrupt('progress read interrupted')
        return real(*args,**kwargs)
    try:
        with mock.patch.object(baseline,'_cleanups',interrupted):
            try:
                _,outcome,_,_=case.supervised()
                raised=False
            except baseline.SupervisorInterrupted as exc:
                outcome=exc.outcome
                raised=True
        results[mode]={'raised':raised,'injection':calls,'turned_after':len(case.turned),'outcome':outcome}
    finally:
        case.tearDown()
        case.doCleanups()
results['seconds']=time.perf_counter()-started
for value in results.values():
    if isinstance(value,dict) and 'outcome' in value:
        assert value['raised'] and value['turned_after']==0
        assert value['outcome']['stopped']=='interrupted'
(HERE/'review-probes-243325.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({k:({'raised':v['raised'],'turned_after':v['turned_after'],'stopped':v['outcome']['stopped']} if isinstance(v,dict) else v) for k,v in results.items()}))
