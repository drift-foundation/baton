"""No test imports, collection or execution; validate research coverage and drift."""
import ast
import hashlib
import json
from pathlib import Path
import runpy
import time

started = time.monotonic()
record = Path(__file__).resolve().parent
repo = next(parent for parent in record.parents if (parent / 'v12/python/tools/parallel_test.py').is_file())
baseline = json.loads((record / 'inventory-168782.json').read_text())
runner_path = repo / 'v12/python/tools/parallel_test.py'
runner_hash = hashlib.sha256(runner_path.read_bytes()).hexdigest()
assert runner_hash == baseline['runner_sha256'], 'runner changed; revalidate research'
runner = runpy.run_path(str(runner_path), run_name='registry_research_only')
suite = runner['Suite'](repo / 'v12/python', runner['PARALLEL_MODULES'], runner['SERIAL_MODULES'])
found = set(suite.discovered())
missing = found - set(suite.parallel) - set(suite.serial)
assert missing == set(baseline['missing'])
try:
    suite.check_registry()
except runner['RunnerRefusal'] as error:
    refusal = str(error)
else:
    raise AssertionError('original missing registry must still refuse')
gate = 'tests.manager.test_runtime_deadline_engine'
rows = []
changed = []
for row in baseline['modules']:
    path = repo / row['path']
    current = hashlib.sha256(path.read_bytes()).hexdigest()
    if current != row['sha256']:
        changed.append({'path': row['path'], 'baseline_sha256': row['sha256'], 'current_sha256': current})
    category = 'supervised' if row['module'] == gate else 'parallel'
    tree = ast.parse(path.read_text())
    hooks = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ('setUpClass', 'tearDownClass', 'setUpModule', 'tearDownModule')]
    if category == 'parallel':
        assert not hooks, (row['module'], hooks)
    rows.append({'module': row['module'], 'category': category, 'path': row['path'], 'sha256': current, 'hooks': hooks})
proposed_parallel = list(suite.parallel) + [r['module'] for r in rows if r['category'] == 'parallel']
proposed_serial = list(suite.serial)
proposed_supervised = [gate]
all_names = proposed_parallel + proposed_serial + proposed_supervised
assert len(all_names) == len(set(all_names)) == len(found) == 117
assert set(all_names) == found
assert gate not in proposed_parallel + proposed_serial
fixture_paths = ['tests/integration/fixtures.py', 'tests/job_manager/fixtures.py', 'tests/manager/test_attempts.py', 'tests/manager/disk_roots.py', 'tests/tools/test_single_worker.py', 'tests/tools/test_stage_execution.py', 'tests/tools/test_parallel_runner.py']
fixtures = {name: hashlib.sha256((repo / 'v12/python' / name).read_bytes()).hexdigest() for name in fixture_paths}
print(json.dumps({'work': 'W168703', 'claim': 168782, 'kind': 'source-only research audit; not implemented registry or runtime acceptance', 'runner_sha256': runner_hash, 'actual_registry_refusal': refusal, 'all_20_source_hashes_unchanged': not changed, 'changed_sources_require_revalidation': changed, 'proposed_coverage_valid': True, 'proposed_counts': {'parallel': len(proposed_parallel), 'serial': len(proposed_serial), 'supervised': len(proposed_supervised)}, 'rows': rows, 'fixture_hashes_at_final_audit': fixtures, 'elapsed_seconds': time.monotonic() - started}, indent=2))
raise SystemExit(2 if changed else 0)
