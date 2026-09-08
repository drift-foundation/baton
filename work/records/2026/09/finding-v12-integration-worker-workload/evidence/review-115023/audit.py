"""Verify final documentation-only completion against accepted joined bytes."""
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
RECORD = HERE.parents[1]
prior = RECORD / 'evidence/review-114978'
expected = json.loads((prior / 'joined.json').read_text())['paths']
result = {'claim': 115023, 'at': datetime.now(timezone.utc).isoformat(), 'paths': {}}
for name, row in expected.items():
    data = (REPO / name).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    dest = HERE / 'candidate' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    result['paths'][name] = {'sha256': sha, 'unchanged_since_join': sha == row['sha256']}

name = 'v12/python/tests/manager/test_integration_worker.py'
before = (prior / 'candidate' / name).read_text()
after = (REPO / name).read_text()
(HERE / 'test-documentation.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='joined/' + name, tofile='final/' + name)))

class WithoutDocstrings(ast.NodeTransformer):
    def generic_visit(self, node):
        node = super().generic_visit(node)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body = node.body[1:]
        return node

def methods(source):
    return {c.name + '.' + m.name: ast.dump(m, include_attributes=False)
            for c in ast.parse(source).body if isinstance(c, ast.ClassDef)
            for m in c.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')}

old, new = methods(before), methods(after)
result['tests'] = {'before': len(old), 'after': len(new), 'changed_methods_including_docstrings': sorted(k for k in old.keys() & new.keys() if old[k] != new[k]), 'added': sorted(new.keys() - old.keys()), 'removed': sorted(old.keys() - new.keys()), 'whole_file_executable_AST_identical': ast.dump(WithoutDocstrings().visit(ast.parse(before)), include_attributes=False) == ast.dump(WithoutDocstrings().visit(ast.parse(after)), include_attributes=False)}
result['matches_author_test_hash'] = result['paths'][name]['sha256'] == 'a35013a2ad37f9079c8c653776bf1c7d76bdb7628a673268c3f0d5b3318b4f15'
progress = (RECORD / 'PROGRESS.md').read_bytes()
(HERE / 'progress-at-review.md').write_bytes(progress)
result['progress_sha256'] = hashlib.sha256(progress).hexdigest()
assert result['tests']['whole_file_executable_AST_identical']
assert result['matches_author_test_hash']
assert all(row['unchanged_since_join'] for path, row in result['paths'].items() if path != name)
(HERE / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
