import os,sys,subprocess,json,time,signal,re,hashlib
from pathlib import Path
out=Path(__file__).resolve().parent
name,seconds,where,*argv=sys.argv[1:];limit=int(seconds);where=str(Path(where).resolve())
scratch=Path(where).parents[2]/'w385695-review-385926-tests' if where.endswith('/v12/python') else Path(where)/'verification-scratch'
scratch.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.update(BATON_V12_DISK_ROOT=str(scratch),BATON_V12_STACK_TEST_ROOT=str(scratch),TMPDIR=str(scratch))
start=time.monotonic()
with (out/(name+'.log')).open('w') as log:
 log.write(json.dumps({'cwd':where,'argv':argv,'timeout_seconds':limit,'scratch':str(scratch)})+'\n');log.flush()
 child=subprocess.Popen(argv,cwd=where,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 timed=False
 try: rc=child.wait(timeout=limit)
 except subprocess.TimeoutExpired:
  timed=True;os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
  rc=124
elapsed=time.monotonic()-start
text=(out/(name+'.log')).read_text();n=re.findall(r'Ran (\d+) tests? in ([\d.]+)s',text)
summary={'argv':argv,'cwd':where,'exit_status':rc,'timed_out':timed,'wall_seconds':elapsed,'unittest_summary':n[-1] if n else None,'log_sha256':hashlib.sha256(text.encode()).hexdigest()}
(out/(name+'.json')).write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary));print(text[-7000:]);sys.exit(rc)
