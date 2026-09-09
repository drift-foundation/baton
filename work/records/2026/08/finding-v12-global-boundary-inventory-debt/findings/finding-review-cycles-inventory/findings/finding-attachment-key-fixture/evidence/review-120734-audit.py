import ast
import difflib
import hashlib
import io
import json
import pathlib
import time
import unittest



root = pathlib.Path.cwd()
evidence = pathlib.Path(__file__).resolve().parent
path = root / "v12/python/tests/manager/test_boundary_inventory.py"
base = (evidence / "base-120598.py").read_bytes()
candidate = path.read_bytes()
base_tree = ast.parse(base)
candidate_tree = ast.parse(candidate)
new_class = next(n for n in candidate_tree.body if isinstance(n, ast.ClassDef) and n.name == "TheAttachmentKeyProbeReachesAdoption")
candidate_tree.body.remove(new_class)
fixture_class = next(n for n in candidate_tree.body if isinstance(n, ast.ClassDef) and n.name == "EveryProbeProvesItArrived")
fixture = next(n for n in fixture_class.body if isinstance(n, ast.FunctionDef) and n.name == "spoiling_review_row")
run = fixture.body[0]
branch = next(n for n in run.body if isinstance(n, ast.If) and ast.unparse(n.test) == "(site, table, column) == ('_attachment_row', 'review_attachments', 'attachment_id')")
run.body.remove(branch)
assert ast.dump(candidate_tree) == ast.dump(base_tree)
baseline = json.loads((evidence / "baseline-120598.json").read_text())
for name, sha in baseline.items():
    if name != "v12/python/tests/manager/test_boundary_inventory.py":
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == sha

# Six initial passing methods remain exact; only the positive control changes.
initial = ast.parse((evidence / "initial-candidate-120598.py").read_bytes())
initial_class = next(n for n in initial.body if isinstance(n, ast.ClassDef) and n.name == new_class.name)
initial_methods = {n.name: n for n in initial_class.body if isinstance(n, ast.FunctionDef)}
current_methods = {n.name: n for n in new_class.body if isinstance(n, ast.FunctionDef)}
for name, old in initial_methods.items():
    if name == "test_valid_returned_key_passes_adoption_and_reaches_the_ended_review_guard":
        continue
    new_name = "test_existing_guard_rejects_the_valid_row_finalization_refusal" if name == "test_existing_guard_rejects_the_valid_row_ended_review_refusal" else name
    new = current_methods[new_name]
    old.name = new.name
    assert ast.dump(old) == ast.dump(new)


assert candidate == (evidence / "candidate-120598.py").read_bytes()
assert hashlib.sha256(base).hexdigest() == "bc1844e7840527818951b89d51762fedcaa0d1413bcd518dc742184ad3075509"
report = {"work": "W120587", "claim": 120734, "candidate_sha256": hashlib.sha256(candidate).hexdigest(), "mode": oct(path.stat().st_mode & 0o777), "scope": "Exact added branch and additive class only; all other baseline AST preserved", "runtime_hashes": "Match retained baseline", "retained_controls": "Six initial passes unchanged except one descriptive rename", "tests": "Reused retained seven controls and nine actual attachment-row closures; no rerun"}
with (evidence / "review-120734-audit.json").open("x") as output:
    json.dump(report, output, indent=2)
print(json.dumps(report, indent=2))
