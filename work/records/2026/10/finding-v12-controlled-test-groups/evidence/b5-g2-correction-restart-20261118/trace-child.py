"""G2 diagnostic: run the useful-correction scenario with the prepare child's exceptions printed to its log."""
import json, sys
from unittest import mock
from tests.tools import correction_restart_trace as proof

anchor = "    status=reconciliation_entry.main(place=launch,command_root=command,event_root=events)"
assert anchor in proof.MANAGED_CHILD
injected = proof.MANAGED_CHILD.replace(anchor,
"""    import traceback
    _ow=reconciliation_entry.PreparationAgent.func.work if hasattr(reconciliation_entry.PreparationAgent,'func') else None
    _cls=reconciliation_entry.PreparationAgent.func
    for _name in ('work','consider'):
        _orig=getattr(_cls,_name)
        def _traced(self,*a,_orig=_orig,_name=_name,**k):
            try:return _orig(self,*a,**k)
            except BaseException:
                print('[child] '+_name+' raised',file=sys.stderr);traceback.print_exc();sys.stderr.flush();raise
        setattr(_cls,_name,_traced)
    import reconciliation_task as _task, os as _os
    _oe=_task.export_derived_objects
    def _te(repository, derived, states, destination, seconds):
        verified=_os.path.join(_os.path.dirname(repository),'exported-candidate')
        try:return _oe(repository, derived, states, destination, seconds)
        finally:
            try:
                a=_task.measure(verified); b=_task.measure(states['combined']['path'])
                print('[child] measure exported vs combined: only-exported',sorted(set(a)-set(b)),'only-combined',sorted(set(b)-set(a)),'differing',sorted(k for k in set(a)&set(b) if a[k]!=b[k]),file=sys.stderr)
                for k in sorted(set(a)^set(b)): print('[child]  ',k,'exported=',a.get(k),'combined=',b.get(k),file=sys.stderr)
                for k in sorted(k for k in set(a)&set(b) if a[k]!=b[k]): print('[child]  ',k,'exported=',a[k],'combined=',b[k],file=sys.stderr)
                print('[child] combined listing',sorted(_os.path.relpath(_os.path.join(r,f),states['combined']['path']) for r,_,fs in _os.walk(states['combined']['path']) for f in fs),file=sys.stderr)
            except Exception as e: print('[child] measure diff failed',repr(e),file=sys.stderr)
            sys.stderr.flush()
    _task.export_derived_objects=_te
    _of=baton_worker._faulted
    def _tf(*a,**k):
        print('[child] _faulted code',a[6:] ,k,file=sys.stderr);sys.stderr.flush();return _of(*a,**k)
    baton_worker._faulted=_tf
    _oh=baton_worker.handle
    def _th(*a,**k):
        try:return _oh(*a,**k)
        except BaseException:
            print('[child] handle raised',file=sys.stderr);traceback.print_exc();sys.stderr.flush();raise
    baton_worker.handle=_th
    status=reconciliation_entry.main(place=launch,command_root=command,event_root=events)
    print('[child] main returned',status,file=sys.stderr)""")
with mock.patch.object(proof, "MANAGED_CHILD", injected):
    world = proof.World()
    try:
        world.setUp()
        try:
            observed = world.run_scenario()
            print("SCENARIO VALIDATED:", proof.validate(observed))
        except AssertionError as failure:
            text = str(failure)
            try:
                doc = json.loads(text)
            except ValueError:
                print(text[:4000]); raise SystemExit(1)
            print("FAILURE:", doc.get("failure"), "tick", doc.get("tick"))
            for child in doc.get("children", []):
                print("--- child", child["runtime_id"], "exit", child["exit_status"])
                print(child["log"])
            print("--- preparation:", json.dumps(doc.get("preparation"), indent=1)[:3000])
            raise SystemExit(1)
    finally:
        world.doCleanups()
