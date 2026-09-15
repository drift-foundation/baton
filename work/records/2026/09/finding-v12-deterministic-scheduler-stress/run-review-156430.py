import hashlib, json, os, subprocess, time
from pathlib import Path
root=Path('/home/sl/src/baton')
record=Path(__file__).parent
names=['v12/python/tests/tools/scheduler_trace.py','v12/python/tests/tools/test_scheduler_trace.py']
def hashes():
    return {n:{'sha256':hashlib.sha256((root/n).read_bytes()).hexdigest(),'bytes':(root/n).stat().st_size} for n in names}
ledger={'work':'W103525','claim':156430,'prior_review_seconds':55.0305936499924,'review_cap_seconds':300,'candidate_before':hashes(),'runs':[]}
target=record/'review-156430.json'
def save():
    ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(r['elapsed_seconds'] for r in ledger['runs'])
    ledger['review_remaining_seconds']=300-ledger['review_spent_seconds']
    target.write_text(json.dumps(ledger,indent=2)+'\n')
save()
env=dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1')
selectors=['tests.tools.test_scheduler_trace.TheValidatorRefusesSyntheticInvalidTraces','tests.tools.test_scheduler_trace.TheComposedOwnersSupplyAuthorizedTransitions.test_the_composed_deployment_reopens_and_continues','tests.tools.test_scheduler_trace.TheComposedOwnersSupplyAuthorizedTransitions.test_both_jobs_traverse_and_one_integrator_serializes_them','tests.tools.test_scheduler_trace.TheComposedOwnersSupplyAuthorizedTransitions.test_both_jobs_reach_a_real_imported_integration']
for name,argv in [('focused',['/usr/bin/python3','-B','-m','unittest','-v',*selectors]),('probe',['/usr/bin/python3','-B',str(record/'repro-156430.py')])]:
    ledger['pending']={'name':name,'argv':argv}; save()
    log=record/('review-156430-'+name+'.log')
    start=time.monotonic()
    with log.open('w') as out:
        try: rc=subprocess.run(argv,cwd=root/'v12/python',env=env,stdout=out,stderr=subprocess.STDOUT,timeout=min(60,ledger['review_remaining_seconds'])).returncode
        except subprocess.TimeoutExpired: rc=124
    ledger['runs'].append({'name':name,'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name})
    ledger.pop('pending'); save()
ledger['candidate_after']=hashes(); ledger['candidate_unchanged']=ledger['candidate_after']==ledger['candidate_before']; save()
print(json.dumps(ledger,indent=2))
