import json, os, signal, subprocess, sys, time
from pathlib import Path
home=Path(__file__).resolve().parent
label=sys.argv[1]; command=sys.argv[2:]
started=time.monotonic(); signals=[]; timed_out=False
with (home/(label+'.log')).open('x') as log:
 child=subprocess.Popen(command,cwd='/home/sl/src/baton/v12/python',env=dict(os.environ,PYTHONPATH='src:tools:.'),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try: child.wait(timeout=60)
 except subprocess.TimeoutExpired:
  timed_out=True
  for sig,grace in ((signal.SIGTERM,5),(signal.SIGKILL,5)):
   try: os.killpg(child.pid,sig); signals.append(sig.name)
   except ProcessLookupError: break
   until=time.monotonic()+grace
   while time.monotonic()<until:
    child.poll()
    try: os.killpg(child.pid,0)
    except ProcessLookupError: break
    time.sleep(.05)
   else: continue
   break
seconds=time.monotonic()-started
record=dict(command=command,cwd='/home/sl/src/baton/v12/python',PYTHONPATH='src:tools:.',seconds=seconds,exit=child.poll(),timed_out=timed_out,signals=signals,limits_seconds=[60,5,5])
(home/(label+'.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record)); print((home/(label+'.log')).read_text()[-13000:])
sys.exit(0 if record['exit']==0 and not timed_out else 1)
