import ast
import difflib
import hashlib
import io
import json
import pathlib
import time
import unittest

from tests.manager import test_boundary_inventory as inventory

root = pathlib.Path.cwd().parents[1]
evidence = pathlib.Path(__file__).resolve().parent
path = pathlib.Path(inventory.__file__)
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

start = time.monotonic()
out = io.StringIO()
suite = unittest.defaultTestLoader.loadTestsFromName("tests.manager.test_boundary_inventory.TheAttachmentKeyProbeReachesAdoption.test_valid_returned_key_passes_adoption_and_reaches_the_recorded_fence_guard")
result = unittest.TextTestRunner(stream=out, verbosity=2).run(suite)
focused_elapsed = time.monotonic() - start
assert result.wasSuccessful(), out.getvalue()

# Collect once, then execute unchanged attachment-row stimuli on private roots.
start = time.monotonic()
case = inventory.EveryProbeProvesItArrived()
case.setUp()
pairs = []
drivers = []
try:
    probes = case.review_cycle_probes()
    for (entry, label), (full, drive) in probes.items():
        if entry[1] == "review_cycles.py:_attachment_row":
            assert entry[0] == "adopted"
            column = entry[2].split(".", 1)[1] if "." in entry[2] else "reviewer_participant"
            pairs.append((entry, label, full, column))
            drivers.append((full, drive))
finally:
    case.doCleanups()
assert len(pairs) > 1
for full, drive in drivers:
    case.setUp()
    try:
        case.refusing(full, drive)
    finally:
        case.doCleanups()
sweep_elapsed = time.monotonic() - start
report = dict(base_sha256=hashlib.sha256(base).hexdigest(), candidate_sha256=hashlib.sha256(candidate).hexdigest(), scope_audit="only exact fixture branch and new control class; all other AST unchanged", runtime_hashes=baseline, retained_initial_passes=6, corrected_control=out.getvalue(), corrected_elapsed_seconds=focused_elapsed, attachment_pairs=pairs, attachment_count=len(pairs), sweep_elapsed_seconds=sweep_elapsed)
(evidence / "candidate-120598.py").write_bytes(candidate)
(evidence / "candidate-120598.patch").write_text("".join(difflib.unified_diff(base.decode().splitlines(True), candidate.decode().splitlines(True), fromfile="a/v12/python/tests/manager/test_boundary_inventory.py", tofile="b/v12/python/tests/manager/test_boundary_inventory.py")))
with (evidence / "verification-120598.json").open("x") as output:
    json.dump(report, output, indent=2)
print(json.dumps(report, indent=2))
