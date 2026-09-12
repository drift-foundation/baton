from pathlib import Path
import hashlib,json
repo=Path('/home/sl/src/baton')
p=repo/"work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof"
e=p/'evidence/review-149664'
prep=p/'prepared-149488'
def sha(f):return 'sha256:'+hashlib.sha256(f.read_bytes()).hexdigest()
m=p/'evidence/run8-freeze-149637/candidate-manifest.json'
assert sha(m)=='sha256:81747c62cd9863f9c0899e1292d80fc82b1757501caa7628e6286b933ba1dd81'
files=json.loads(m.read_text())['files']
reviewed={str(repo/n):v['sha256'] for n,v in files.items()}
reviewed[str(m)]=sha(m)
assert len(reviewed)==990
for n,h in reviewed.items():assert sha(Path(n))==h,n
review=p/'review-2026-09-12T04-00-48Z.md';assert review.is_file()
images=json.loads((prep/'candidate-images.json').read_text())
report={'verdict':'accepted','reviewer':'baton.codex','reviewed_at':'2026-09-12T04:00:48Z','review_locator':'baton:'+str(review.relative_to(repo)),'execution_authorized':True,'authorization_note':'Owner149484, reaffirmed149607: exactly ONE OPERATOR attempt after final actual-input review, now satisfied. No agent execution or automatic retry.','config_files':{n:sha(prep/'frozen-config'/n) for n in ('stage-execution.json','submission.json')},'reviewed_files':reviewed,'runtime_profile_digest':'sha256:15929015622f1264fa7f8f500ba8435d5a2ef4c366dee45b3d3a43e14d59bf88','images':images}
for name,doc in [('selected-images.json',images),('execution-review.json',report)]:
 with (prep/name).open('x') as f:json.dump(doc,f,indent=2,sort_keys=True);f.write('\n')
actual=json.loads((prep/'execution-review.json').read_text())
assert actual==report
for n,h in actual['reviewed_files'].items():assert sha(Path(n))==h,n
for n in ('run.py','deployment.py','target_posture.py','failure_observation.py'):assert str(prep/n) in reviewed
for n,h in actual['config_files'].items():assert sha(prep/'frozen-config'/n)==h
assert json.loads((prep/'selected-images.json').read_text())==actual['images']
markers={n:sha(prep/n) for n in ('selected-images.json','execution-review.json')}
(e/'markers.json').write_text(json.dumps({'reviewed_files':990,'config_files':actual['config_files'],'markers':markers,'operator_authority':[149484,149607],'agent_execution_authorized':False,'verified':True},indent=2)+'\n')
(e/'custody-check.py').write_bytes(Path('/tmp/w71879-review-149664-custody.py').read_bytes())
print(json.dumps(markers,indent=2))
