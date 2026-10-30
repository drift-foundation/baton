"""Launch the ONE selected invocation using ONLY the generated enforced command."""
import json, os, subprocess, sys, time, datetime
from pathlib import Path

ROOT = Path('/home/sl/baton-instances/durable-capture-w341357-352156')
E = Path('/home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-'
         'diagnostics/findings/finding-durable-failure-capture/evidence/run-352156')
cmd = json.loads((ROOT / 'packet/AUTHORING-COMMAND.json').read_text())
env = dict(os.environ)
env.update(cmd['environment'])
launched = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
out = open(E / 'controller-stdout.log', 'wb')
err = open(E / 'controller-stderr.log', 'wb')
started = time.time()
child = subprocess.Popen(cmd['start'], cwd=cmd['working_directory'], env=env,
                         stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                         start_new_session=True)
(E / 'LAUNCH.json').write_text(json.dumps({
    'schema': 'baton.w341357-launch/1', 'claim': 352586,
    'run': 'durable-capture-w341357-352156',
    'selection': 'owner reroute352577, exactly one invocation, no retry',
    'launched_at': launched, 'pid': child.pid,
    'argv': cmd['start'], 'cwd': cmd['working_directory'],
    'environment': cmd['environment'],
    'source': 'packet/AUTHORING-COMMAND.json, the generated enforced command; '
              "packet/commands.json's start was NOT used",
    'monotonic_start': started,
}, indent=1, sort_keys=True) + '\n')
print(json.dumps({'pid': child.pid, 'launched_at': launched}))
