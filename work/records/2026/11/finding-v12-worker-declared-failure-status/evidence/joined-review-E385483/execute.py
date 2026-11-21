from pathlib import Path
import subprocess,os,time,json,sys
r=Path('/home/sl/src/baton');e=Path(__file__).resolve().parent;s=r/'work/scratch/w385424-joined-review';label=sys.argv[1];script='run_inventory.py' if label=='inventory' else 'run_joined_focused.py';env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='src:.',TMPDIR=str(s/'tmp'),BATON_V12_DISK_ROOT=str(s/'tmp'),BATON_V12_STACK_TEST_ROOT=str(s/'tmp'),PATH=str(e/'no-git')+':'+os.environ['PATH']);t=time.monotonic()
with (e/(label+'.log')).open('w') as out:
 p=subprocess.run([str(r/'.venv/bin/python'),str(e/script)],cwd=s/'candidate/v12/python',env=env,stdout=out,stderr=subprocess.STDOUT,timeout=180)
(e/(label+'.json')).write_text(json.dumps({'exit':p.returncode,'wall_seconds':time.monotonic()-t,'script':script},indent=2));print((e/(label+'.json')).read_text());print('\n'.join((e/(label+'.log')).read_text().splitlines()[-7:]))
