"""Run ONE shutdown-matrix mode exactly as the Composition test does (diagnostic driver)."""
import json, os, subprocess, sys, time
from pathlib import Path
sys.path[:0] = ['src', '.']
from tests.manager import shutdown_fixture
source = Path.cwd().resolve().parents[1]
mode, output = sys.argv[1], Path(sys.argv[2])
root = output / mode
root.mkdir(parents=True)
shutdown_fixture.prepare(source, root, mode)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=os.pathsep.join([str(source / 'v12/python'), str(source / 'v12/python/src')]))
started = time.monotonic()
with (root / 'outer.log').open('w') as log:
    child = subprocess.Popen([sys.executable, '-B', str(Path(shutdown_fixture.__file__).resolve()), '--fixture', str(source), '--packet', str(root / 'packet.json')], env=env, stdout=log, stderr=subprocess.STDOUT)
    code = child.wait(timeout=30)
print('mode', mode, 'exit', code, 'seconds', round(time.monotonic() - started, 2))
for line in (root / 'events.jsonl').read_text().splitlines():
    row = json.loads(line)
    if row['event'].startswith('token_') or row['event'] in ('fake_engine', 'blocked_serving_sweep'):
        print(' ', row['event'], {k: v for k, v in row.items() if k not in ('event', 'monotonic', 'pid', 'thread')})
