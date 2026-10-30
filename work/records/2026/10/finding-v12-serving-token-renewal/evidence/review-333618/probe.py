"""Preparation falsification, not token/engine acceptance.
Real supervisor, serve loop and cancellation dispatch; simulated scheduling,
status reads and cancellation adapter. No stores, Git, engine or provider.
"""
import contextlib
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
STAGED = Path('/tmp/w333485-preflight-x4bdpfzp/instance-root')
REPO = Path('/home/sl/src/baton')
PINS = REPO / 'work/records/2026/10/finding-v12-serving-token-renewal/execution-333532/PREPARATION-PINS.json'
pins = json.loads(PINS.read_text())
for relative, expected in pins['manager_files'].items():
    assert hashlib.sha256((STAGED / 'code/v12/python' / relative).read_bytes()).hexdigest() == expected
for relative, expected in pins['supervisor_files'].items():
    assert hashlib.sha256((STAGED / 'supervisor' / relative).read_bytes()).hexdigest() == expected
sys.path[:0] = [str(STAGED/'supervisor'), str(STAGED/'code/v12/python/src'), str(STAGED/'code/v12/python')]
import baseline
import baton_v12.job_manager as api
from baton_v12.job_manager import manager
from baton_v12.worker_manager import attempts

ATTEMPT = 'simulated-attempt-w333485'
RUNTIME = 'simulated-exact-runtime-w333485'
root = Path(tempfile.mkdtemp(prefix='w333485-enforcement-probe-'))
submission = root/'submission.json'
submission.write_text('{}')

def scenario(name, total, turn, sweep_delay, cancel_delay, cancel_fails):
    elapsed = [0.0]
    calls = []
    observed_serve = []
    def advance(seconds):
        elapsed[0] += seconds
    def sweep(*args, **kwargs):
        calls.append({'kind':'simulated-blocking-sweep', 'at':elapsed[0], 'delay':sweep_delay})
        advance(sweep_delay)
        return {}
    class Operations:
        def cancel_attempt(self, *, attempt_id, reason):
            calls.append({'kind':'cancel', 'attempt':attempt_id, 'runtime':RUNTIME, 'at':elapsed[0], 'delay':cancel_delay})
            advance(cancel_delay)
            if cancel_fails:
                raise TimeoutError('simulated cancellation adapter timeout; no cessation observation')
            return {'requested':True}  # acknowledgement deliberately does NOT prove absence
    def serve(*args, **kwargs):
        observed_serve.append({'reclaim_supplied':kwargs.get('reclaim') is not None})
        return manager.serve(*args, **kwargs)
    limits = {'boundaries':{'provider_turn':{'seconds':turn, 'origin':'job'}}}
    states = { 'implementation':'waiting' }
    packet = dict(schema=baseline.FRESH_PACKET_SCHEMA, bounds=dict(total_seconds=total, cleanup_seconds=60, turn_seconds=turn, implementer_invocations=1, retry=False), submission=dict(path=str(submission),job_id='simulated-job'),run_id=name,work='W333485',claim=333593,outcome_path=str(root/(name+'.json')))
    with contextlib.ExitStack() as stack:
        for owner, attr, value in [
            (api,'read_submission',lambda value:{}),
            (api,'submit',lambda *args:{'submission_id':'simulated-not-submitted'}),
            (api,'serve',serve),
            (api,'sweep',sweep),
            (manager,'reconcile',lambda *args,**kwargs:{}),
            (manager,'sweep',sweep),
            (baseline,'_attempts_of',lambda *args:({ATTEMPT:'implementation'},states,limits)),
            (baseline,'_cleanups',lambda *args:{'cleanup':{},'outstanding':[ATTEMPT]}),
            (baseline,'_workload_evidence',lambda *args,**kwargs:{'shortfalls':['simulation; no result']}),
            (attempts,'attempt_runtime_of',lambda *args:{'runtime_id':RUNTIME,'execution_runtime':'running'}),
        ]:
            stack.enter_context(patch.object(owner,attr,value))
        out = baseline.supervise(object(),object(),Operations(),packet,clock=lambda:'2026-10-19T00:00:00Z',sleep=advance,monotonic=lambda:elapsed[0],surveyed={'preexisting_jobs':[],'preexisting_stages':{},'accounting_scope':'simulated preparation probe only'})
    assert observed_serve == [{'reclaim_supplied':False}]
    cancels = [c for c in calls if c['kind']=='cancel']
    assert len(cancels)==1 and cancels[0]['attempt']==ATTEMPT
    assert out['state']=='held' and out['outstanding_cleanup']==[ATTEMPT]
    assert out['cancellation'][ATTEMPT]['runtime_id']==RUNTIME
    assert out['stopped']=='overall-bound-exceeded'
    return dict(name=name,bounds=packet['bounds'],serve=observed_serve,calls=calls,simulated_elapsed_seconds=elapsed[0],served_seconds=out['served_seconds'],state=out['state'],outstanding_cleanup=out['outstanding_cleanup'],cancellation=out['cancellation'],held_because=out['held_because'])

started=time.monotonic()
results=[scenario('long-envelope',4800,3600,600,0,False),scenario('short-envelope-slow-cancel',300,180,600,600,True)]
assert results[0]['calls'][-1]['at']>900
assert results[1]['simulated_elapsed_seconds']>900
report=dict(scope=__doc__,staged_source=str(STAGED),retained_outcomes=str(root),wall_seconds=time.monotonic()-started,results=results,limitations='Scheduling/status/cancellation boundaries are simulated. This disproves a supervisor timing guarantee; it does not prove token expiry, runtime cessation, authority receipts, or availability of a safe replacement vehicle.')
(HERE/'RESULT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'wall_seconds':report['wall_seconds'],'scenarios':len(results),'held':[r['state'] for r in results],'simulated_seconds':[r['simulated_elapsed_seconds'] for r in results]}))
