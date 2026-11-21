"""Review probes against exact candidate via real frozen-output fixture; no Git."""
import json,os,sys,time
from tests.manager.test_attempt_failure_cause import TheWorkerDeclaredAxisIsComposedFromSEALEDEVIDENCE as Case
from baton_v12.worker_manager import failure_cause
case=Case('test_a_PROVIDER_TIMEOUT_is_attributable_with_its_bound_and_its_verification');case.setUp()
try:
    kind=sys.argv[1]
    if kind=='missing-verification':
        doc=json.loads(case.result_document());del doc['verification'];case.freeze(case.candidate(json.dumps(doc).encode()));print(json.dumps(case.values(failure_cause.declaration_of(case.composed()))))
    elif kind=='nested-json':
        raw=b'{"schema":"baton.dogfood-proposal/2","padding":'+b'['*2000+b'0'+b']'*2000+b'}'
        case.freeze(case.candidate(raw))
        try:print(json.dumps(case.composed()))
        except Exception as error:print(type(error).__name__+': '+str(error));raise
    elif kind=='fifo':
        case.freeze(case.candidate(case.result_document()));place=os.path.join(case.custody,'result.json');os.unlink(place);os.mkfifo(place)
        print('sealed regular result replaced with FIFO; calling public observation',flush=True);case.composed();print('returned')
finally:case.doCleanups()
