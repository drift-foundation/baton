"""Independent run10 preparation checks; never run host preparation or models."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PROOF = HERE.parent.parent
REPO = Path('/home/sl/src/baton')
sys.path.insert(0, str(REPO / 'v12/python/src'))
spec = importlib.util.spec_from_file_location('custody_reader', PROOF / 'evidence/run9-budget-150384/reconcile.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
read = lambda path: reader.read(path, 16 * 1024 * 1024)
sha = lambda raw: 'sha256:' + hashlib.sha256(raw).hexdigest()
start = time.monotonic()
manifest = PROOF / 'evidence/run10-preparation-152826/candidate-manifest.json'
assert sha(read(manifest)) == 'sha256:63b84c6e3749787746894938117d44dcac326cf8291994195133479b9bec2c87'
journals = {str(PROOF.relative_to(REPO) / n) for n in ('FINDING.md', 'PLAN.md', 'PROGRESS.md')}
counts = {}
for name, count in [('run10-preparation-152826', 72), ('accounting-152750', 86), ('accounting-152563', 92), ('accounting-150501', 75), ('run9-freeze-150125', 198), ('run9-budget-150384', 19)]:
    actual = 0
    files = json.loads(read(PROOF / 'evidence' / name / 'candidate-manifest.json'))['files']
    for locator, binding in files.items():
        if name != 'run10-preparation-152826' and locator in journals:
            continue
        rel = Path(locator)
        assert not rel.is_absolute() and '..' not in rel.parts
        raw = read(REPO / rel)
        assert sha(raw) == binding['sha256'] and len(raw) == binding['bytes'], locator
        if 'mode' in binding:
            assert oct((REPO / rel).stat().st_mode & 0o7777) == binding['mode'], locator
        if name == 'run10-preparation-152826' and locator in journals:
            (HERE / ('candidate-' + rel.name)).write_bytes(raw)
        actual += 1
    assert actual == count, (name, actual)
    counts[name] = actual
package = PROOF / 'prepared-152826'
helpers = json.loads(read(package / 'runner-helpers.json'))
assert set(helpers) == {'run.py', 'deployment.py', 'accounting.py', 'target_posture.py', 'failure_observation.py'}
for name, expected in helpers.items():
    assert sha(read(package / name)) == expected
for name in ('accounting.py', 'target_posture.py', 'failure_observation.py', 'test_accounting.py', 'test_joined_judges.py', 'test_stats_observation.py'):
    assert read(package / name) == read(PROOF / 'prepared-152750' / name), name
assert not os.path.lexists('/home/sl/.local/state/baton/v12/w71879-run10')
for name in ('frozen-config', 'validation.json', 'selected-images.json', 'execution-review.json'):
    assert not os.path.lexists(package / name), name
commands = json.loads(read(PROOF / 'evidence/run10-preparation-152826/operator-commands.json'))
assert commands['owner_event'] == 152823 and commands['operator_attempts_authorized'] == 1
assert len(commands['commands']) == 5
readme = read(package / 'README.md').decode()
for command in commands['commands']:
    assert command['command'] in readme and command['cwd'] in readme
report = {'claim': 152872, 'files': counts, 'helpers': helpers, 'run10_absent': True, 'actual_inputs_and_markers_absent': True,
          'operator_recipe_commands': 5, 'continuing_journals_captured_before_review_append': True,
          'seconds': time.monotonic() - start}
(HERE / 'custody.json').write_text(json.dumps(report, indent=2) + '\n')
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(REPO / 'v12/python/src') + ':' + str(REPO / 'v12/python') + ':' + str(REPO / 'v12/worker'))
checks = {}
for name, argv in [('fresh-preparation', [sys.executable, '-B', '-m', 'unittest', 'test_run10_preparation', '-v']), ('shell-syntax', ['/bin/bash', '-n', str(package / 'operator-prepare.sh')])]:
    start = time.monotonic()
    done = subprocess.run(argv, cwd=package, env=env, capture_output=True, text=True, timeout=30)
    checks[name] = {'exit': done.returncode, 'seconds': time.monotonic() - start}
    (HERE / (name + '.txt')).write_text(done.stdout + done.stderr)
(HERE / 'checks.json').write_text(json.dumps(checks, indent=2) + '\n')
seconds = report['seconds'] + sum(item['seconds'] for item in checks.values())
cost = {'current_listed_seconds': seconds, 'cumulative_listed_preparation_seconds': 111.197589272952 + seconds,
        'nine_failed_runtime_walls_seconds': 2002.0388815780316, 'uncertainty': 'Prior untimed/CLI/static/host/operator/billing/rounding uncertainty retained. Prior product166 and proof95 results reused on accepted behavior; no host preparation, image build, credential probe or model run.'}
(HERE / 'spending.json').write_text(json.dumps(cost, indent=2) + '\n')
print(json.dumps({'custody': report, 'checks': checks, 'spending': cost}, indent=2))
sys.exit(any(item['exit'] for item in checks.values()))
