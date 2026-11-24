from pathlib import Path
import json,hashlib,subprocess,tarfile,stat,re
root=Path('/home/sl/src/baton'); repo=root/'work/scratch/w385965-n1n2/repo'; dossier=root/'work/records/2026/11/finding-v12-native-provider-selection';e=dossier/'evidence/implementation-385975'
sha=lambda b:hashlib.sha256(b).hexdigest()
runs=['compatibility-1','interrupted-proof']+[f'finite-{i:02d}' for i in range(1,35)]+['completion-proof','sharing-proof']
outcomes={};sources={};duration=0;eventpasses=0;runrows=[]
for n in runs:
 p=e/(n+'.accounting-corrected.json')
 if not p.exists(): p=e/(n+'.summary.json')
 s=json.loads(p.read_text());duration+=s['duration_seconds'];eventpasses+=s['passed']
 for test,result in s['outcomes'].items():
  if result=='ok':outcomes[test]='passed';sources.setdefault(test,[]).append(n)
 assert not s['source_drift'] and not s['duplicates'] and not s['uncollected']
 if n!='compatibility-1': assert not s['nonpassing'] and not s['unaccounted'] and s['exit_status']==0
 runrows.append({'name':n,'ledger':p.name,'collected':s['collected'],'passed':s['passed'],'exit_status':s['exit_status'],'seconds':s['duration_seconds']})
