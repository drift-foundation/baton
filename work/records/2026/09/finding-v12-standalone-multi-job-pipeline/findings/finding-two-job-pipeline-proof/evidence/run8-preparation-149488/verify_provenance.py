from pathlib import Path
import ast,difflib,hashlib,json,re,stat,sys,time
repo=Path('/home/sl/src/baton');r=repo/'work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof';p=r/'prepared-149488';e=r/'evidence/run8-preparation-149488';old=r/'prepared-149053';t=time.monotonic()
def sha(f):return 'sha256:'+hashlib.sha256(f.read_bytes()).hexdigest()
report={'work':'W71879','claim':149488,'prior_manifests':[]}
for rel,hash_ in [('evidence/run7-freeze-149356/candidate-manifest.json','6e95a68815f0d1c353dc7f78836dc762132176a92f17f28ac0b39b6b88052224'),('evidence/image-preparation-149053/candidate-manifest.json','fa2f9526995166f66c195704b71bfb4504c3713d6820362565641b88246c9037')]:
 m=r/rel;assert sha(m)=='sha256:'+hash_;files=json.loads(m.read_text())['files']
 for name,v in files.items():
  f=repo/name;s=f.lstat();assert stat.S_ISREG(s.st_mode) and sha(f)==v['sha256'] and s.st_size==v['bytes'] and oct(stat.S_IMODE(s.st_mode))==v['mode'],name
 report['prior_manifests'].append({'path':str(m.relative_to(repo)),'sha256':sha(m),'verified_files':len(files)})
markers={'selected-images.json':'d0da4684accfa0cba16dc712d2456745de56ef3632f315a7c17a6649407a8f5f','execution-review.json':'87289f5ec4d7a2d31455516856de4a71cb0b27f259e0645e2291370a0229caed'}
for name,h in markers.items():assert sha(old/name)=='sha256:'+h
report['preserved_run7_markers']=markers
source=json.loads((r/'prepared-146897/evidence/provenance.json').read_text());report['source_bindings']={}
for name,v in source['provider_chain'].items():
 if 'sha256' in v:assert sha(repo/name)=='sha256:'+v['sha256'],name
 else:assert not (repo/name).exists() and not (repo/name).is_symlink()
for group in ('source_requirements','current_observation_sources'):
 for name,h in source[group].items():assert sha(repo/name)==h;report['source_bindings'][name]=h
report['provider_chain_entries']=len(source['provider_chain'])
changed=[];unchanged=[];patch=[]
for f in sorted(p.rglob('*')):
 if not f.is_file() or '__pycache__' in f.parts:continue
 rel=str(f.relative_to(p));prior=old/('test_run7_preparation.py' if rel=='test_run8_preparation.py' else rel)
 if not prior.exists():continue
 if prior.read_bytes()==f.read_bytes():unchanged.append(rel)
 else:
  changed.append(rel)
  if f.suffix in ('.py','.json','.sh'):patch+=list(difflib.unified_diff(prior.read_text().splitlines(True),f.read_text().splitlines(True),fromfile=str(prior.relative_to(r)),tofile=str(f.relative_to(r))))
report['changed_copies']=changed;report['unchanged_copies']=unchanged
(e/'preparation-delta.patch').write_text(''.join(patch))
# Verify supported delivery configuration without reading credential source or old delivery payloads.
log=(e/'verification-1.txt').read_text();match=re.search(r'Retained offline public bootstrap: (\S+)',log);assert match
fixture=Path(match[1])/'documents';homes=[]
for f in sorted((fixture/'workers').glob('*.json')):
 d=json.loads(f.read_text());assert d['credential_sources']=='/home/sl/.baton/credential-sources.json'
 assert d['credential_slots']==['claude'] and d['credential_profile']=={'claude':{'provider':'operator-file','reference':'w64268-run1'}}
 assert '/offline-run/credentials/' in d['credential_home'] and 'w71879-run7' not in d['credential_home'];homes.append(d['credential_home'])
assert len(homes)==len(set(homes))==8
report['credential_delivery_check']={'scope':'eight offline constructed worker documents; configured provider/reference and separate fresh per-worker homes, not credential contents or successful login validation','fixture':str(fixture),'distinct_homes':homes,'runtime_path_rule':'deployment uses RUN/credentials/actor; RUN is fresh run8','owner_refreshed_source_attestation':149484}
# Correlate the first supported run7 failure without broader investigation or raw provider reads.
sys.path[:0]=[str(old),str(repo/'v12/python/src')];from failure_observation import first_failure
samples=[json.loads(line) for line in (e/'run7-samples.jsonl').read_text().splitlines()]
works={n:'c71879b1-W'+str(i) for i,n in enumerate(('a','b','verification','review','approval'),1)}
found=[]
for i,row in enumerate(samples,1):
 f=first_failure(row['status'],authority_uuid='c71879b1000000000000000000000001',incarnation='w71879-run7',works=works)
 if f:found.append((i,row['wall_seconds'],f))
assert found and found[0][0]==5
result=json.loads((e/'run7-run-result.json').read_text());failure=json.loads((e/'run7-first-failure.json').read_text());diagnostic=json.loads((e/'run7-failure-diagnostic.json').read_text())
assert result['primary_failure']==failure and result['provider_diagnostic']==diagnostic
assert failure['attempt_id']==found[0][2]['attempt_id'] and failure['wall_seconds']==found[0][1]
assert result['terminal_both'] is False and result['submitted'] is True
assert diagnostic['authentication_cause']=='provider-reported-oauth-session-expired-refresh-failed'
assert diagnostic['detail']['explanation']=='Failed to authenticate: OAuth session expired and could not be refreshed'
report['run7']={'scope':'bounded retained first-failure replay and existing supplementary detail, no broader diagnosis','sample_count':len(samples),'first_failure_sample':found[0][0],'first_failure_seconds':found[0][1],'wall_seconds':result['wall_seconds'],'first_failure_to_end_seconds':result['wall_seconds']-found[0][1],'terminal_both':False,'supported_provider_detail':diagnostic,'source_files':{name:sha(e/('run7-'+name)) for name in ('run-result.json','first-failure.json','failure-diagnostic.json','samples.jsonl')}}
images=json.loads((p/'candidate-images.json').read_text());assert images==json.loads((old/'selected-images.json').read_text())
report['images']=images
for row in map(json.loads,(e/'images.jsonl').read_text().splitlines()):assert row['id'] in images.values() and row['user']=='65532:65532' and row['os']=='linux' and row['arch']=='amd64'
for f in p.glob('*.py'):ast.parse(f.read_text())
for name in ('frozen-config','validation.json','selected-images.json','execution-review.json','image-build'):
 f=p/name;assert not f.exists() and not f.is_symlink(),name
fresh=Path('/home/sl/.local/state/baton/v12/w71879-run8');assert not fresh.exists() and not fresh.is_symlink()
report['fresh_run8_absent']=True;report['new_actual_host_outputs_and_markers_absent']=True
report['verification_seconds']=time.monotonic()-t
(e/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'prior_manifests':report['prior_manifests'],'credential_workers':8,'run7_wall':result['wall_seconds'],'new_root_absent':True,'verification_seconds':report['verification_seconds']},indent=2))
