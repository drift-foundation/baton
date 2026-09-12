"""Read-only run4 diagnosis; never opens a store or credential, starts a runtime, or changes the target."""
import collections, datetime, hashlib, json, pathlib, stat, subprocess, sys, time
started = time.monotonic()
ROOT = pathlib.Path('/home/sl/src/baton')
RUN = pathlib.Path('/home/sl/.local/state/baton/v12/w71879-run4')
OUT = pathlib.Path(__file__).resolve().parent
PROOF = OUT.parent.parent
ATTEMPT = 'attempt-29cb33dbf7b0028b039a5f8d045bffafa0163f8dfba26681d8b69bc761529380'
BUNDLE = RUN / 'state/integration-bundles' / ATTEMPT
def read(p): return json.loads(p.read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(name, *args):
    p = RUN / name
    done = subprocess.run(['git', '--no-optional-locks', '-c', 'safe.directory='+str(p), '-C', str(p), *args], capture_output=True, text=True, timeout=10)
    assert done.returncode == 0, done.stderr
    return done.stdout
manifest = read(PROOF/'evidence/run4-freeze-145461/candidate-manifest.json')
source_checks = {}
for name in ['v12/worker/integration_contract.py','v12/worker/integration_entry.py','v12/worker/integration_workload.py']:
    source_checks[name] = digest(ROOT/name) == manifest['provider_chain'][name]['sha256']
assert all(source_checks.values())
envelope = read(BUNDLE/'integration.json')
targets = []
for row in envelope['paths']:
    p = RUN/'target'/row['path']
    s = p.lstat()
    targets.append(dict(path=row['path'], regular=stat.S_ISREG(s.st_mode), mode=oct(stat.S_IMODE(s.st_mode)), sha256=digest(p), candidate_matches=digest(p)==row['candidate']['blob'], bytes=s.st_size, modified_at=datetime.datetime.fromtimestamp(s.st_mtime,datetime.timezone.utc).isoformat()))
samples = [json.loads(x) for x in (RUN/'evidence/samples.jsonl').read_text().splitlines()]
status = read(OUT/'canonical-status.json')
artifacts = []
for job in status['jobs']:
    for stage in job['stages']:
        for artifact in stage['artifacts'] or []:
            base = pathlib.Path(artifact['locator'].removeprefix('file://'))
            filename = 'result.json' if artifact['output_name']=='proposal' else 'report.json' if artifact['output_name']=='findings' else 'review.json'
            p = base/filename
            document = read(p)
            artifacts.append(dict(stage=stage['stage_id'],path=str(p),sha256=digest(p),document=document))
sys.path.insert(0,str(ROOT/'v12/worker'))
import integration_contract as contract
import integration_workload as workload
authority = read(BUNDLE/'evidence/authority.json')
assignment = read(RUN/'state/integration/integration/assignment/assignment.json')
prompt = workload.compose_prompt(instructions=(BUNDLE/'instructions.txt').read_bytes(),bundle_root='/input/source',target_root='/target',report_place='/tmp/RECONSTRUCTED-NOT-ACTUAL/integration-report/report.json',assignment=assignment,assignment_digest=envelope['assignment_digest'],bundle_digest=workload.measure_bundle(str(BUNDLE)),rows=envelope['paths'],authority=authority['paths'],scope=authority['scope']['test_scope'],documents=authority['review']['documents'],verification=workload.accepted_verification({'tests.json':read(BUNDLE/'evidence/tests.json')}))
(OUT/'reconstructed-prompt.txt').write_text(prompt)
missing = [key for key in contract.REPORT_MEMBERS if '"'+key+'"' not in prompt]
result = dict(observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),run_result=read(RUN/'evidence/run-result.json'),total_four_failed_wall_seconds=560.1007706070232+272.6205856000015,source_checks=source_checks,target=targets,git={name:dict(revision=git(name,'rev-parse','HEAD','HEAD^{tree}').splitlines(),status=git(name,'status','--porcelain=v1')) for name in ('source','target')},integration_result_entries=sorted(p.name for p in (RUN/'state/integration/integration/result').iterdir()),workspace_entries=sorted(p.name for p in (RUN/'storage'/ATTEMPT/'workspace').iterdir()),samples=dict(count=len(samples),first_wall=samples[0]['wall_seconds'],last_wall=samples[-1]['wall_seconds'],stats=dict(collections.Counter(s['docker_stats']['state'] for s in samples)),last_claims=samples[-1]['claims']),artifacts=artifacts,prompt=dict(reconstructed=True,private_report_path_placeholder=True,sha256=digest(OUT/'reconstructed-prompt.txt'),report_members_not_explicitly_named_as_JSON_keys=missing,report_schema_named=contract.REPORT_SCHEMA in prompt,contract_members=list(contract.REPORT_MEMBERS),contract_outcomes=list(contract.REPORT_OUTCOMES),contract_phases=list(contract.REPORT_PHASES),contract_codes=list(contract.REPORT_CODES)),elapsed_seconds=time.monotonic()-started)
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('artifacts','samples')},indent=2))
print('Artifact records:',len(artifacts),'samples:',len(samples))
