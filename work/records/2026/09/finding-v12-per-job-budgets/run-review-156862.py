import hashlib,json,os,pathlib,subprocess,time
record=pathlib.Path(__file__).parent
root=pathlib.Path('/home/sl/src/baton/v12/python')
names=list(json.loads((record/'review-156801.json').read_text())['candidate_after'])+['tests/tools/test_stage_execution.py']
def hashes():
    return {n:{'sha256':hashlib.sha256((root/n).read_bytes()).hexdigest(),'bytes':(root/n).stat().st_size} for n in names}
ledger={'work':'W156162','claim':156862,'author_spent_seconds':134.89787969399913,'author_unmeasured_activities':['original baseline','golden generation','new isolated-copy attribution attempt','new in-place injection-removal attribution experiment'],'prior_review_seconds':4.529427870997097,'candidate_before':hashes(),'runs':[]}
def save():
    ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(r['elapsed_seconds'] for r in ledger['runs'])
    (record/'review-156862.json').write_text(json.dumps(ledger,indent=2)+'\n')
selectors=['tests.tools.test_stage_execution.TheComposedImplementationHalfRunsOnOrdinaryTicks.test_one_submitted_job_reaches_a_completed_implementation_stage','tests.tools.test_stage_execution.TheComposedJobTraversesReviewAndAcceptance.test_the_reviewers_own_verdict_completes_the_review_stage','tests.tools.test_stage_execution.TwoBoundJobsTraverseServingAndCorrection.test_the_second_job_reaches_its_own_reviewer_and_verdict']
argv=['/usr/bin/python3','-B','-m','unittest','-v',*selectors]
ledger['pending']=argv;save()
log=record/'review-156862-focused.log';start=time.monotonic()
with log.open('w') as out:
    try: rc=subprocess.run(argv,cwd=root,env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=30).returncode
    except subprocess.TimeoutExpired: rc=124
ledger['runs'].append({'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name});ledger.pop('pending')
ledger['candidate_after']=hashes();ledger['candidate_unchanged']=ledger['candidate_after']==ledger['candidate_before'];save()
print(json.dumps({'runs':ledger['runs'],'review_spent_seconds':ledger['review_spent_seconds'],'candidate_unchanged':ledger['candidate_unchanged']},indent=2))
