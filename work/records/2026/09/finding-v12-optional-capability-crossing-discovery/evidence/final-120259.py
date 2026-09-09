"""Two subprocess checks with inherited package paths, then the final census."""
import ast
import hashlib
import io
import json
from pathlib import Path
import time
import unittest
from tests.manager import test_boundary_inventory as b

here = Path(__file__).resolve().parent
root = Path.cwd()
started = time.monotonic()
prior = json.loads((here / "verification-120259.json").read_text())
path = root / "v12/python/tests/manager/test_boundary_inventory.py"
assert hashlib.sha256(path.read_bytes()).hexdigest() == prior["source_hashes"][str(path.relative_to(root))]
names = ["test_member_reassignment_is_finite_and_applies_each_assignment_once",
         "test_recursive_member_expansion_ends_at_recursive_reentry"]
output = io.StringIO()
result = unittest.TextTestRunner(stream=output).run(unittest.TestSuite(b.AdoptedHelperOriginsAreContextual(name) for name in names))
assert result.wasSuccessful(), output.getvalue()
entries = b.receiving_entries()
records = b.boundary_occurrences()
claims = b._boundary_claims(records, entries, b.DELEGATED)
_, residual = b._account_boundary_calls(records, claims, b.NOT_AN_ENTRY)
owner = b.EveryReceivingEntryHasOneOwner()
crossing = b._crossings().get("satisfy_gate")
assert crossing == "authority_port.py:AuthorityPort.satisfy_gate"
gate_entries = sorted(e for e in entries if e[2].startswith("satisfy_gate"))
assert gate_entries == [("injected", crossing, value) for value in ("satisfy_gate", "satisfy_gate.gate", "satisfy_gate.kind", "satisfy_gate.phase")]
nodes = {}
for source, tree in b._sources():
    for site, node in b._functions(tree, source.name):
        if site in (crossing, "intake.py:discharge_quiescence_gate"):
            origins = b._origins(node, site, b._helper_returns())
            nodes[site] = {
                "bindings": {name: sorted(b._origin_values(origins.get(name))) for name in ("answer", "answered")},
                "member_origins": sorted({(origin, member) for piece in b._scope_nodes(node) for origin, member in b._member_origins(piece, origins) if origin.startswith("session:satisfy_gate")})}
report = {
    "work": "W120204", "claim": 120259, "subprocess_tests": names, "result": output.getvalue(),
    "entry_count": len(entries), "entries": sorted(entries), "gate_entries": gate_entries,
    "origin_sites": nodes,
    "unowned": sorted(e for e in entries if owner.owner_of(e)[0] is None),
    "orphan_calls": sorted({(r.site, r.kind, r.label) for r in residual}),
    "lanes_entries": sorted(e for e in entries if e[1].startswith("lanes.py:")),
    "scope_audit": prior["scope_audit"],
    "source_hashes": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [path] + sorted((root / "v12/python/src/baton_v12/worker_manager").glob("*.py"))},
    "seconds": time.monotonic() - started,
}
with (here / "final-120259.json").open("x") as file:
    file.write(json.dumps(report, indent=2) + "\n")
print(json.dumps({key: value for key, value in report.items() if key not in ("entries", "unowned", "orphan_calls", "source_hashes", "lanes_entries")}, indent=2))
