"""K review runner: `unittest -v` on the prepared interpreter in one tree,
explicit id accounting, roots outside every checkout. No engine or provider."""
import json, os, re, subprocess, sys, time, hashlib
from pathlib import Path
tree, name, selection, bound = Path(sys.argv[1]), sys.argv[2], json.loads(Path(sys.argv[3]).read_text()), int(sys.argv[4])
out = Path('/var/tmp/baton-k-review-386054/logs'); out.mkdir(exist_ok=True)
py = '/home/sl/.local/state/baton-v12-venv/bin/python'
roots = '/var/tmp/baton-k-review-386054/roots'
env = dict(os.environ, PYTHONPATH='src', TMPDIR=roots, BATON_V12_DISK_ROOT=roots, GIT_CEILING_DIRECTORIES='/var/tmp')
def identity():
    h = hashlib.sha256()
    for p in sorted((tree/'v12').rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and 'node_modules' not in p.parts:
            h.update(str(p.relative_to(tree)).encode()); h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()
before = identity()
collector = 'import unittest,json,sys; f=lambda s: [s.id()] if isinstance(s,unittest.TestCase) else [i for x in s for i in f(x)]; print(json.dumps(f(unittest.TestLoader().loadTestsFromNames(sys.argv[1:]))))'
c = subprocess.run([py, '-c', collector, *selection], cwd=tree/'v12/python', env=dict(env, PYTHONPATH='src:.'), capture_output=True, text=True)
expected = json.loads(c.stdout) if c.returncode == 0 else []
start = time.monotonic()
with open(out/f'{name}.stderr.log', 'wb') as err:
    p = subprocess.Popen([py, '-m', 'unittest', '-v', *selection], cwd=tree/'v12/python', env=env, stdout=subprocess.DEVNULL, stderr=err, start_new_session=True)
    try: p.wait(timeout=bound); timed = False
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, 9); p.wait(); timed = True
results = {}; current = None
for line in (out/f'{name}.stderr.log').read_text(errors='replace').splitlines():
    m = re.match(r'^(test_\S+) \(([^)]+)\)', line)
    if m:
        current = m.group(2) if m.group(2).endswith('.'+m.group(1)) else m.group(2)+'.'+m.group(1); results[current] = 'started'
    if current and (line in ('ok', 'FAIL', 'ERROR') or re.search(r'\.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$', line)):
        results[current] = line.rsplit('... ', 1)[-1]; current = None
summary = {'tree': str(tree), 'collected': len(expected), 'collection_exit': c.returncode, 'executed': len(results), 'passed': sum(v == 'ok' for v in results.values()),
           'exit_status': p.returncode, 'timed_out': timed, 'seconds': time.monotonic()-start, 'unaccounted': sorted(set(expected)-set(results)),
           'nonpassing': {k: v for k, v in results.items() if v != 'ok'}, 'source_stable': before == identity(), 'tree_identity': before, 'outcomes': results}
(out/f'{name}.summary.json').write_text(json.dumps(summary, indent=1, sort_keys=True)+'\n')
print(json.dumps({k: v for k, v in summary.items() if k not in ('outcomes', 'nonpassing')}), len(summary['nonpassing']))