expected=set(json.loads((e/'compatibility-1.collection.json').read_text()))
for name in ['completion-proof','sharing-proof']: expected.update(json.loads((e/(name+'.collection.json')).read_text()))
assert set(outcomes)==expected
ledger={'selection':'20 affected compatibility modules plus 8 added completion proofs; focused test-one, not full suite or group run','groups':['manager-pure','tools-pure','job_manager'],'collected_unique':len(expected),'executed_unique':len(outcomes),'passed_unique':len(outcomes),'failed':0,'errors':0,'skipped':0,'unaccounted':[],'pass_events':eventpasses,'intentional_repeated_passes':eventpasses-len(outcomes),'summed_run_seconds_including_timeout':duration,'duration_note':'Sum of measured test subprocess durations, not elapsed wall time; finite batches run two concurrently. Earlier development runs are separate retained evidence.','runs':runrows,'outcomes':outcomes,'evidence_by_test':sources}
(e/'joined-accounting.json').write_text(json.dumps(ledger,indent=2,sort_keys=True)+'\n')
paths=set(subprocess.check_output(['git','diff','--name-only','--','v12'],cwd=repo,text=True).splitlines())|set(subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','v12'],cwd=repo,text=True).splitlines())
files=[]
for name in sorted(paths):
 p=repo/name;assert p.is_file() and not p.is_symlink();raw=p.read_bytes();files.append({'path':name,'bytes':len(raw),'mode':oct(stat.S_IMODE(p.stat().st_mode)),'sha256':sha(raw)})
context={p.name:sha(p.read_bytes()) for p in sorted((e/'context').iterdir()) if p.is_file()}
identity={'base':'9f9790222dfd004bc8f19d5c378c3acdb00fd4ca','files':files,'context':context}
canonical=json.dumps(identity,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
candidate='sha256:'+sha(canonical)
manifest=dict(identity,candidate=candidate,claim=385975,work='W385965',algorithm='sha256 of UTF-8 JSON of {base,files,context}; sort_keys=True, separators=(comma,colon), ensure_ascii=False; files sorted by path',status='candidate for independent K review, not accepted or imported')
(e/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
with tarfile.open(e/'candidate-files.tar.gz','w:gz') as tar:
 for f in files: tar.add(repo/f['path'],arcname=f['path'],recursive=False)
with tarfile.open(e/'candidate-files.tar.gz') as tar:
 assert {x.name for x in tar.getmembers()}==set(paths)
 for f in files:
  member=tar.getmember(f['path']);assert sha(tar.extractfile(member).read())==f['sha256'];assert oct(member.mode)==f['mode']
(e/'candidate-files.tar.gz.sha256').write_text(sha((e/'candidate-files.tar.gz').read_bytes())+'  candidate-files.tar.gz\n')
(e/'tracked.patch').write_bytes(subprocess.check_output(['git','diff','--binary','--','v12'],cwd=repo))
check=subprocess.run(['git','diff','--check'],cwd=repo,capture_output=True);(e/'diff-check.log').write_bytes(check.stdout+check.stderr);assert check.returncode==0
mapping=json.loads(Path('/tmp/w385965-proof-map.json').read_text());mapping['32'].append('test_32_failed_holder_release_and_return_from_another_job_preserve_bytes');mapping['32a'].append('test_32_failed_holder_release_and_return_from_another_job_preserve_bytes');mapping['41'].append('test_41_second_job_uses_delivery_not_first_jobs_refreshed_seed');mapping['45'].append('test_45_same_seed_reference_allows_two_workers_and_two_jobs')
resolved={}
for number,patterns in mapping.items():
 resolved[number]=[]
 for pattern in patterns:
  matches=sorted(t for t in outcomes if t.startswith(pattern+'.') or t.endswith('.'+pattern))
  assert matches,(number,pattern)
  resolved[number]+=matches
(e/'proof-table.json').write_text(json.dumps(resolved,indent=2)+'\n')
lines=['# W385965 N1/N2 and owner-B proof table','',f'Candidate: `{candidate}`. Base: `{manifest["base"]}`.','',f'Joined accounting: **{len(outcomes)}/{len(expected)} unique tests passed**, zero failures/errors/skips/unaccounted. See `evidence/implementation-385975/joined-accounting.json` for per-test run locators, duration and exact collection.','', 'All provider/engine behavior is explicitly simulated at its normal boundary; no image, daemon, credential registry, provider network or native execution is qualified. Real local owners, stores, worker entry, disposable Git, output freezing, custody and recovery handoff are exercised.','', '| Proof | Named deterministic evidence (all passed) |','| --- | --- |']
for number,ids in resolved.items():
 if len(ids)>30:
  pattern=mapping[number][0] if len(mapping[number])==1 else ' / '.join(mapping[number]);shown=f'`{pattern}` ({len(ids)} exact IDs enumerated in proof-table.json)'
 else: shown='<br>'.join('`'+i+'`' for i in ids)
 lines.append(f'| {number} | {shown} |')
lines+=['','## Scope of the evidence','','- 17 simulates a pre-change output by removing the attribution member through the real worker/freeze path; it does not execute an old container image.','- 25 simulates a Codex table row for shared-policy lane admission. N3/N4 inventory and a real Codex adapter remain outside this slice; 44 tests the shared closed environment and typed failure path, not live Codex authentication.','- 32/32a combine connected normal ending/correction/removal/restart with the home owner’s explicit failed-holder and unrelated-Job mount proofs. A failed terminal alone cannot authorize another writer.','- 35 exercises real cleanup, frozen manifests and custody exclusion with marker/sentinel bytes, and verifies retained home state. It does not claim a new live orphan-sweep qualification.','- 39 injects a crash after the durable holder record and before home creation, then replays the same holder.','- 45 admits two synthetic Jobs and two seeded workers using the same configured credential profile; separate home/seed tests prove isolation. No claim about provider account concurrency is made.','- Owner-B B1/B7 use the provider-free publication path; B6 reopens the durable control store and repeats admission/handoff without another publisher. B8 retains all 274 legacy recovery-admission/execution passes.','- Participation-source provenance is the retained September independent review, copied as participation-source-review-235117.json. Its named original temporary raw file is absent; no fresh raw/live qualification is claimed.','']
(dossier/'PROOF-TABLE-N1N2-385975.md').write_text('\n'.join(lines))
print(json.dumps({'candidate':candidate,'paths':len(files),'archive_sha256':sha((e/'candidate-files.tar.gz').read_bytes()),'unique_passes':len(outcomes),'pass_events':eventpasses,'summed_seconds':duration}))
