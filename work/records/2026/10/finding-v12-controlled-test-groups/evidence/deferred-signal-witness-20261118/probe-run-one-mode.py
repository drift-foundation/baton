"""Ad-hoc driver: run ONE shutdown-matrix mode through the real fixture and print its journal timeline."""
import json, os, subprocess, sys, time
from pathlib import Path
source = Path('/home/sl/src/baton')
sys.path[:0] = [str(source / 'v12/python/src'), str(source / 'v12/python')]
from tests.manager import shutdown_fixture
mode = sys.argv[1]
root = Path(sys.argv[2]) / mode
root.mkdir(parents=True)
shutdown_fixture.prepare(source, root, mode)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=os.pathsep.join([str(source / 'v12/python'), str(source / 'v12/python/src')]))
started = time.monotonic()
with (root / 'outer.log').open('w') as log:
    child = subprocess.Popen([sys.executable, '-B', str(Path(shutdown_fixture.__file__).resolve()), '--fixture', str(source), '--packet', str(root / 'packet.json')], env=env, stdout=log, stderr=subprocess.STDOUT)
    code = child.wait(timeout=20)
elapsed = time.monotonic() - started
events = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
origin = events[0]['monotonic']
print('mode', mode, 'code', code, 'elapsed %.2f' % elapsed, 'unreached', shutdown_fixture.unreached(mode, events))
for row in events:
    if row['event'] == 'trace' and row['function'] not in ('_handle', 'defer', 'install', 'restore', 'start', 'main', 'child_main', 'supervise'):
        continue
    extra = {k: v for k, v in row.items() if k not in ('event', 'monotonic', 'pid', 'thread')}
    print('%7.3f pid=%d %s %s' % (row['monotonic'] - origin, row['pid'], row['event'], json.dumps(extra)[:160]))
