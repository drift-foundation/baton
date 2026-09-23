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
# Disposable copy of the builder's output namespace. No bound artifact edited.
with tempfile.TemporaryDirectory(prefix='review-243244-builder-') as tmp:
    root=pathlib.Path(tmp)
    source=root/'python'
    (source/'tools').mkdir(parents=True)
    (source/'tools'/'probe.py').write_text('pass\n')
    dossier=root/'dossier'; dossier.mkdir()
    manifest=dossier/'MANAGER-SOURCE-242687.json'
    original='{"path":"preserved-original-snapshot","files":{}}\n'
    manifest.write_text(original)
    with mock.patch.multiple(builder,HERE=dossier,PYTHON=source,SNAPSHOT=root/'fresh-successor',PACKAGES=(('tools','tools'),),ACCEPTED={},SUPERSEDED={}):
        with contextlib.redirect_stdout(io.StringIO()): builder.main()
    results['builder']={'original_manifest_preserved':manifest.read_text()==original,'new_manifest':json.loads(manifest.read_text()),'note':'entire source and output namespace disposable; canonical manifest untouched'}
results['seconds']=time.perf_counter()-started
(HERE/'review-probes-243244.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({k: ({'raised':v['raised'],'injection':v['injection'],'turned_after':v['turned_after'],'state':v['outcome']['state'],'stopped':v['outcome']['stopped']} if k in ('sigint','keyboard_interrupt') else v) for k,v in results.items()},indent=2))
