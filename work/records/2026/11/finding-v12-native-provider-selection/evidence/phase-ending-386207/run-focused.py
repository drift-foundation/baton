"""Focused, unaccounted-by-registry run with explicit id accounting.

Usage: run-focused.py NAME SELECTION.json BOUND_SECONDS
Runs `just test-one` (prepared interpreter) from the disposable candidate
repository, retains collection, header, raw logs, source identity before and
after, and a summary of every collected id by outcome. No engine or provider.
"""
import os, json, re, subprocess, time, sys, signal
from pathlib import Path
repo = Path('/var/tmp/baton-phase-386207-source')
evidence = Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/phase-ending-386207')
python = '/home/sl/.local/state/baton-v12-venv/bin/python'
roots = '/var/tmp/baton-phase-386207-tests'
Path(roots).mkdir(exist_ok=True)
env = dict({k:v for k,v in os.environ.items() if not k.startswith('GIT_')}, PYTHONPATH='src', PYTHONDONTWRITEBYTECODE='1', BATON_V12_DISK_ROOT=roots, TMPDIR=roots)
identity = [python, '-m', 'tools.source_identity', '--declared', 'v12']
name = sys.argv[1]; names = json.loads(Path(sys.argv[2]).read_text()); bound = int(sys.argv[3])
r = subprocess.run(identity, cwd=repo/'v12/python', env=env, capture_output=True)
(evidence/f'{name}.source-before.json').write_bytes(r.stdout)
if r.returncode: sys.exit(r.returncode)
collector = 'import unittest,json,sys; flatten=lambda s: [s.id()] if isinstance(s,unittest.TestCase) else [i for x in s for i in flatten(x)]; print(json.dumps(flatten(unittest.TestLoader().loadTestsFromNames(sys.argv[1:]))))'
r = subprocess.run([python, '-c', collector, *names], cwd=repo/'v12/python', env=env, capture_output=True)
(evidence/f'{name}.collection.json').write_bytes(r.stdout)
if r.returncode: sys.stderr.write(r.stderr.decode()); sys.exit(r.returncode)
expected = json.loads(r.stdout); command = ['just', '--justfile', 'v12/justfile', 'test-one', *names]
header = {'command': command, 'interpreter': python, 'base': '42da148f1b845474e5fa6db870132fcf214073f6',
          'candidate_repository_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
          'groups': ['manager-pure', 'tools-pure', 'job_manager'], 'collected': len(expected), 'bound_seconds': bound,
          'disk_root': roots, 'TMPDIR': roots, 'accounting': 'explicit ids from unittest -v; test-one has no registry accounting'}
start = time.monotonic(); timed = False
with (evidence/f'{name}.stdout.log').open('wb') as out, (evidence/f'{name}.stderr.log').open('wb') as err:
    p = subprocess.Popen(command, cwd=repo, stdout=out, stderr=err, start_new_session=True, env=dict(env, PYTHONPATH=''))
    header.update(pid=p.pid, pgid=p.pid); (evidence/f'{name}.header.json').write_text(json.dumps(header, indent=2)+'\n')
    try: p.wait(timeout=bound)
    except subprocess.TimeoutExpired: timed = True; os.killpg(p.pid, signal.SIGKILL); p.wait()
elapsed = time.monotonic()-start
r = subprocess.run(identity, cwd=repo/'v12/python', env=env, capture_output=True); (evidence/f'{name}.source-after.json').write_bytes(r.stdout)
results = {}; duplicates = []; current = None
for line in (evidence/f'{name}.stderr.log').read_text(errors='replace').splitlines():
    m = re.match(r'^(test_\S+) \(([^)]+)\)', line)
    if m:
        current = m.group(2) if m.group(2).endswith('.'+m.group(1)) else m.group(2)+'.'+m.group(1)
        if current in results: duplicates.append(current)
        results[current] = 'started'
    if current and (line in ('ok', 'FAIL', 'ERROR') or re.search(r'\.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$', line)):
        results[current] = line.rsplit('... ', 1)[-1]; current = None
summary = {'collected': len(expected), 'executed': len(results), 'passed': sum(v == 'ok' for v in results.values()),
           'exit_status': p.returncode, 'timed_out': timed, 'duration_seconds': elapsed, 'duplicates': duplicates,
           'unaccounted': sorted(set(expected)-set(results)), 'uncollected': sorted(set(results)-set(expected)),
           'nonpassing': {k: v for k, v in results.items() if v != 'ok'},
           'source_drift': (evidence/f'{name}.source-before.json').read_bytes() != r.stdout,
           'source_after_exit_status': r.returncode, 'outcomes': results}
(evidence/f'{name}.summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
print(json.dumps({k: v for k, v in summary.items() if k not in ('outcomes',)}), flush=True)
sys.exit(124 if timed else p.returncode if p.returncode else 1 if summary['unaccounted'] or summary['nonpassing'] or summary['source_drift'] or summary['duplicates'] else 0)
