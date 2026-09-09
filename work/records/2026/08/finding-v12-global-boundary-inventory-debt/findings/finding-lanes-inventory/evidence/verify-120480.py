"""Lane-only joined proof and complete residual capture, no aggregate test."""
import ast
import difflib
import hashlib
import io
import json
from pathlib import Path
import time
import unittest
from tests.manager import test_boundary_inventory as b

root = Path.cwd()
here = Path(__file__).resolve().parent
started = time.monotonic()
output = io.StringIO()
result = unittest.TextTestRunner(stream=output).run(unittest.defaultTestLoader.loadTestsFromTestCase(b.LanesHaveCompleteReceivingCoverage))
report = {"work": "W116972", "claim": 120480, "tests": result.testsRun, "successful": result.wasSuccessful(),
          "test_result": output.getvalue(), "test_seconds": time.monotonic() - started}
entries = b.receiving_entries()
owner = b.EveryReceivingEntryHasOneOwner()
records = b.boundary_occurrences()
claims = b._boundary_claims(records, entries, b.DELEGATED)
_, residual = b._account_boundary_calls(records, claims, b.NOT_AN_ENTRY)
case = b.EveryProbeProvesItArrived()
try:
    case.setUp()
    declared = {pair for pair in case.all_probes() if pair[0][1].startswith("lanes.py:")}
    expected = {pair for pair in case.expected() if pair[0][1].startswith("lanes.py:")}
finally:
    case.doCleanups()
report["lanes"] = {
    "entries": sorted(e for e in entries if e[1].startswith("lanes.py:")),
    "unowned": sorted(e for e in entries if e[1].startswith("lanes.py:") and owner.owner_of(e)[0] is None),
    "orphan_calls": sorted({(r.site, r.kind, r.label) for r in residual if r.site.startswith("lanes.py:")}),
    "expected": sorted(expected), "declared": sorted(declared),
    "missing": sorted(expected - declared), "orphan_probes": sorted(declared - expected),
}
report["global_residuals"] = {
    "unowned": sorted(e for e in entries if owner.owner_of(e)[0] is None),
    "orphan_calls": sorted({(r.site, r.kind, r.label) for r in residual}),
}
path = root / "v12/python/tests/manager/test_boundary_inventory.py"
base = (here / "base-120480.py").read_text()
current = path.read_text()
original = ast.parse(base)
candidate = ast.parse(current)
fp = lambda n: ast.dump(n, include_attributes=False)
old_nodes = {n.name: n for n in original.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
new_nodes = {n.name: n for n in candidate.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
changed = {name for name in old_nodes if fp(old_nodes[name]) != fp(new_nodes[name])}
assert changed == {"EveryProbeProvesItArrived"}, changed
old_methods = {n.name:fp(n) for n in old_nodes["EveryProbeProvesItArrived"].body if isinstance(n, ast.FunctionDef)}
new_methods = {n.name:fp(n) for n in new_nodes["EveryProbeProvesItArrived"].body if isinstance(n, ast.FunctionDef)}
assert {name for name in old_methods if old_methods[name] != new_methods[name]} == {"lane_probes"}
def assignments(tree):
    return {ast.unparse(n.targets[0]):fp(n) for n in tree.body if isinstance(n, ast.Assign)}
a,z = assignments(original), assignments(candidate)
assert {name for name in a if a[name]!=z[name]} == {"NOT_AN_ENTRY", "DELEGATED"}
assert new_nodes.keys()-old_nodes.keys() == {"LanesHaveCompleteReceivingCoverage"}
# Preserve each original catalog item as exact AST, including dictionaries expanded by comprehension.
def values(tree, name):
    return next(n.value for n in tree.body if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])==name)
for name in ("NOT_AN_ENTRY","DELEGATED"):
    before,after=values(original,name),values(candidate,name)
    old_items=[(fp(k) if k else None,fp(v)) for k,v in zip(before.keys,before.values)]
    new_items=[(fp(k) if k else None,fp(v)) for k,v in zip(after.keys,after.values)]
    assert all(item in new_items for item in old_items)
report["scope_audit"] = {
    "changed_existing_class_method":"EveryProbeProvesItArrived.lane_probes (additive pairs only)",
    "new_class":"LanesHaveCompleteReceivingCoverage",
    "changed_catalogs":["NOT_AN_ENTRY (four additions)","DELEGATED (one addition)"],
    "all_other_existing_classes_functions_assertions_and_catalog_items_unchanged":True,
}
paths = [path] + [root / "v12/python/src/baton_v12/worker_manager" / name for name in ("lanes.py","schema.py","attempts.py","intake.py")]
report["source_hashes"] = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
report["seconds"] = time.monotonic()-started
with (here / "verification-120480.json").open("x") as f:f.write(json.dumps(report,indent=2)+"\n")
with (here / "candidate-120480.py").open("x") as f:f.write(current)
with (here / "candidate-120480.patch").open("x") as f:
    f.write("".join(difflib.unified_diff(base.splitlines(True),current.splitlines(True),fromfile="a/v12/python/tests/manager/test_boundary_inventory.py",tofile="b/v12/python/tests/manager/test_boundary_inventory.py")))
print(output.getvalue(),end="")
print(json.dumps({k:v for k,v in report.items() if k not in ("test_result","lanes","global_residuals")},indent=2))
print(json.dumps({"lane_entries":len(report["lanes"]["entries"]),"expected_probes":len(expected),"declared_probes":len(declared),
                  "lane_unowned":report["lanes"]["unowned"],"lane_orphan_calls":report["lanes"]["orphan_calls"],
                  "global_unowned":len(report["global_residuals"]["unowned"]),"global_orphan_calls":len(report["global_residuals"]["orphan_calls"])}))
assert result.wasSuccessful()
