import hashlib,json,os,pathlib,subprocess,time
record=pathlib.Path(__file__).resolve().parent
root=pathlib.Path('/home/sl/src/baton')
names=list(json.loads((record/'review-157052.json').read_text())['candidate_after'])+['v12/python/tools/integration_worker.py','v12/python/tools/integration_bundle.py']
def hashes():
    return {name:{'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'bytes':(root/name).stat().st_size} for name in names}
ledger={'work':'W156162','claim':157207,'author_spent_seconds':663.5290292359932,'author_unmeasured_activities':['original baseline','golden generation','isolated-copy attribution attempt','in-place injection-removal attribution experiment'],'prior_review_seconds':7.126665509995291,'candidate_before':hashes(),'runs':[]}
def save():
    ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(run['elapsed_seconds'] for run in ledger['runs'])
    (record/'review-157207.json').write_text(json.dumps(ledger,indent=2)+'\n')
prefix='tests.tools.test_execution_limits.'
selectors=[prefix+name for name in ['TheContainerEntryReadsTheThirdVersion','TheAdapterHandsTheCommandWhatWasConfigured','TheImportedVerificationUsesItsOwnBoundary','TheJobOwnerAnswersOneBoundaryWithoutADelivery','TheDirectIntegrationCarriesItsJobsOwnCeiling.test_the_port_materializes_a_third_version_carrying_the_job','TheDirectIntegrationCarriesItsJobsOwnCeiling.test_a_port_with_no_job_owner_composes_exactly_what_it_always_did','TheDirectIntegrationCarriesItsJobsOwnCeiling.test_an_attempt_this_execution_never_prepared_is_refused','TheHostSideVerificationCarriesTheSameCeiling.test_an_unconfigured_owner_runs_under_the_boundarys_own_default','TheHostSideVerificationCarriesTheSameCeiling.test_the_git_clock_is_untouched_by_a_jobs_ceiling']]
for label,argv in [('focused',['/usr/bin/python3','-B','-m','unittest','-v',*selectors]),('probe',['/usr/bin/python3','-B',str(record/'repro-157207.py')])]:
    ledger['pending']=argv;save()
    log=record/('review-157207-'+label+'.log');start=time.monotonic()
    with log.open('w') as out:
        try: rc=subprocess.run(argv,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=30).returncode
        except subprocess.TimeoutExpired: rc=124
    ledger['runs'].append({'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name});ledger.pop('pending');save()
ledger['candidate_after']=hashes();ledger['candidate_unchanged']=ledger['candidate_before']==ledger['candidate_after'];save()
print(json.dumps({key:ledger[key] for key in ('runs','review_spent_seconds','candidate_unchanged')},indent=2))
