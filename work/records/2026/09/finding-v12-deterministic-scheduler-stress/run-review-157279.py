import hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/home/sl/src/baton');record=pathlib.Path(__file__).resolve().parent
names=['v12/python/tests/tools/scheduler_trace.py','v12/python/tests/tools/test_scheduler_trace.py']
def hashes():
    return {name:{'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'bytes':(root/name).stat().st_size} for name in names}
ledger={'work':'W103525','claim':157279,'prior_review_seconds':58.77968077699256,'review_cap_seconds':300,'author_spent_seconds':321.26425073798833,'author_cap_seconds':600,'candidate_before':hashes(),'runs':[]}
def save():
    ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(run['elapsed_seconds'] for run in ledger['runs'])
    ledger['review_remaining_seconds']=300-ledger['review_spent_seconds']
    (record/'review-157279.json').write_text(json.dumps(ledger,indent=2)+'\n')
prefix='tests.tools.test_scheduler_trace.'
selectors=[prefix+'TheValidatorRefusesSyntheticInvalidTraces']+[prefix+'TheComposedOwnersSupplyAuthorizedTransitions.'+name for name in ['test_both_jobs_reach_a_real_imported_integration','test_four_jobs_on_two_repositories_code_in_parallel','test_two_producer_slots_cannot_serve_four_jobs','test_the_four_job_contention_exports_a_clean_artifact']]
for name,argv in [('focused',['/usr/bin/python3','-B','-m','unittest','-v',*selectors]),('probe',['/usr/bin/python3','-B',str(record/'repro-157279.py')])]:
    ledger['pending']={'name':name,'argv':argv};save();log=record/('review-157279-'+name+'.log');start=time.monotonic()
    with log.open('w') as out:
        try: rc=subprocess.run(argv,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=min(30,ledger['review_remaining_seconds'])).returncode
        except subprocess.TimeoutExpired: rc=124
    ledger['runs'].append({'name':name,'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name});ledger.pop('pending');save()
ledger['candidate_after']=hashes();ledger['candidate_unchanged']=ledger['candidate_before']==ledger['candidate_after'];save()
print(json.dumps({key:ledger[key] for key in ['runs','review_spent_seconds','review_remaining_seconds','candidate_unchanged']},indent=2))
