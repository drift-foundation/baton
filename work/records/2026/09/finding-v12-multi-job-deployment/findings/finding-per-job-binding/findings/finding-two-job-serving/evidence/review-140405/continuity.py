import ast
import hashlib
import json
from pathlib import Path
import shutil
import stat
import time

start = time.monotonic()
root = Path('/home/sl/src/baton')
out = Path(__file__).resolve().parent
record = out.parent.parent
r = root / 'work/records/2026/09/finding-v12-line-rebase-after-target-advance/findings/finding-integration-result-composition'
accepted = json.loads((r / 'evidence/review-140320/result.json').read_text())
actual, errors = {}, []
for name, wanted in accepted['accepted_union'].items():
    p = root / name
    if wanted.get('state') == 'absent':
        value = {'state': 'absent'} if not p.exists() and not p.is_symlink() else {'state': 'present'}
    else:
        data = p.read_bytes()
        value = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'mode': oct(stat.S_IMODE(p.stat().st_mode))}
        if p.is_symlink() or not p.is_file():
            errors.append(name + ': not a regular non-symlink')
    actual[name] = value
    if value != wanted:
        errors.append(name + ': differs from accepted R')
for name in ('tools/stage_execution.py', 'tests/tools/test_stage_execution.py'):
    dest = out / 'candidate' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / 'v12/python' / name, dest)

def methods(path, klass):
    tree = ast.parse(path.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == klass)
    return {n.name: ast.dump(n, include_attributes=False) for n in cls.body if isinstance(n, ast.FunctionDef)}

name = 'tests/tools/test_stage_execution.py'
klass = 'TwoBoundJobsTraverseServingAndCorrection'
before = methods(record / 'evidence/review-131441/candidate' / name, klass)
after = methods(root / 'v12/python' / name, klass)
comparison = {n: ('unchanged' if before[n] == after.get(n) else 'changed' if n in after else 'removed') for n in before if n.startswith('test_')}
preflight_class = 'NothingIsOpenedBeforeTheConfigurationIsProved'
old_preflight = methods(record / 'evidence/review-131441/candidate' / name, preflight_class)
new_preflight = methods(root / 'v12/python' / name, preflight_class)
preflight_comparison = {n: ('unchanged' if old_preflight[n] == new_preflight.get(n) else 'changed' if n in new_preflight else 'removed') for n in old_preflight if n.startswith('test_')}
elapsed = time.monotonic() - start
result = {'work': 'W130224', 'claim': 140405, 'accepted_R_candidate': 140229, 'accepted_union': actual, 'errors': errors, 'serving_test_ast_continuity': comparison, 'preflight_test_ast_continuity': preflight_comparison, 'new_serving_tests': sorted(set(after) - set(before)), 'continuity_elapsed_seconds': elapsed, 'continuity_charge_seconds': elapsed + 0.05, 'reviewer_prior_charge_seconds': 4.391688829, 'reviewer_cumulative_charge_seconds': 4.391688829 + elapsed + 0.05, 'reviewer_ceiling_seconds': 5, 'runtime_tests_run': 0, 'campaign_author_carry_seconds': 383.25, 'note': 'Current43 entries match accepted R; full test evidence reused, no source/test edit or runtime rerun. All prior uncertainty and unmeasured reads/dossier work retained. No budget transfer.'}
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'accepted_union'}, indent=2))
assert not errors, errors
assert result['reviewer_cumulative_charge_seconds'] < 5
