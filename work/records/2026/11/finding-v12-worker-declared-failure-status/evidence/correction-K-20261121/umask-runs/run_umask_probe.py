"""One confined run: <label> <tree> <umask>. Fresh disposable fixture roots only; host read-only."""
from pathlib import Path
import subprocess,os,time,json,tempfile,sys,shutil
label,tree,mask=sys.argv[1:4]
P=Path('/var/tmp/baton-v12-w385424-fix');base=P/'verification-git';base.mkdir(exist_ok=True)
run=Path(tempfile.mkdtemp(prefix=f'run-{label}-',dir=base));fixtures=run/'fixtures';fixtures.mkdir();guard=run/'guard';guard.mkdir()
GUARD_SRC=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-monitor-running-deadlines/evidence/continuation-385443/guard/git')
shutil.copyfile(GUARD_SRC,guard/'git');(guard/'git').chmod(0o755);(guard/'guard-config.json').write_text(json.dumps({'root':str(fixtures),'log':str(run/'git.jsonl')}))
cwd=Path(tree)/'v12/python'
env=dict(os.environ,PATH=str(guard)+':'+os.environ['PATH'],RUN_ROOT=str(run),TMPDIR=str(fixtures),BATON_V12_DISK_ROOT=str(fixtures),BATON_V12_STACK_TEST_ROOT=str(fixtures),PYTHONPATH='src:.',PYTHONDONTWRITEBYTECODE='1',HOME=str(run),PROBE_UMASK=mask)
args=['bwrap','--ro-bind','/','/','--bind',str(run),str(run),'--unshare-net','--unshare-pid','--die-with-parent','--new-session','--cap-drop','ALL','--proc','/proc','--dev','/dev','--chdir',str(cwd),'--','/home/sl/.local/state/baton-v12-venv/bin/python',str(P/'umask_fixture_runner.py')]
t=time.monotonic();p=subprocess.run(args,env=env,capture_output=True,text=True,timeout=300);wall=time.monotonic()-t
out=P/'results'/label;out.mkdir(parents=True,exist_ok=True)
(out/'run.log').write_text(p.stdout+p.stderr)
(out/'run.json').write_text(json.dumps({'label':label,'tree':tree,'umask':mask,'argv':args,'exit_code':p.returncode,'wall_seconds':wall,'run_root':str(run),'guard_sha256':__import__('hashlib').sha256(GUARD_SRC.read_bytes()).hexdigest()},indent=2))
for name in ('git.jsonl','git-trace2.jsonl','diagnostics.jsonl','posture.jsonl'):
 if (run/name).exists():shutil.copyfile(run/name,out/name)
print(label,'exit',p.returncode,'wall %.1fs'%wall);print(p.stderr[-600:])
