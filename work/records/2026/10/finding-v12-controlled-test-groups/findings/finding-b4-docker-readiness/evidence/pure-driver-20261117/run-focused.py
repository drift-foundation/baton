"""Focused pure tests on the accepted snapshot; no Docker or provider execution."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,tempfile,time
HERE=Path(__file__).resolve().parent
REPO=next(p for p in HERE.parents if (p/'AGENTS.md').is_file())
m=json.loads((HERE/'source-restored.json').read_text());SNAP=REPO/m['snapshot']
label=sys.argv[1];assert label.isalnum();out=HERE/label;out.mkdir()
root=Path(tempfile.mkdtemp(prefix='baton-w384944-pure-',dir='/var/tmp'));os.chown(root,-1,1001);os.chmod(root,0o2770)
env=dict(os.environ,TMPDIR=str(root),BATON_V12_DISK_ROOT=str(root),BATON_V12_WORKSPACE_GROUP='1001',PYTHONDONTWRITEBYTECODE='1',W384944_SNAPSHOT=str(SNAP),W384944_LEDGER=str(out/'ledger.json'))
def hashes():return {p:hashlib.sha256((SNAP/p).read_bytes()).hexdigest() for p in m['files']}
ids=sys.argv[2:] or [line.split('\t')[1] for line in (HERE.parent/'remaining-engine-20261117/remaining-pure-driver-historical.tsv').read_text().splitlines()[1:]]
argv=['just','test-one',*ids] if label=='baseline' else ['/home/sl/.local/state/baton-v12-venv/bin/python',str(HERE/'audit-tests.py'),*ids]
before=hashes();(out/'source-before.json').write_text(json.dumps(before,indent=2)+'\n');start=time.monotonic();timedout=False
with (out/'focused.log').open('x') as log:
 proc=subprocess.Popen(argv,cwd=SNAP/'v12',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:proc.wait(timeout=600)
 except subprocess.TimeoutExpired:
  timedout=True;os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=10)
elapsed=time.monotonic()-start;after=hashes();leftovers=sorted(str(p.relative_to(root)) for p in root.rglob('*'))
if not leftovers:root.rmdir()
result=dict(argv=argv,exit=proc.returncode,timed_out=timedout,seconds=elapsed,source_drift=[p for p in before if before[p]!=after[p]],temporary_root=str(root),leftovers=leftovers,root_removed=not root.exists())
(out/'source-after.json').write_text(json.dumps(after,indent=2)+'\n');(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));sys.exit(proc.returncode or bool(leftovers) or bool(result['source_drift']))
