"""Supported group recipe, retained source headers and reconciled JSON ledger.

The actual runner supplies --account. On an all-passing run its accounting
assertion establishes expected==executed==passed; retain those exact IDs here.
"""
from pathlib import Path
import subprocess,os,sys,json,time,signal,re
repo=Path('/home/sl/src/baton/work/scratch/w385830-join-386051/repo')
e=Path(__file__).resolve().parent
group=sys.argv[1]; py='/home/sl/.local/state/baton-v12-venv/bin/python'
roots=Path('/var/tmp')/('baton-n4a-386051-'+group);roots.mkdir(exist_ok=True)
env=dict(os.environ,PYTHONPATH='src',BATON_V12_DISK_ROOT=str(roots),TMPDIR=str(roots))
identity=[py,'-m','tools.source_identity','--declared','v12']
def source(suffix):
 r=subprocess.run(identity,cwd=repo/'v12/python',env=env,capture_output=True,check=True)
 (e/(group+'.source-'+suffix+'.json')).write_bytes(r.stdout);return r.stdout
before=source('before')
c=subprocess.run([py,'tools/parallel_test.py','--group',group,'--print-ids'],cwd=repo/'v12/python',env=env,capture_output=True,check=True)
(e/(group+'.collection.log')).write_bytes(c.stdout+c.stderr)
expected=[s for s in c.stdout.decode().splitlines() if s.startswith('tests.')]
command=['just','test-group',group,'4'];start=time.monotonic()
with (e/(group+'.stdout.log')).open('wb') as out,(e/(group+'.stderr.log')).open('wb') as err:
 p=subprocess.Popen(command,cwd=repo/'v12',env=env,stdout=out,stderr=err,start_new_session=True)
 header={'command':command,'cwd':str(repo/'v12'),'interpreter':py,'group':group,'bound_seconds':600,'pid':p.pid,'collected':len(expected),'base':'ac034bc1c9fae525b94a1a5f21d9721c677dc39e'}
 (e/(group+'.header.json')).write_text(json.dumps(header,indent=2)+'\n')
 try:p.wait(timeout=600)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=20)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
after=source('after');text=(e/(group+'.stdout.log')).read_text()
account=[s for s in text.splitlines() if s.startswith(('collected ','[accounting]'))]
passed=bool(p.returncode==0 and before==after and any(s.endswith('-> OK') for s in account))
summary={'group':group,'exit_status':p.returncode,'elapsed_seconds':time.monotonic()-start,'collected_ids':expected,'accounting_lines':account,'source_drift':before!=after,'passed':passed,'ledger_provenance':'IDs collected independently; all-pass equality established by actual supported --account runner','passed_ids':expected if passed else None}
(e/(group+'.summary.json')).write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('collected_ids','passed_ids')}),flush=True)
sys.exit(0 if passed else 1)
