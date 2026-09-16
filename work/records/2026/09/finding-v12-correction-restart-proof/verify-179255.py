"""Selected deterministic B run: 180s plus TERM5/KILL5 and group exclusion."""
import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

record = Path(__file__).resolve().parent
repo = next(p for p in record.parents if (p / 'v12/python/requirements.lock').exists())
number = sys.argv[1]
if not number.isdecimal(): raise SystemExit('decimal run identity required')
selectors = sys.argv[2:] or ['tests.manager.test_provider_context', 'tests.manager.test_provider_context_delivery']
allowed = ('tests.manager.test_provider_context', 'tests.manager.test_provider_context_delivery', 'tests.manager.test_claude_context', 'tests.manager.test_launch', 'tests.manager.test_oci', 'tests.manager.test_claude_agent', 'tests.tools.test_single_worker', 'tests.tools.test_stage_execution')
if selectors != ['media-conflict'] and any(not any(s == a or s.startswith(a+'.') for a in allowed) for s in selectors): raise SystemExit('outside selected test scope')
paths = [x['path'] for x in json.loads((record/'BASE-179255.json').read_bytes())['files'] if (repo/x['path']).exists()]

before = {p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths}
env = dict(os.environ, PYTHONPATH='src:tools:.', PYTHONDONTWRITEBYTECODE='1')
start = time.monotonic()
with (record / ('run-179255-' + number + '.log')).open('xb') as log:
 command = [sys.executable, str(record/'reproduce-media-conflict-179255.py')] if selectors == ['media-conflict'] else [sys.executable, '-m', 'unittest', '-v', *selectors]
 p = subprocess.Popen(command, cwd=repo/'v12/python', env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
 timed_out = False
 try: status = p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timed_out = True
  os.killpg(p.pid, signal.SIGTERM)
  try: status = p.wait(timeout=5)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid, signal.SIGKILL)
   status = p.wait(timeout=5)
 try:
  os.killpg(p.pid, 0)
  os.killpg(p.pid, signal.SIGTERM)
  deadline = time.monotonic() + 5
  while time.monotonic() < deadline:
   try: os.killpg(p.pid, 0)
   except ProcessLookupError: break
   time.sleep(.02)
  else: os.killpg(p.pid, signal.SIGKILL)
 except ProcessLookupError: pass
 try: os.killpg(p.pid, 0); gone = False
 except ProcessLookupError: gone = True
 result = {'claim':179255,'run':number,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds':time.monotonic()-start,'status':status,'timeout':timed_out,'group_gone':gone,'selectors':selectors,'python':sys.version,'dependencies':{n:importlib.metadata.version(n) for n in ('jsonschema','jsonschema-specifications','referencing','attrs','rpds-py')},'before':before,'after':{p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths}}
 (record / ('run-179255-' + number + '.json')).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ('run','seconds','status','timeout','group_gone')}))
 raise SystemExit(0 if status == 0 and gone and not timed_out else 1)
