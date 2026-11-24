from pathlib import Path
import json,hashlib,subprocess,stat,tarfile,difflib,shutil,os
root=Path('/home/sl/src/baton');r=root/'work/scratch/w385965-n1n2/repo';d=root/'work/records/2026/11/finding-v12-native-provider-selection';old=d/'evidence/implementation-385975';e=d/'evidence/correction-385982'
sha=lambda b:hashlib.sha256(b).hexdigest()
prior=json.loads((old/'candidate-manifest.json').read_text());oldfiles={f['path']:f for f in prior['files']}
ctx=e/'context';ctx.mkdir(exist_ok=True)
for p in (old/'context').iterdir():shutil.copyfile(p,ctx/p.name)
review=d/'review-2026-11-24T10-12-37Z.md';shutil.copyfile(review,ctx/review.name)
ruling=d.joinpath('FINDING.md').read_text().split('## 2026-11-24 — owner confirms drafted, unqualified Claude participation list\n',1)[1]
(ctx/'OWNER-DRAFT-QUALIFICATION-RULING-2026-11-24.md').write_text('# Owner ruling — 2026-11-24\n\nSource: owning FINDING.md, section “owner confirms drafted, unqualified Claude participation list”.\n'+ruling)
assert sha((root/'v12/DESIGN.md').read_bytes())==prior['context']['DESIGN.md']
paths=sorted(set(subprocess.check_output(['git','diff','--name-only','--','v12'],cwd=r,text=True).splitlines())|set(subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','v12'],cwd=r,text=True).splitlines()))
files=[];delta=[];patch=[]
with tarfile.open(old/'candidate-files.tar.gz') as previous:
 for name in paths:
  p=r/name;b=p.read_bytes();f={'path':name,'bytes':len(b),'mode':oct(stat.S_IMODE(p.stat().st_mode)),'sha256':sha(b)};files.append(f)
  before=previous.extractfile(name).read() if name in oldfiles else subprocess.check_output(['git','show','HEAD:'+name],cwd=r)
  beforemode=oldfiles[name]['mode'] if name in oldfiles else '0o644'
  if sha(before)!=f['sha256'] or beforemode!=f['mode']:
   delta.append({'path':name,'before_sha256':sha(before),'before_bytes':len(before),'before_mode':beforemode,'after_sha256':f['sha256'],'after_bytes':f['bytes'],'after_mode':f['mode']})
   patch.extend(difflib.unified_diff(before.decode().splitlines(keepends=True),b.decode().splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
context={p.name:sha(p.read_bytes()) for p in sorted(ctx.iterdir())}
identity={'base':prior['base'],'files':files,'context':context};candidate='sha256:'+sha(json.dumps(identity,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
m=dict(identity,candidate=candidate,claim=385982,work='W385965',prior_candidate=prior['candidate'],algorithm=prior['algorithm'],status='R1-R4 correction candidate for independent K delta review; no native qualification')
(e/'candidate-manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
(e/'delta-manifest.json').write_text(json.dumps({'base':prior['base'],'from_candidate':prior['candidate'],'to_candidate':candidate,'files':delta},indent=2,sort_keys=True)+'\n')
(e/'delta.patch').write_text(''.join(patch))
for name,selected in [('candidate-files.tar.gz',paths),('delta-files.tar.gz',[f['path'] for f in delta])]:
 with tarfile.open(e/name,'w:gz') as tar:
  for p in selected:tar.add(r/p,arcname=p,recursive=False)
 with tarfile.open(e/name) as tar:
  assert set(tar.getnames())==set(selected)
  for member in tar.getmembers():
   f=next(f for f in files if f['path']==member.name);assert sha(tar.extractfile(member).read())==f['sha256'];assert oct(member.mode)==f['mode']
 (e/(name+'.sha256')).write_text(sha((e/name).read_bytes())+'  '+name+'\n')
check=subprocess.run(['git','diff','--check'],cwd=r,capture_output=True);assert check.returncode==0;(e/'diff-check.log').write_bytes(check.stdout+check.stderr)
py='/home/sl/.local/state/baton-v12-venv/bin/python';result=subprocess.run([py,'-m','tools.source_identity','--declared','v12'],cwd=r/'v12/python',env=dict(os.environ,PYTHONPATH='src'),capture_output=True);assert result.returncode==0;(e/'final-source.json').write_bytes(result.stdout)
a=json.loads((e/'focused.source-after.json').read_text());b=json.loads(result.stdout);x={p['path']:p['sha256'] for p in a['changed']};y={p['path']:p['sha256'] for p in b['changed']};changed=sorted(k for k in set(x)|set(y) if x.get(k)!=y.get(k));assert changed==['v12/PROVIDER-SELECTION.md'];assert a['consumed']==b['consumed']
(e/'source-reconciliation.json').write_text(json.dumps({'tested_source':a['content_digest'],'final_source':b['content_digest'],'post_test_delta':changed,'production_and_test_bytes_unchanged':True,'reason':'Added explanatory pre-start release/hold sentences to documentation after focused run.'},indent=2)+'\n')
summary=json.loads((e/'focused.summary.json').read_text());assert summary['collected']==summary['passed']==765 and not summary['nonpassing'] and not summary['unaccounted'] and summary['exit_status']==0
mapping=json.loads((old/'proof-table.json').read_text());mapping['37']=['tests.job_manager.test_scheduling.Capacity.test_a_second_admission_to_one_live_worker_is_refused']
newids={test for test in summary['outcomes'] if '.test_R' in test or test.endswith('test_a_second_admission_to_one_live_worker_is_refused') or test.endswith('test_attribution_holds_name_typed_cause_and_owner_action_on_all_views')}
mapping['R1']=sorted(t for t in newids if '.test_R1_' in t);mapping['R2']=[t for t in summary['outcomes'] if 'test_39_crash_after_record_before_home_creation_replays_same_holder' in t];mapping['R3']=sorted(t for t in newids if '.test_R3_' in t or 'test_attribution_holds' in t);mapping['R4']=mapping['37']
(e/'proof-table.json').write_text(json.dumps({'prior_proof_table':'../implementation-385975/proof-table.json','proofs':mapping,'focused_rechecked_ids':sorted(summary['outcomes']),'note':'Earlier 2791 evidence is retained historical baseline, not a new full rerun. Current delta checks collected/executed/passed 765.'},indent=2)+'\n')
text=(d/'PROOF-TABLE-N1N2-385975.md').read_text().replace('# W385965 N1/N2 and owner-B proof table','# W385965 R1–R4 proof table and retained baseline').replace(prior['candidate'],candidate)
a=text.index('Joined accounting:');b=text.index('\n\n',a);text=text[:a]+'Current delta accounting: **765 collected/executed/passed**, zero failures/errors/skips/unaccounted. Earlier 2791-pass evidence remains a reviewed historical baseline; it is not a full rerun of these changed bytes. `evidence/correction-385982/proof-table.json` distinguishes current rechecked IDs from retained baseline. The table below preserves earlier mappings except corrected proof 37; the R1–R4 table names current checks.'+text[b:]
lines=text.splitlines();lines=[('| 37 | `'+mapping['37'][0]+'` (passed in focused delta) |') if l.startswith('| 37 |') else l for l in lines];text='\n'.join(lines)+'\n'
text=text.replace('- Participation-source provenance is the retained September independent review, copied as participation-source-review-235117.json. Its named original temporary raw file is absent; no fresh raw/live qualification is claimed.','- Claude sources are drafted and unqualified under the recorded owner ruling. The written September review and FINDING describe fields; the JSON review summary does not. Raw output is unavailable, so retained raw-output provenance is NOT satisfied. Native use stays gated on exact-build qualification with raw output retained by dossier path/digest.')
text+='\n## Current R1–R4 delta\n\n| Correction | Exact focused tests |\n| --- | --- |\n'
for key in ['R1','R2','R3','R4']:
 text+='| '+key+' | '+'<br>'.join('`'+t+'`' for t in mapping[key])+' |\n'
text+='\nR1 exercises a real failed launch delivery and the manager’s durable preparation ending, then an explicitly recorded successor through normal home acquisition and typed mount. This tests the home release boundary; it does not add or claim an automatic Job retry. Its negative interrupts the real adapter start after journalled intent. R2 ran the whole home module under `/home/sl/src/baton/work/scratch/w385965-n1n2/test-roots`. R3 preserves lifecycle state and creates no owner item; reason rendering is shared by status/monitor. R4 also includes the documentation correction and native qualification gate, inspected rather than asserted by a prose-mirroring test.\n'
(d/'PROOF-TABLE-N1N2-385982.md').write_text(text)
print(json.dumps({'candidate':candidate,'full_paths':len(files),'delta_paths':len(delta),'archive':sha((e/'candidate-files.tar.gz').read_bytes()),'delta_archive':sha((e/'delta-files.tar.gz').read_bytes()),'tests':summary['passed'],'seconds':summary['duration_seconds']}))
