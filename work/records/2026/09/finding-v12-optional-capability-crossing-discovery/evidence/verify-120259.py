"""Bounded scanner regression and real-source census; run from repository root."""
import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest

root = Path.cwd()
here = Path(__file__).resolve().parent
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from tests.manager import test_boundary_inventory as b

started = time.monotonic()
classes = (
    "AdoptedHelperOriginsAreContextual",
    "DeclaredMountOriginsStayWithTheirElements",
    "ProviderLabelsStayWithTheirSubdocuments",
    "TheDiscoveryProjectionsAreBoundedAndImmutable",
    "HelperDeclarationsHaveExactAccounting",
)
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(getattr(b, name)) for name in classes)
output = io.StringIO()
result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
report = {"work": "W120204", "claim": 120259, "classes": classes,
          "tests": result.testsRun, "successful": result.wasSuccessful(),
          "output": output.getvalue(), "regression_seconds": time.monotonic() - started}
if result.wasSuccessful():
    b._clear_boundary_projections()
    entries = b.receiving_entries()
    crossing = b._crossings().get("satisfy_gate")
    assert crossing == "authority_port.py:AuthorityPort.satisfy_gate", crossing
    expected = {("injected", crossing, member) for member in ("satisfy_gate", "satisfy_gate.gate", "satisfy_gate.kind", "satisfy_gate.phase")}
    assert expected <= entries
    records = b.boundary_occurrences()
    claims = b._boundary_claims(records, entries, b.DELEGATED)
    _, residual = b._account_boundary_calls(records, claims, b.NOT_AN_ENTRY)
    owner = b.EveryReceivingEntryHasOneOwner()
    report["census"] = {
        "entry_count": len(entries), "satisfy_gate_crossing": crossing,
        "gate_entries": sorted(e for e in entries if e[2].startswith("satisfy_gate")),
        "entries": sorted(entries),
        "unowned": sorted(e for e in entries if owner.owner_of(e)[0] is None),
        "orphan_calls": sorted({(r.site, r.kind, r.label) for r in residual}),
        "lanes_entries": sorted(e for e in entries if e[1].startswith("lanes.py:")),
    }
    nodes = {}
    for source, tree in b._sources():
        for site, node in b._functions(tree, source.name):
            if site in (crossing, "intake.py:discharge_quiescence_gate"):
                origins = b._origins(node, site, b._helper_returns())
                nodes[site] = {"bindings": {name: sorted(b._origin_values(origins.get(name))) for name in ("answer", "answered")},
                               "member_origins": sorted({(origin, member) for piece in b._scope_nodes(node) for origin, member in b._member_origins(piece, origins) if origin.startswith("session:satisfy_gate")})}
    report["origin_sites"] = nodes

path = root / "v12/python/tests/manager/test_boundary_inventory.py"
before = ast.parse((here / "base-120259.py").read_text())
after = ast.parse(path.read_text())
def fingerprint(node):
    return ast.dump(node, include_attributes=False)
changed = {"_source", "_origins", "_crossings", "receiving_entries"}
original = {n.name: n for n in before.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
current = {n.name: n for n in after.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
unchanged = [name for name in original if name not in changed]
assert all(fingerprint(original[name]) == fingerprint(current[name]) for name in unchanged)
assert [fingerprint(n) for n in before.body if not isinstance(n, (ast.ClassDef, ast.FunctionDef))] == [fingerprint(n) for n in after.body if not isinstance(n, (ast.ClassDef, ast.FunctionDef))]
report["scope_audit"] = {"existing_changed_functions": sorted(changed),
                         "unchanged_existing_classes_and_functions": len(unchanged),
                         "new_classes_and_functions": sorted(current.keys() - original.keys()),
                         "existing_catalogs_imports_and_assertions_unchanged": True}
report["source_hashes"] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [path] + sorted((root / "v12/python/src/baton_v12/worker_manager").glob("*.py"))}
report["seconds"] = time.monotonic() - started
with (here / "verification-120259.json").open("x") as file:
    file.write(json.dumps(report, indent=2) + "\n")
print(output.getvalue(), end="")
print(json.dumps({key: value for key, value in report.items() if key not in ("output", "census", "source_hashes")}, indent=2))
if not result.wasSuccessful():
    raise SystemExit(1)
