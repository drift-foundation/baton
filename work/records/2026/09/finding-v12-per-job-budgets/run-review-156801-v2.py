import hashlib,json,os,pathlib,subprocess,time
record=pathlib.Path(__file__).parent
root=pathlib.Path('/home/sl/src/baton/v12/python')
file=record/'review-156801.json';ledger=json.loads(file.read_text())
argv=['/usr/bin/python3','-B',str(record/'repro-156801-v2.py')]
ledger['pending']=argv;file.write_text(json.dumps(ledger,indent=2)+'\n')
log=record/'review-156801-proposed-fixture-v2.log';start=time.monotonic()
with log.open('w') as out:
    try: rc=subprocess.run(argv,cwd=root,env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=45).returncode
    except subprocess.TimeoutExpired: rc=124
ledger['runs'].append({'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name});ledger.pop('pending')
ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(r['elapsed_seconds'] for r in ledger['runs'])
ledger['candidate_after']={n:{'sha256':hashlib.sha256((root/n).read_bytes()).hexdigest(),'bytes':(root/n).stat().st_size} for n in ledger['candidate_before']}
ledger['candidate_unchanged']=ledger['candidate_after']==ledger['candidate_before']
file.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({'runs':ledger['runs'],'review_spent_seconds':ledger['review_spent_seconds'],'candidate_unchanged':ledger['candidate_unchanged']},indent=2))
