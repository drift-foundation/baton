import os,json,re,subprocess,time,hashlib,sys,signal
from pathlib import Path
repo=Path('/home/sl/src/baton/work/scratch/w385965-r1a-prompt')
evidence=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/correction-prompt-r1a')
python='/home/sl/.local/state/baton-v12-venv/bin/python'
modules=['tests.manager.test_claude_agent', 'tests.manager.test_provider_home', 'tests.manager.test_model_attribution', 'tests.tools.test_provider_selection', 'tests.job_manager.test_provider_attribution_recovery', 'tests.tools.test_pool', 'tests.manager.test_launch', 'tests.manager.test_oci', 'tests.manager.test_worker_entry', 'tests.tools.test_single_worker', 'tests.tools.test_stage_execution', 'tests.job_manager.test_review_driver', 'tests.job_manager.test_publication_recovery_admission', 'tests.job_manager.test_publication_recovery_execution', 'tests.manager.test_attempt_logs', 'tests.manager.test_attempts', 'tests.tools.test_job_observation', 'tests.tools.test_job_viewer', 'tests.tools.test_parallel_runner', 'tests.job_manager.test_scheduling']
env=dict(os.environ,PYTHONPATH='src')
identity=[python,'-m','tools.source_identity','--declared','v12']

os.environ['BATON_V12_DISK_ROOT']='/home/sl/src/baton/work/scratch/w385965-r1a-test-roots'
os.environ['TMPDIR']=os.environ['BATON_V12_DISK_ROOT']
Path(os.environ['TMPDIR']).mkdir(exist_ok=True)
env.update(BATON_V12_DISK_ROOT=os.environ['TMPDIR'],TMPDIR=os.environ['TMPDIR'])
name=sys.argv[1]; names=json.loads(Path(sys.argv[2]).read_text()); bound=int(sys.argv[3])
for tag in ['before']:
 r=subprocess.run(identity,cwd=repo/'v12/python',env=env,capture_output=True); (evidence/f'{name}.source-{tag}.json').write_bytes(r.stdout)
 if r.returncode: sys.exit(r.returncode)
collector='import unittest,json,sys; flatten=lambda s: [s.id()] if isinstance(s,unittest.TestCase) else [i for x in s for i in flatten(x)]; print(json.dumps(flatten(unittest.TestLoader().loadTestsFromNames(sys.argv[1:]))))'
r=subprocess.run([python,'-c',collector,*names],cwd=repo/'v12/python',env=env,capture_output=True)
(evidence/f'{name}.collection.json').write_bytes(r.stdout)
if r.returncode: sys.exit(r.returncode)
expected=json.loads(r.stdout);command=['just','--justfile','v12/justfile','test-one',*names]
header={'command':command,'interpreter':python,'base':'9f9790222dfd004bc8f19d5c378c3acdb00fd4ca','groups':['manager-pure','tools-pure'],'collected':len(expected),'bound_seconds':bound,'disk_root':os.environ['BATON_V12_DISK_ROOT'],'TMPDIR':os.environ['TMPDIR']}
start=time.monotonic();timed=False
with (evidence/f'{name}.stdout.log').open('wb') as out,(evidence/f'{name}.stderr.log').open('wb') as err:
 p=subprocess.Popen(command,cwd=repo,stdout=out,stderr=err,start_new_session=True)
 header.update(pid=p.pid,pgid=p.pid);(evidence/f'{name}.header.json').write_text(json.dumps(header,indent=2)+'\n')
 try: p.wait(timeout=bound)
 except subprocess.TimeoutExpired: timed=True;os.killpg(p.pid,signal.SIGKILL);p.wait()
elapsed=time.monotonic()-start
r=subprocess.run(identity,cwd=repo/'v12/python',env=env,capture_output=True);(evidence/f'{name}.source-after.json').write_bytes(r.stdout)
results={};duplicates=[];current=None
for line in (evidence/f'{name}.stderr.log').read_text().splitlines():
 m=re.match(r'^(test_\S+) \(([^)]+)\)',line)
 if m:
  current=m.group(2) if m.group(2).endswith('.'+m.group(1)) else m.group(2)+'.'+m.group(1)
  if current in results: duplicates.append(current)
  results[current]='started'
 if current and (line in ('ok', 'FAIL', 'ERROR') or re.search(r'\.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$',line)): results[current]=line.rsplit('... ',1)[-1];current=None
summary={'collected':len(expected),'executed':len(results),'passed':sum(v=='ok' for v in results.values()),'exit_status':p.returncode,'timed_out':timed,'duration_seconds':elapsed,'duplicates':duplicates,'unaccounted':sorted(set(expected)-set(results)),'uncollected':sorted(set(results)-set(expected)),'nonpassing':{k:v for k,v in results.items() if v!='ok'},'source_drift':(evidence/f'{name}.source-before.json').read_bytes()!=r.stdout,'source_after_exit_status':r.returncode,'outcomes':results}
(evidence/f'{name}.summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('outcomes','unaccounted')}),flush=True)
sys.exit(124 if timed else p.returncode if p.returncode else 1 if summary['unaccounted'] or summary['nonpassing'] or summary['source_drift'] else 0)
