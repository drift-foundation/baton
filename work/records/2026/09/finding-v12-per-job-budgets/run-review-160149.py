import hashlib,json,os,pathlib,subprocess,time
record=pathlib.Path(__file__).resolve().parent;root=pathlib.Path('/home/sl/src/baton')
previous=json.loads((record/'review-160060.json').read_text())
author=json.loads((record/'ledger-156316.json').read_text())
names=list(previous['candidate_after'])
def hashes():
    return {name:{'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'bytes':(root/name).stat().st_size} for name in names}
ledger={'work':'W156162','claim':160149,'author_spent_seconds':author['spent_seconds'],'author_measured_runs':len(author['runs']),'prior_review_seconds':previous['review_spent_seconds'],'candidate_before':hashes(),'runs':[]}
argv=['/usr/bin/python3', '-B', '-m', 'unittest', '-v', 'tests.tools.test_execution_limits.TheComposedHostVerificationUsesTheJobsCeiling.test_a_blocked_result_is_refused_by_the_composed_judgment_owners', 'tests.tools.test_execution_limits.TheComposedHostVerificationUsesTheJobsCeiling.test_a_scratch_that_survives_disposal_is_the_deployments_to_release', 'tests.tools.test_execution_limits.TheComposedHostVerificationUsesTheJobsCeiling.test_a_scratch_that_survives_the_release_too_is_reported'];log=record/'review-160149-focused.log';start=time.monotonic()
with log.open('w') as out:
    try:rc=subprocess.run(argv,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=20).returncode
    except subprocess.TimeoutExpired:rc=124
ledger['runs'].append({'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name})
ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(one['elapsed_seconds'] for one in ledger['runs'])
ledger['candidate_after']=hashes();ledger['candidate_unchanged']=ledger['candidate_before']==ledger['candidate_after']
(record/'review-160149.json').write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({name:ledger[name] for name in ('runs','review_spent_seconds','author_spent_seconds','author_measured_runs','candidate_unchanged')},indent=2))
