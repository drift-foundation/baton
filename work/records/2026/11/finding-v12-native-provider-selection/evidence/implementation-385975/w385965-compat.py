import os,json,re,subprocess,time,hashlib,sys,signal
from pathlib import Path
repo=Path('/home/sl/src/baton/work/scratch/w385965-n1n2/repo')
evidence=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/implementation-385975')
python='/home/sl/.local/state/baton-v12-venv/bin/python'
modules=['tests.manager.test_claude_agent', 'tests.manager.test_provider_home', 'tests.manager.test_model_attribution', 'tests.tools.test_provider_selection', 'tests.job_manager.test_provider_attribution_recovery', 'tests.tools.test_pool', 'tests.manager.test_launch', 'tests.manager.test_oci', 'tests.manager.test_worker_entry', 'tests.tools.test_single_worker', 'tests.tools.test_stage_execution', 'tests.job_manager.test_review_driver', 'tests.job_manager.test_publication_recovery_admission', 'tests.job_manager.test_publication_recovery_execution', 'tests.manager.test_attempt_logs', 'tests.manager.test_attempts', 'tests.tools.test_job_observation', 'tests.tools.test_job_viewer', 'tests.tools.test_parallel_runner', 'tests.job_manager.test_scheduling']
env=dict(os.environ,PYTHONPATH='src')
identity=[python,'-m','tools.source_identity','--declared','v12']
for tag in ['before']:
    r=subprocess.run(identity,cwd=repo/'v12/python',env=env,capture_output=True)
    (evidence/f'compatibility-1.source-{tag}.json').write_bytes(r.stdout)
    if r.returncode:
        print(r.stderr.decode());sys.exit(r.returncode)
collector='import unittest,json,sys; s=unittest.TestLoader().loadTestsFromNames(sys.argv[1:]); flatten=lambda s: [x.id() for x in s] if isinstance(s,unittest.TestCase) else [i for x in s for i in ([x.id()] if isinstance(x,unittest.TestCase) else flatten(x))]; print(json.dumps(flatten(s)))'
r=subprocess.run([python,'-c',collector,*modules],cwd=repo/'v12/python',env=env,capture_output=True)
(evidence/'compatibility-1.collection.json').write_bytes(r.stdout)
if r.returncode:
    print(r.stderr.decode());sys.exit(r.returncode)
expected=json.loads(r.stdout)
command=['just','--justfile','v12/justfile','test-one',*modules]
start=time.monotonic();timed=False
with (evidence/'compatibility-1.log').open('wb') as log:
    log.write((json.dumps({'command':command,'interpreter':python,'base':'9f9790222dfd004bc8f19d5c378c3acdb00fd4ca','modules':modules,'collected':len(expected),'groups':['manager-pure','tools-pure','job-manager'],'accounting':'focused test-one collection and verbose outcome reconciliation; not full/group accounting'})+'\n').encode());log.flush()
    p=subprocess.Popen(command,cwd=repo,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try: p.wait(timeout=180)
    except subprocess.TimeoutExpired:
        timed=True;os.killpg(p.pid,signal.SIGKILL);p.wait()
elapsed=time.monotonic()-start
r=subprocess.run(identity,cwd=repo/'v12/python',env=env,capture_output=True)
(evidence/'compatibility-1.source-after.json').write_bytes(r.stdout)
text=(evidence/'compatibility-1.log').read_text()
results={};duplicates=[];current=None
for line in text.splitlines():
    m=re.match(r'^(test_\S+) \(([^)]+)\)',line)
    if m:
        current=m.group(2) if m.group(2).endswith('.'+m.group(1)) else m.group(2)+'.'+m.group(1)
        if current in results: duplicates.append(current)
        results[current]='started'
    if current and re.search(r'\.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$',line):
        results[current]=line.rsplit('... ',1)[1];current=None
summary={'selected_modules':modules,'collected':len(expected),'executed':len(results),'passed':sum(v=='ok' for v in results.values()),'exit_status':p.returncode,'timed_out':timed,'duration_seconds':elapsed,'duplicates':duplicates,'unaccounted':sorted(set(expected)-set(results)),'uncollected':sorted(set(results)-set(expected)),'nonpassing':{k:v for k,v in results.items() if v!='ok'},'source_drift':(evidence/'compatibility-1.source-before.json').read_bytes()!=r.stdout,'source_after_exit_status':r.returncode,'outcomes':results}
(evidence/'compatibility-1.summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='outcomes'}))
