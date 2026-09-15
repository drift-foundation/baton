import ast
import hashlib
import json
import os
import pathlib
import re
import subprocess
import time

record = pathlib.Path(__file__).resolve().parent
root = pathlib.Path('/home/sl/src/baton')
packet = json.loads((record / 'provenance-160468.json').read_text())
prior = json.loads((record / 'review-160401.json').read_text())
author = json.loads((record / 'ledger-156316.json').read_text())
def digest(data):
    return hashlib.sha256(data).hexdigest()
def hashes():
    return {row['path']: {'sha256': digest((root / row['path']).read_bytes()), 'bytes': (root / row['path']).stat().st_size} for row in packet['paths']}
ledger = {'claim': 160499, 'work': 'W156162', 'prior_review_seconds': prior['review_spent_seconds'], 'author_spent_seconds': author['spent_seconds'], 'author_measured_runs': len(author['runs']), 'candidate_before': hashes(), 'runs': []}
start = time.monotonic()
def git(*args):
    return subprocess.run(['git', *args], cwd=root, capture_output=True, check=False)
audit = {'head': git('rev-parse', 'HEAD').stdout.decode().strip(), 'paths': len(packet['paths']), 'mismatches': [], 'numstat': [], 'default_context_hunks': {}, 'foreign_methods': {}}
for row in packet['paths']:
    name = row['path']
    base = git('show', audit['head'] + ':' + name)
    actual = ledger['candidate_before'][name]
    if actual != {'sha256': row['candidate_sha256'], 'bytes': row['candidate_bytes']}:
        audit['mismatches'].append({'candidate': name})
    if (digest(base.stdout) if base.returncode == 0 else None) != row['base_sha256'] or (len(base.stdout) if base.returncode == 0 else None) != row['base_bytes']:
        audit['mismatches'].append({'base': name})
    stat = git('diff', '--numstat', audit['head'], '--', name).stdout.decode().strip()
    hunks = git('diff', '-U0', audit['head'], '--', name).stdout.decode()
    if stat != row['numstat'] or sum(line.startswith('@@') for line in hunks.splitlines()) != row['hunk_count']:
        audit['mismatches'].append({'diff': name})
    audit['numstat'].append({'path': name, 'numstat': stat})
for name, method in [('v12/python/tools/stage_execution.py', 'observe_integration'), ('v12/python/tests/tools/test_stage_execution.py', 'test_readonly_reconciled_completion_without_runtime_reaches_outer_observer')]:
    data = (root / name).read_text()
    node = next(node for node in ast.walk(ast.parse(data)) if isinstance(node, ast.FunctionDef) and node.name == method)
    body = ''.join(data.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])
    previous = json.loads((record / 'audit-160401.json').read_text())['foreign_methods'][name]
    audit['foreign_methods'][name] = {'sha256': digest(body.encode()), 'matches_prior_audit': digest(body.encode()) == previous['sha256']}
    diff = git('diff', audit['head'], '--', name).stdout.decode()
    audit['default_context_hunks'][name] = sum(line.startswith('@@') for line in diff.splitlines())
    (record / ('review-160499-' + pathlib.Path(name).name + '.diff')).write_text(diff)
old_diff = (record / 'review-160401-stage_execution.py.diff').read_text()
source = root / 'v12/python/tools/stage_execution.py'
# Reconstruct the exact prior source in memory from the saved review diff.
base_lines = git('show', audit['head'] + ':v12/python/tools/stage_execution.py').stdout.decode().splitlines(keepends=True)
old_lines = []
cursor = 0
in_hunk = False
for line in old_diff.splitlines(keepends=True):
    if line.startswith('@@'):
        begin = int(re.match(r'@@ -(\d+)', line).group(1)) - 1
        old_lines.extend(base_lines[cursor:begin])
        cursor = begin
        in_hunk = True
    elif in_hunk and line.startswith(' '):
        assert base_lines[cursor] == line[1:]
        old_lines.append(line[1:])
        cursor += 1
    elif in_hunk and line.startswith('-'):
        assert base_lines[cursor] == line[1:]
        cursor += 1
    elif in_hunk and line.startswith('+'):
        old_lines.append(line[1:])
old_lines.extend(base_lines[cursor:])
old_source = ''.join(old_lines)
assert digest(old_source.encode()) == prior['candidate_after']['v12/python/tools/stage_execution.py']['sha256']
audit['prior_source_sha256'] = digest(old_source.encode())
def normalized(payload):
    tree = ast.parse(payload)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body = node.body[1:]
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'HOST_OBSERVATION_CONTRACT' for target in node.targets):
            node.value = ast.Constant(value='<explanatory constant>')
    return ast.dump(tree, include_attributes=False)
audit['source_ast_equal_except_docstrings_and_explanatory_constant'] = normalized(old_source) == normalized(source.read_text())
audit['raw_source_ast_unchanged'] = ast.dump(ast.parse(old_source), include_attributes=False) == ast.dump(ast.parse(source.read_text()), include_attributes=False)
audit['explanatory_constant_references'] = [str(file.relative_to(root)) for file in (root / 'v12/python').rglob('*.py') if 'HOST_OBSERVATION_CONTRACT' in file.read_text()]

audit['head_matches_packet'] = audit['head'] == packet['summary']['head_revision']
audit['head_after'] = git('rev-parse', 'HEAD').stdout.decode().strip()
(record / 'audit-160499.json').write_text(json.dumps(audit, indent=2) + '\n')
ledger['runs'].append({'activity': 'read-only 29-path provenance audit', 'elapsed_seconds': time.monotonic() - start, 'log': 'audit-160499.json'})
ledger['review_spent_seconds'] = ledger['prior_review_seconds'] + sum(run['elapsed_seconds'] for run in ledger['runs'])
ledger['candidate_after'] = hashes()
ledger['candidate_unchanged'] = ledger['candidate_before'] == ledger['candidate_after']
(record / 'review-160499.json').write_text(json.dumps(ledger, indent=2) + '\n')
print(json.dumps({key: ledger[key] for key in ('runs', 'review_spent_seconds', 'author_spent_seconds', 'author_measured_runs', 'candidate_unchanged')}, indent=2))
print(json.dumps({key: audit[key] for key in ('head', 'mismatches', 'foreign_methods', 'default_context_hunks')}, indent=2))
