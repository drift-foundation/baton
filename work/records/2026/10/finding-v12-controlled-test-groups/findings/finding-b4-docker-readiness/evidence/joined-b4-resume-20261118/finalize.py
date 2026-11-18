from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;O=H.parent/'joined-b4-438eefa6-20261118'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
for name,digest in read(O/'SHA256.json').items():assert hashlib.sha256((O/name).read_bytes()).hexdigest()==digest,name
old=[read(O/('%02d'%n)/'ledger.json') for n in range(1,4)];new=[read(H/('%02d'%n)/'ledger.json') for n in range(1,11)]
expected=[i for group in read(O/'collected.json').values() for i in group];prior=[i for x in old for i in x['passed']];resumed=[i for x in new for i in x['passed']]
assert len(prior)==143 and len(resumed)==99 and len(set(expected))==242
assert not set(prior)&set(resumed) and set(prior+resumed)==set(expected)
for ledger in old+new:
 assert ledger['started']==ledger['collected'] and set(ledger['passed'])==set(ledger['collected'])
 for key in ['failed','errors','skipped','expected_failures','unexpected_successes','unaccounted','duplicates','loader_errors']:assert not ledger[key],key
 assert all(s['outcome']=='passed' for s in ledger['subtests'])
assert read(H/'summary.json')['all_passed'] and read(H/'source-before.json')==read(H/'source-after.json')==read(O/'source-after.json')
def docker(*a):return subprocess.check_output(['/usr/bin/docker',*a],text=True).splitlines()
now=set(docker('ps','-aq','--no-trunc'));images=set(docker('image','ls','-q','--no-trunc'));rs=read(H/'results.json');created={i for r in rs for i in r['created_container_ids']};assert not created&now
assert set(read(H/'containers-before.json'))<=now;assert set(read(H/'build-plan.json')['preexisting_images'])<=images
assert all(r['root_removed'] and not r['emergency_cleanup'] for r in rs)
combined=dict(commit=read(H/'source-manifest.json')['commit'],expected_ids=expected,accepted_prior_passed=prior,resumed_passed=resumed,passed=242,failed=[],errors=[],skipped=[],unaccounted=[],duplicates=[],successful_subtests=sum(len(x['subtests']) for x in old+new),prior_interruption_preserved=True,prior_evidence_hashes_unchanged=True,source_unchanged=True,all_passed=True,continuation_seconds=sum(r['seconds'] for r in rs),created_container_count=len(created),created_ids_absent=True,preexisting_containers_preserved=True,preexisting_images_preserved=True,all_task_roots_removed=True)
write(H/'combined-ledger.json',combined)
print(json.dumps({k:v for k,v in combined.items() if not isinstance(v,list)},indent=2))
