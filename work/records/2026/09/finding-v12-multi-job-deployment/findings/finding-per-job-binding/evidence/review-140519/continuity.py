"""Reconcile current bytes and retained admission assertions; execute no tests."""
import ast
import hashlib
import json
from pathlib import Path
import stat
import time

started = time.monotonic()
root = Path.cwd()
out = Path(__file__).resolve().parent
record = out.parents[1]
accepted = json.loads((record / 'findings/finding-per-job-readonly-observation/evidence/review-140487/result.json').read_bytes())
errors, actual = [], {}
for name, wanted in accepted['accepted_union'].items():
    path = root / name
    if wanted.get('state') == 'absent':
        got = {'state': 'absent' if not path.exists() and not path.is_symlink() else 'present'}
    else:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            errors.append(name + ': not regular')
        data = path.read_bytes()
        got = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'mode': oct(stat.S_IMODE(info.st_mode))}
    actual[name] = got
    if got != wanted:
        errors.append(name + ': drift')
def methods(path):
    tree = ast.parse(path.read_bytes())
    return {node.name: {m.name: ast.dump(m, include_attributes=False) for m in node.body if isinstance(m, ast.FunctionDef)} for node in tree.body if isinstance(node, ast.ClassDef)}
old_path = record / 'findings/finding-all-role-job-admission/evidence/review-131028/candidate/tests/tools/test_stage_execution.py'
old = methods(old_path)
current = methods(root / 'v12/python/tests/tools/test_stage_execution.py')
comparison = {}
for name in ('EachJobBindsItsOwnDeploymentAndLine', 'EveryJobRoleIsValidatedBeforeAllocation'):
    comparison[name] = {method: 'identical' if body == current.get(name, {}).get(method) else 'changed_or_removed' for method, body in old[name].items()}
elapsed = time.monotonic() - started
result = {'work': 'W119405', 'claim': 140519, 'accepted_candidate': 140229,
          'accepted_union': actual, 'errors': errors, 'admission_method_comparison': comparison,
          'elapsed_seconds': elapsed, 'outer_reserve_seconds': 0.05,
          'review_charge_seconds': elapsed + 0.05,
          'review_cumulative_seconds': 4.623840369998892 + elapsed + 0.05,
          'review_cap_seconds': 5, 'runtime_tests': 0, 'database_opens': 0,
          'joined_allocation_spent_seconds': 0,
          'limitations': 'Static continuity only. Retained execution evidence remains attributed to original claims. All historical costs and uncertainty remain; no transfer.'}
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'accepted_union'}, indent=2))
assert not errors, errors
assert result['review_cumulative_seconds'] < 5
