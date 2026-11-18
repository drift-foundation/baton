"""PROBE ONLY (not part of the candidate): force the controller's SIGTERM AFTER the deferred injection.

The controller process runs the real fixture with ONE gate: its SIGTERM send waits (bounded) until the
manager's journal shows `deferred_signal_returned`. The manager runs the unmodified fixture. This shows the
witness under the ordering the third owner full run most plausibly hit, in the real controller+manager
composition, and whether the manager's own serving bound leaves it enough shutdown budget there.
"""
import json, os, signal, subprocess, sys, time
from pathlib import Path
source = Path('/home/sl/src/baton')
sys.path[:0] = [str(source / 'v12/python/src'), str(source / 'v12/python')]
from tests.manager import shutdown_fixture, disk_roots

if sys.argv[1] == '--controller':
    from tools import authoring_enforcement as e
    root = Path(sys.argv[sys.argv.index('--packet') + 1]).parent
    real_signal = e.Process._signal
    def gated(self, number):
        if number == signal.SIGTERM:
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if (root / 'events.jsonl').exists() and 'deferred_signal_returned' in (root / 'events.jsonl').read_text():
                    break
                time.sleep(0.01)
            shutdown_fixture.event(root, 'probe_gate_released', waited_for='deferred_signal_returned', seen=(root / 'events.jsonl').exists() and 'deferred_signal_returned' in (root / 'events.jsonl').read_text())
        return real_signal(self, number)
    e.Process._signal = gated
    raise SystemExit(shutdown_fixture.fixture(source, sys.argv[2:]))

mode = 'absent_cleanup'
root = Path('/var/tmp/w384870-deferred-probe-late-' + sys.argv[1]) / mode
root.mkdir(parents=True)
shutdown_fixture.prepare(source, root, mode)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=os.pathsep.join([str(source / 'v12/python'), str(source / 'v12/python/src')]))
started = time.monotonic()
with (root / 'outer.log').open('w') as log:
    child = subprocess.Popen([sys.executable, '-B', __file__, '--controller', '--packet', str(root / 'packet.json')], env=env, stdout=log, stderr=subprocess.STDOUT)
    code = child.wait(timeout=20)
elapsed = time.monotonic() - started
events = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
o = events[0]['monotonic']
report = json.loads(next(root.glob('outcome.json.enforcement-*.json')).read_text())
workload = json.loads((root / 'outcome.json').read_text())
request = json.loads(next(root.glob('*.shutdown.json')).read_text())
published = [row['monotonic'] for row in events if row['event'] == 'snapshot_replaced' and row['finished']]
rows = list(report['enforcement']['attempts'].values())
print('run', sys.argv[1], 'code', code, 'elapsed %.2f' % elapsed, 'unreached', shutdown_fixture.unreached(mode, events), 'witness', shutdown_fixture.deferred_injection_unreached(events), 'ordering:', shutdown_fixture.controller_ordering(events))
print('  lifecycle: state', report['state'], 'child_status', report['child_status'], 'workload', workload['state'], 'stopped', workload['stopped'], 'retry', workload['retry'], 'outstanding_cleanup', bool(workload['outstanding_cleanup']),
      'runtime', [(r['observation']['runtime_id'], r['observation']['state'], r['token']['returned'], r['token']['revoked'], r['faults']) for r in rows],
      'final publication before request deadline: %.3f s margin' % (request['deadline'] - max(published)), 'progress deadline <= request:', report['shutdown_progress']['deadline'] <= request['deadline'], 'faults', report['faults'], report['shutdown_progress']['faults'])
for row in events:
    if row['event'] in ('outer_signal', 'termination_callback', 'deferred_signal_sent', 'deferred_signal_returned', 'probe_gate_released') or (row['event'] == 'trace' and row['function'] in ('defer', 'restore', '_supervise', 'supervise')) or (row['event'] == 'snapshot_replaced' and row['finished']):
        extra = {k: v for k, v in row.items() if k not in ('event', 'monotonic', 'pid', 'thread', 'callback')}
        print('  %7.3f pid=%d %s %s' % (row['monotonic'] - o, row['pid'], row['event'], json.dumps(extra, sort_keys=True)[:200]))
disk_roots.remove_owned_root(str(root.parent))
