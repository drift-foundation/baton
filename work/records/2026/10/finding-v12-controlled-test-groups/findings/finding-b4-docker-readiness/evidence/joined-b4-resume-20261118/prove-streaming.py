from pathlib import Path
import json,os,selectors,signal,subprocess,tempfile,time
H=Path(__file__).resolve().parent
start=time.monotonic()
with tempfile.TemporaryDirectory(prefix='w384944-stream-',dir='/var/tmp') as tmp:
 fake=Path(tmp)/'fake';fake.write_text('''#!/usr/bin/python3
import sys
print('ready',flush=True)
for line in sys.stdin:
 text=line.strip()
 if text=='finish':sys.exit(23)
 print('reply:'+text,flush=True)
 print('error:'+text,file=sys.stderr,flush=True)
''');fake.chmod(0o755)
 env=dict(os.environ,W384944_REAL_DOCKER=str(fake),ENGINE_LOG=str(H/'fake-engine.jsonl'))
 def launch():return subprocess.Popen(['/usr/bin/python3',str(H/'docker-shim.py'),'exec','--interactive','fake'],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
 def read(pipe):
  with selectors.DefaultSelector() as sel:
   sel.register(pipe,selectors.EVENT_READ);assert sel.select(3),'stream response blocked'
  return pipe.readline()
 p=launch();assert read(p.stdout)==b'ready\n'
 for frame in [b'first',b'second']:
  p.stdin.write(frame+b'\n');assert read(p.stdout)==b'reply:'+frame+b'\n';assert read(p.stderr)==b'error:'+frame+b'\n'
 p.stdin.write(b'finish\n');assert p.wait(timeout=3)==23
 for pipe in [p.stdin,p.stdout,p.stderr]:pipe.close()
 p=launch();assert read(p.stdout)==b'ready\n';p.send_signal(signal.SIGTERM);assert p.wait(timeout=3)==-signal.SIGTERM
 for pipe in [p.stdin,p.stdout,p.stderr]:pipe.close()
(H/'streaming-proof.json').write_text(json.dumps(dict(ok=True,frames=2,stdout_before_stdin_closed=True,stderr_separate=True,exit_status=23,signal_status=-15,seconds=time.monotonic()-start),indent=2)+'\n')
print('Streaming, stderr, exit status and signal passthrough proved')
