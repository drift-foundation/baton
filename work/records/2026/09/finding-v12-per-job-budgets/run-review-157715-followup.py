import hashlib,json,os,pathlib,subprocess,sys,time
record=pathlib.Path(__file__).resolve().parent;root=pathlib.Path('/home/sl/src/baton')
path=record/'review-157715.json';ledger=json.loads(path.read_text());label=sys.argv[1]
argv=['/usr/bin/python3','-B',str(record/('repro-157715-'+label+'.py'))]
ledger['pending']=argv;path.write_text(json.dumps(ledger,indent=2)+'\n')
log=record/('review-157715-'+label+'.log');start=time.monotonic()
with log.open('w') as out:
    try: rc=subprocess.run(argv,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=15).returncode
    except subprocess.TimeoutExpired: rc=124
ledger['runs'].append({'argv':argv,'exit':rc,'elapsed_seconds':time.monotonic()-start,'log':log.name});ledger.pop('pending')
ledger['review_spent_seconds']=ledger['prior_review_seconds']+sum(one['elapsed_seconds'] for one in ledger['runs'])
ledger['candidate_after']={name:{'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest(),'bytes':(root/name).stat().st_size} for name in ledger['candidate_before']}
ledger['candidate_unchanged']=ledger['candidate_before']==ledger['candidate_after']
path.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({'run':ledger['runs'][-1],'review_spent_seconds':ledger['review_spent_seconds'],'candidate_unchanged':ledger['candidate_unchanged']},indent=2))
