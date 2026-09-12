from pathlib import Path
import hashlib,json,stat,time
repo=Path('/home/sl/src/baton')
p=repo/"work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof"
e=p/'evidence/review-150048'
start=time.monotonic()
def sha(f):return 'sha256:'+hashlib.sha256(f.read_bytes()).hexdigest()
m=p/'evidence/run9-preparation-150007/candidate-manifest.json'
assert sha(m)=='sha256:7c5ad3aeb64f845cc083ab9f25c6b857840f845f257b8591b8ac6ffb4f76f260'
files=json.loads(m.read_text())['files'];assert len(files)==153
for n,v in files.items():
 rel=Path(n);assert not rel.is_absolute() and '..' not in rel.parts
 assert n.startswith(str(p.relative_to(repo))+'/') or n in ('v12/python/tools/stage_execution.py','v12/python/tests/tools/test_stage_execution.py')
 assert rel.suffix not in ('.db','.sqlite','.sqlite3') and 'credentials' not in rel.parts
 f=repo/rel;s=f.lstat()
 assert stat.S_ISREG(s.st_mode) and sha(f)==v['sha256'] and s.st_size==v['bytes'] and oct(stat.S_IMODE(s.st_mode))==v['mode'],n
prior=json.loads(Path('/tmp/w71879-150007-provenance-r5t6wc96/provenance.json').read_text())
(e/'provenance.json').write_text(json.dumps(prior,indent=2)+'\n')
homes=[]
for f in Path('/tmp/w71879-150007-public-bootstrap-6pk73kw5/documents/workers').glob('*.json'):
 d=json.loads(f.read_text());assert d['authority_uuid']=='c71879b3000000000000000000000001'
 assert d['credential_sources']=='/home/sl/.baton/credential-sources.json' and d['credential_profile']=={'claude':{'provider':'operator-file','reference':'w64268-run1'}} and d['credential_slots']==['claude']
 homes.append(d['credential_home'])
assert len(homes)==len(set(homes))==8
report={'manifest':sha(m),'verified_files':len(files),'four_helpers':prior['four_helpers'],'independent_fixture_credential_config_only':{'distinct_homes':homes,'payloads_read':False},'seconds':time.monotonic()-start}
(e/'custody.json').write_text(json.dumps(report,indent=2)+'\n')
seconds=report['seconds']+0.14506326499395072+0.027
cost={'fresh_preparation_tests_seconds_rounded':0.027,'provenance_seconds':0.14506326499395072,'custody_seconds':report['seconds'],'current_listed_seconds':seconds,'cumulative_listed_preparation_seconds':49.59649493788288+seconds,'eight_failed_runtime_walls_seconds':1593.8314001880208,'uncertainty':'Rounded test time and untimed reads/edits/CLI/host/billing additional; prior suites not rerun or recounted.'}
(e/'spending.json').write_text(json.dumps(cost,indent=2)+'\n')
print(json.dumps({'custody':report,'spending':cost},indent=2))
