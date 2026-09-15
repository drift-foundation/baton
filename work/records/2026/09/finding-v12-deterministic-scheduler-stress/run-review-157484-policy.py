import hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/home/sl/src/baton');record=pathlib.Path(__file__).resolve().parent
ledger=json.loads((record/'review-157484.json').read_text())
argv=['/usr/bin/python3','-B',str(record/'repro-157484-policy.py')]
ledger['pending']={'name':'fresh-policy','argv':argv}
def save():
    (record/'review-157484.json').write_text(json.dumps(ledger,indent=2)+'\n')
save();start=time.monotonic();log=record/'review-157484-policy.log'
with log.open('w') as out:
    try: rc=subprocess.run(argv,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=min(30,ledger['review_remaining_seconds'])).returncode
    except subprocess.TimeoutExpired: rc=124
ledger['runs'].append({'name':'fresh-policy','argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name})
ledger.pop('pending');ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(one['elapsed_seconds'] for one in ledger['runs']);ledger['review_remaining_seconds']=300-ledger['review_spent_seconds']
ledger['candidate_after']={name:{'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'bytes':(root/name).stat().st_size} for name in ledger['candidate_before']}
ledger['candidate_unchanged']=ledger['candidate_before']==ledger['candidate_after'];save()
print(json.dumps({key:ledger[key] for key in ('runs','review_spent_seconds','review_remaining_seconds','candidate_unchanged')},indent=2))
