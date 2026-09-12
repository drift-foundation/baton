"""Run reviewed offline tests and retain independent process spending."""
from pathlib import Path
import json, os, subprocess, sys, time
ROOT = Path('/home/sl/src/baton')
OUT = Path(__file__).resolve().parent
PROOF = OUT.parents[1]
env = dict(os.environ, PYTHONPATH=str(ROOT / 'v12/python/src'), PYTHONDONTWRITEBYTECODE='1')
commands = {
    'adapter': [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'v12/python/tests/manager', '-p', 'test_claude_agent.py', '-v'],
    'package': [sys.executable, '-B', str(PROOF / 'prepared-148870/verify_offline.py')],
    'worker-entry': [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'v12/python/tests/manager', '-p', 'test_worker_image.py', '-v'],
}
results = {}
for name, command in commands.items():
    started = time.monotonic()
    with (OUT / (name + '.txt')).open('w') as log:
        finished = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    results[name] = {'returncode': finished.returncode, 'seconds': time.monotonic() - started, 'command': command}
    (OUT / 'tests.json').write_text(json.dumps(results, indent=2) + '\n')
    print(name, json.dumps(results[name]), flush=True)
    if finished.returncode:
        raise SystemExit(finished.returncode)
