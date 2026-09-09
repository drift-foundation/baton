"""Final correction checks; run from repo root with inherited package PYTHONPATH."""
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
classes = ("OptionalCapabilityAliasesKeepTheirCrossing", "AdoptedHelperOriginsAreContextual",
           "DeclaredMountOriginsStayWithTheirElements", "ProviderLabelsStayWithTheirSubdocuments",
           "TheDiscoveryProjectionsAreBoundedAndImmutable", "HelperDeclarationsHaveExactAccounting")
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(getattr(b, name)) for name in classes))
report = {"work": "W120204", "claim": 120344, "classes": classes, "tests": result.testsRun,
          "successful": result.wasSuccessful(), "test_result": stream.getvalue(),
          "regression_seconds": time.monotonic() - started}
path = root / "v12/python/tests/manager/test_boundary_inventory.py"
current = path.read_text()
base = (here / "base-120344.py").read_text()
old = ast.parse(base)
new = ast.parse(current)
fingerprint = lambda node: ast.dump(node, include_attributes=False)
before = {n.name: n for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
after = {n.name: n for n in new.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
changed = {name for name in before if fingerprint(before[name]) != fingerprint(after[name])}
assert changed == {"_OriginBindings", "_invoked_capabilities", "_origins", "OptionalCapabilityAliasesKeepTheirCrossing"}, changed
old_tests = {n.name: fingerprint(n) for n in before["OptionalCapabilityAliasesKeepTheirCrossing"].body if isinstance(n, ast.FunctionDef)}
new_tests = {n.name: fingerprint(n) for n in after["OptionalCapabilityAliasesKeepTheirCrossing"].body if isinstance(n, ast.FunctionDef)}
assert all(new_tests[name] == value for name, value in old_tests.items())
assert [fingerprint(n) for n in old.body if not isinstance(n, (ast.FunctionDef, ast.ClassDef))] == [fingerprint(n) for n in new.body if not isinstance(n, (ast.FunctionDef, ast.ClassDef))]
report["scope"] = {"changed_existing_nodes": sorted(changed), "unchanged_other_nodes": len(before) - len(changed),
                   "preserved_existing_alias_class_methods": len(old_tests),
                   "added_tests": sorted(new_tests.keys() - old_tests.keys()),
                   "catalogs_and_existing_assertions_unchanged": True}
if result.wasSuccessful():
    b._clear_boundary_projections()
    entries = b.receiving_entries()
    crossing = b._crossings().get("satisfy_gate")
    assert crossing == "authority_port.py:AuthorityPort.satisfy_gate"
    gate = sorted(e for e in entries if e[2].startswith("satisfy_gate"))
    assert gate == [("injected", crossing, name) for name in ("satisfy_gate", "satisfy_gate.gate", "satisfy_gate.kind", "satisfy_gate.phase")]
    records = b.boundary_occurrences()
    claims = b._boundary_claims(records, entries, b.DELEGATED)
    _, residual = b._account_boundary_calls(records, claims, b.NOT_AN_ENTRY)
    owner = b.EveryReceivingEntryHasOneOwner()
    previous = json.loads((here / "final-120259.json").read_text())
    unowned = sorted(e for e in entries if owner.owner_of(e)[0] is None)
    orphans = sorted({(r.site, r.kind, r.label) for r in residual})
    report["census"] = {"count": len(entries), "gate_entries": gate,
                       "entries": sorted(entries), "unowned": unowned, "orphan_calls": orphans,
                       "same_entries_as_prior": sorted(entries) == [tuple(e) for e in previous["entries"]],
                       "same_unowned_as_prior": unowned == [tuple(e) for e in previous["unowned"]],
                       "same_orphans_as_prior": orphans == [tuple(e) for e in previous["orphan_calls"]]}
report["source_hashes"] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [path] + sorted((root / "v12/python/src/baton_v12/worker_manager").glob("*.py"))}
report["seconds"] = time.monotonic() - started
with (here / "verification-120344.json").open("x") as f:f.write(json.dumps(report, indent=2) + "\n")
with (here / "candidate-120344.py").open("x") as f:f.write(current)
with (here / "candidate-120344.patch").open("x") as f:
    f.write("".join(difflib.unified_diff(base.splitlines(True), current.splitlines(True), fromfile="a/v12/python/tests/manager/test_boundary_inventory.py", tofile="b/v12/python/tests/manager/test_boundary_inventory.py")))
print(stream.getvalue(), end="")
print(json.dumps({k: v for k, v in report.items() if k not in ("test_result", "source_hashes", "census")}, indent=2))
if result.wasSuccessful():
    print(json.dumps({k:v for k,v in report["census"].items() if k not in ("entries", "unowned", "orphan_calls")}, indent=2))
assert result.wasSuccessful()
