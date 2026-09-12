from pathlib import Path
import ast, hashlib, json, re, stat, sys, time
repo=Path('/home/sl/src/baton')
proof=repo/"work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof"
out=proof/'evidence/review-149543'
p=proof/'prepared-149488'
start=time.monotonic()
def sha(path): return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()
manifest=proof/'evidence/run8-preparation-149488/candidate-manifest.json'
assert sha(manifest)=='sha256:d0c4aa3f674c72b90161d645009594f8ecbed6299c9bb13b70c2d4ea0692eab9'
files=json.loads(manifest.read_text())['files']
assert len(files)==944
for name,value in files.items():
    rel=Path(name)
    assert not rel.is_absolute() and '..' not in rel.parts
    assert name.startswith(str(proof.relative_to(repo))+'/') or name in ('v12/worker/claude_agent.py','v12/python/tests/manager/test_claude_agent.py')
    assert not any(part in ('credentials','provider.stdout','provider.stderr') for part in rel.parts)
    assert rel.suffix not in ('.sqlite3','.sqlite','.db')
    f=repo/rel
    assert stat.S_ISREG(f.lstat().st_mode) and not f.is_symlink(),name
    assert sha(f)==value['sha256'] and f.stat().st_size==value['bytes'] and oct(stat.S_IMODE(f.stat().st_mode))==value['mode'],name
source=json.loads((proof/'prepared-146897/evidence/provenance.json').read_text())
for name,value in source['provider_chain'].items():
    f=repo/name
    if 'sha256' in value: assert sha(f)=='sha256:'+value['sha256'],name
    else: assert not f.exists() and not f.is_symlink()
count=0
for group in ('source_requirements','current_observation_sources'):
    for name,value in source[group].items(): assert sha(repo/name)==value,name; count+=1
for name,value in json.loads((p/'runner-helpers.json').read_text()).items(): assert sha(p/name)==value
for name in ('frozen-config','validation.json','selected-images.json','execution-review.json','image-build'):
    assert not (p/name).exists() and not (p/name).is_symlink(),name
fresh=Path('/home/sl/.local/state/baton/v12/w71879-run8')
assert not fresh.exists() and not fresh.is_symlink()
old=proof/'prepared-149053'
for name,value in {'selected-images.json':'d0da4684accfa0cba16dc712d2456745de56ef3632f315a7c17a6649407a8f5f','execution-review.json':'87289f5ec4d7a2d31455516856de4a71cb0b27f259e0645e2291370a0229caed'}.items(): assert sha(old/name)=='sha256:'+value
for f in p.glob('*.py'): ast.parse(f.read_text())
fixture=Path('/tmp/w71879-149488-public-bootstrap-j24oipcc/documents')
homes=[]
for f in sorted((fixture/'workers').glob('*.json')):
    d=json.loads(f.read_text())
    assert d['credential_sources']=='/home/sl/.baton/credential-sources.json'
    assert d['credential_slots']==['claude']
    assert d['credential_profile']=={'claude':{'provider':'operator-file','reference':'w64268-run1'}}
    assert '/offline-run/credentials/' in d['credential_home']
    homes.append(d['credential_home'])
assert len(homes)==len(set(homes))==8
e=proof/'evidence/run8-preparation-149488'
sys.path[:0]=[str(old),str(repo/'v12/python/src')]
from failure_observation import first_failure
samples=[json.loads(line) for line in (e/'run7-samples.jsonl').read_text().splitlines()]
works={n:'c71879b1-W'+str(i) for i,n in enumerate(('a','b','verification','review','approval'),1)}
found=[]
for i,row in enumerate(samples,1):
    failure=first_failure(row['status'],authority_uuid='c71879b1000000000000000000000001',incarnation='w71879-run7',works=works)
    if failure: found.append((i,row['wall_seconds'],failure))
result=json.loads((e/'run7-run-result.json').read_text())
failure=json.loads((e/'run7-first-failure.json').read_text())
diagnostic=json.loads((e/'run7-failure-diagnostic.json').read_text())
assert len(samples)==5 and found[0][0]==5 and result['terminal_both'] is False
assert failure==result['primary_failure'] and diagnostic==result['provider_diagnostic']
assert failure['attempt_id']==found[0][2]['attempt_id'] and failure['wall_seconds']==found[0][1]
assert diagnostic['authentication_cause']=='provider-reported-oauth-session-expired-refresh-failed'
report={'manifest':sha(manifest),'verified_files':len(files),'provider_chain_entries':len(source['provider_chain']),'source_bindings':count,'helpers':json.loads((p/'runner-helpers.json').read_text()),'fresh_root_and_actual_outputs_absent':True,'credential_configuration_only':{'workers':8,'distinct_homes':homes,'owner_login_attestation':149484,'payloads_read':False},'run7':{'first_failure_sample':5,'first_failure_seconds':found[0][1],'wall_seconds':result['wall_seconds'],'terminal_both':False,'diagnostic':diagnostic},'seconds':time.monotonic()-start}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
spending={'previous_listed_preparation_seconds':42.20336665593286,'independent_offline_suite_seconds':0.33141366101335734,'independent_custody_seconds':report['seconds'],'current_listed_preparation_seconds':0.33141366101335734+report['seconds'],'cumulative_listed_preparation_seconds':42.20336665593286+0.33141366101335734+report['seconds'],'seven_failed_runtime_walls_seconds':1350.217186488022,'uncertainty':'Additional untimed review, edits, CLI, metadata and operator/login/host/billing costs remain; suite inner time only counted once; no reserve transfer.'}
(out/'spending.json').write_text(json.dumps(spending,indent=2)+'\n')
print(json.dumps({'verification':report,'spending':spending},indent=2))
