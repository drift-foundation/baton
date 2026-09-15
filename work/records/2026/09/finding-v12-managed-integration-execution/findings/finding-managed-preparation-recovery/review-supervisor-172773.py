"""Focused independent review: 180s run, TERM5/KILL5, own process group."""
import json, os, signal, subprocess, sys, time
from pathlib import Path

home = Path(__file__).resolve().parent
label, command = sys.argv[1], sys.argv[2:]
started = time.monotonic()
sent = []
timed_out = False
with (home / (label + '.log')).open('x') as log:
    child = subprocess.Popen(command, cwd='/home/sl/src/baton/v12/python',
                             env=dict(os.environ, PYTHONPATH='src:tools:.'),
                             stdout=log, stderr=subprocess.STDOUT,
                             start_new_session=True)
    try:
        child.wait(timeout=180)
    except subprocess.TimeoutExpired:
        timed_out = True
        for sig, grace in ((signal.SIGTERM, 5), (signal.SIGKILL, 5)):
            try:
                os.killpg(child.pid, sig)
                sent.append(sig.name)
            except ProcessLookupError:
                break
            try:
                child.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                continue
            try:
                os.killpg(child.pid, 0)
            except ProcessLookupError:
                break
try:
    os.killpg(child.pid, 0)
    group_gone = False
except ProcessLookupError:
    group_gone = True
record = dict(command=command, cwd='/home/sl/src/baton/v12/python',
              PYTHONPATH='src:tools:.', seconds=time.monotonic()-started,
              exit=child.poll(), timed_out=timed_out, signals=sent,
              limits_seconds=[180, 5, 5], process_group_gone=group_gone)
(home / (label + '.json')).write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record))
print((home / (label + '.log')).read_text()[-3000:])
raise SystemExit(not (record['exit'] == 0 and not timed_out and group_gone))
