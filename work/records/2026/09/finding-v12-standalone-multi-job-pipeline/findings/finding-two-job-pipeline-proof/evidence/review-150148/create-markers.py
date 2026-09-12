from pathlib import Path
import hashlib,json
repo=Path('/home/sl/src/baton')
p=repo/"work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof"
prep=p/'prepared-150007'
e=p/'evidence/review-150148'
def sha(f):return 'sha256:'+hashlib.sha256(f.read_bytes()).hexdigest()
m=p/'evidence/run9-freeze-150125/candidate-manifest.json'
assert sha(m)=='sha256:aa78787caaf0796d303c703bc745e758d46e67dde671a6668d6e95de3b9ac5a2'
files=json.loads(m.read_text())['files']
reviewed={str(repo/n):v['sha256'] for n,v in files.items()};reviewed[str(m)]=sha(m)
assert len(reviewed)==199
for n,h in reviewed.items():assert sha(Path(n))==h,n
review=p/'review-2026-09-12T05-23-46Z.md';assert review.is_file()
images=json.loads((prep/'candidate-images.json').read_text())
doc={'verdict':'accepted','reviewer':'baton.codex','reviewed_at':'2026-09-12T05:23:46Z','review_locator':'baton:'+str(review.relative_to(repo)),'execution_authorized':True,'authorization_note':'Owner150004, reaffirmed150121, authorizes exactly ONE OPERATOR attempt after required checks and genuine bindings, now complete. No agent execution or automatic retry.','config_files':{n:sha(prep/'frozen-config'/n) for n in ('stage-execution.json','submission.json')},'runtime_profile_digest':'sha256:e9cc25e922d3e3cf018f0c7538d953b8dd773cdc96bc8eea5cea522b4b3b1112','images':images,'reviewed_files':reviewed}
for n,data in [('selected-images.json',images),('execution-review.json',doc)]:
 with (prep/n).open('x') as f:json.dump(data,f,indent=2,sort_keys=True);f.write('\n')
assert json.loads((prep/'execution-review.json').read_text())==doc
for n,h in doc['reviewed_files'].items():assert sha(Path(n))==h,n
for n,h in doc['config_files'].items():assert sha(prep/'frozen-config'/n)==h
for n in ('run.py','deployment.py','target_posture.py','failure_observation.py'):assert str(prep/n) in reviewed
assert json.loads((prep/'selected-images.json').read_text())==images
markers={n:sha(prep/n) for n in ('selected-images.json','execution-review.json')}
(e/'markers.json').write_text(json.dumps({'markers':markers,'reviewed_files':199,'config_files':doc['config_files'],'verified':True,'owner_authority':[150004,150121],'agent_execution_authorized':False},indent=2)+'\n')
print(json.dumps(markers,indent=2))
