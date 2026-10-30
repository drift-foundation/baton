"""Actual executor-boundary preflight, run AFTER bind and BEFORE the start.

Spawned as a child with the controller's exact working directory, PYTHONPATH
and BATON_V12_STAGE_EXECUTION_CONFIG, read from the GENERATED
packet/AUTHORING-COMMAND.json rather than retyped. The child calls the staged
controller's own bounded_engine, so the engine call is a grandchild of this
process -- the depth the real run uses.

It also runs main's first three pre-lock statements in order -- held_packet,
verify_imported_sources, verify_controller -- against the composed packet. That
is the window run348852 and run350529 both died in. It stops before the
authoring lock: no lock taken, no store opened, no image inspected, no Job, no
container, no provider call, no credential value read.

It does NOT establish that the controller starts, that the provider session is
valid, that a Job is admitted or that a turn completes.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path('/home/sl/baton-instances/durable-capture-w341357-352156')
CMD = json.loads((ROOT / 'packet/AUTHORING-COMMAND.json').read_text())
CWD = CMD['working_directory']
ENV = dict(os.environ)
ENV.update(CMD['environment'])
IMAGE = 'baton-v12-claude-worker:w239528-244216'

CHILD = r'''
import json, sys, time
report = {"probes": [], "startup": {}}
from tools import authoring_enforcement as controller
from tools import authoring_baseline as baseline
report["controller_file"] = controller.__file__
report["baseline_file"] = baseline.__file__
report["engine_entry"] = ("tools.authoring_enforcement.bounded_engine -> "
                          "single_worker._engine_run -> subprocess.run")
for name, argv in (("engine-version", ["docker", "version", "--format", "{{json .}}"]),
                   ("image-inspect", ["docker", "image", "inspect", "%s",
                                      "--format", "{{json .Id}}"])):
    started = time.time()
    try:
        done = controller.bounded_engine(argv, seconds=20)
        # _engine_run returns a MAPPING, not a CompletedProcess. Assuming the
        # latter fabricates a denial out of a probe that actually succeeded.
        def field(mapping, *names):
            for one in names:
                if one in mapping:
                    return mapping[one]
            return None
        raw_out = field(done, "stdout", "out") or ""
        raw_err = field(done, "stderr", "err") or ""
        entry = {"probe": name, "argv": argv,
                 "status": field(done, "status", "returncode", "code"),
                 "stdout": raw_out if isinstance(raw_out, str) else raw_out.decode(),
                 "stderr": raw_err if isinstance(raw_err, str) else raw_err.decode(),
                 "engine_run_return_keys": sorted(done)}
    except Exception as exc:
        entry = {"probe": name, "argv": argv, "error": repr(exc)}
    entry["seconds"] = round(time.time() - started, 3)
    report["probes"].append(entry)

# main's first three statements, in main's order, against the composed packet.
packet_path = "%s"
order = ["held_packet", "verify_imported_sources", "verify_controller"]
started = time.time()
packet = None
for step in order:
    try:
        if step == "held_packet":
            packet = baseline.held_packet(packet_path)
            report["startup"][step] = {"accepted": True, "refused": None,
                                       "not_reached": False}
        elif step == "verify_imported_sources":
            baseline.verify_imported_sources(packet)
            report["startup"][step] = {"accepted": True, "refused": None,
                                       "not_reached": False}
        else:
            controller.verify_controller(packet)
            report["startup"][step] = {"accepted": True, "refused": None,
                                       "not_reached": False}
    except BaseException as exc:
        report["startup"][step] = {"accepted": False, "refused": repr(exc),
                                   "not_reached": False}
        for rest in order[order.index(step) + 1:]:
            report["startup"][rest] = {"accepted": False, "refused": None,
                                       "not_reached": True}
        break
report["startup_seconds"] = round(time.time() - started, 6)
report["stopped_before"] = ("main's next statement, the authoring lock at "
                            "authoring_enforcement.py:566; no lock taken, no "
                            "store opened, no image verified by the controller")
report["resolved"] = {"baton_v12": [p for p in __import__("baton_v12").__path__],
                      "tools": [p for p in __import__("tools").__path__]}
print(json.dumps(report))
''' % (IMAGE, str(ROOT / 'packet/PACKET.json'))

started = time.time()
done = subprocess.run([sys.executable, '-B', '-c', CHILD], cwd=CWD, env=ENV,
                      capture_output=True, text=True, timeout=120)
seconds = round(time.time() - started, 3)

child = None
parse_error = None
try:
    child = json.loads(done.stdout)
except Exception as exc:
    parse_error = repr(exc)

denials = []
if done.returncode != 0:
    denials.append('boundary child exited %d' % done.returncode)
if child is None:
    denials.append('boundary child produced no parseable report: %s' % parse_error)
else:
    for entry in child['probes']:
        if entry.get('status') != 0:
            denials.append('%s failed at the boundary: %s'
                           % (entry['probe'], entry.get('stderr', entry.get('error'))))
    for step, verdict in child['startup'].items():
        if verdict['not_reached']:
            denials.append('%s NOT REACHED (an earlier statement refused)' % step)
        elif not verdict['accepted']:
            denials.append('%s REFUSED: %s' % (step, verdict['refused']))

report = {
    'schema': 'baton.w341357-executor-preflight/2',
    'claim': 352586,
    'when': 'AFTER bind and BEFORE the single selected start',
    'run': 'durable-capture-w341357-352156',
    'boundary': "a child process spawned with the controller's exact cwd, "
                'PYTHONPATH and BATON_V12_STAGE_EXECUTION_CONFIG read from the '
                'GENERATED packet/AUTHORING-COMMAND.json, calling the staged '
                "controller's own bounded_engine. The engine call is therefore "
                'a grandchild of this process, which is the depth the real run '
                'uses.',
    'working_directory': CWD,
    'environment': CMD['environment'],
    'child_status': done.returncode,
    'child_stderr': done.stderr,
    'child': child,
    'seconds': seconds,
    'denials': denials,
    'read_only': 'engine version and image inspect only, plus the three pre-lock '
                 'startup verifiers; no container created, no workload started, '
                 'no Job submitted, no store opened, no lock taken, no credential '
                 'value read, nothing written anywhere by this program',
    'what_this_does_not_establish':
        'that the controller starts, that the provider session is valid, that a '
        'Job is admitted or that a turn completes. Three selected invocations in '
        'a row failed at startup; this is the window the last two were in, and a '
        'closed window is not a prediction.',
    'regenerated': "the author's claim352156 copy of this check was under /tmp "
                   'and is absent after the announced wipe; this is a regenerated '
                   'check against the composed packet, not recovered historical '
                   'bytes',
}
report['verdict'] = 'available' if not denials else 'denied'
print(json.dumps(report, indent=1, sort_keys=True))
sys.exit(0 if not denials else 1)
