"""Independent additive-scope and retained-evidence audit; no tests rerun."""
import ast
import hashlib
import json
from pathlib import Path

folder = Path(__file__).parent
root = Path(__file__).resolve().parents[8]
path = root / "v12/python/tests/manager/test_boundary_inventory.py"
candidate = path.read_bytes()
assert candidate == (folder / "final-candidate-120480.py").read_bytes()
digest = hashlib.sha256(candidate).hexdigest()
assert digest == "bc1844e7840527818951b89d51762fedcaa0d1413bcd518dc742184ad3075509"
base = (folder / "base-120480.py").read_bytes()
assert hashlib.sha256(base).hexdigest() == "05c45eba60d79ec3c940305259d35b2c3cc59e32586db3d8da75bded0195c8d8"
old, new = ast.parse(base), ast.parse(candidate)
dump = lambda node: ast.dump(node, include_attributes=False)
named = lambda tree: {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
before, after = named(old), named(new)
assert set(after) - set(before) == {"LanesHaveCompleteReceivingCoverage"}
assert [name for name in before if dump(before[name]) != dump(after[name])] == ["EveryProbeProvesItArrived"]
old_methods, new_methods = named(before["EveryProbeProvesItArrived"]), named(after["EveryProbeProvesItArrived"])
assert set(old_methods) == set(new_methods)
assert [name for name in old_methods if dump(old_methods[name]) != dump(new_methods[name])] == ["lane_probes"]
old_probe, new_probe = old_methods["lane_probes"], new_methods["lane_probes"]
assert [dump(n) for n in old_probe.body[:2]] == [dump(n) for n in new_probe.body[:2]]
assert [dump(n) for n in old_probe.body[3:]] == [dump(n) for n in new_probe.body[5:]]
assert isinstance(old_probe.body[2], ast.Assign) and dump(old_probe.body[2].value) == dump(ast.Dict(keys=[], values=[]))
catalogs = {}
for tree, destination in ((old, {}), (new, {})):
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            destination[node.targets[0].id] = node.value
    catalogs[id(tree)] = destination
for name, count in (("NOT_AN_ENTRY", 4), ("DELEGATED", 1)):
    initial, final = catalogs[id(old)][name], catalogs[id(new)][name]
    assert len(final.keys) == len(initial.keys) + count
    assert [None if n is None else dump(n) for n in initial.keys] == [None if n is None else dump(n) for n in final.keys[count:]]
    assert [dump(n) for n in initial.values] == [dump(n) for n in final.values[count:]]
def other_nodes(tree):
    return [dump(n) for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.ClassDef)) and not (isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("NOT_AN_ENTRY", "DELEGATED"))]
assert other_nodes(old) == other_nodes(new)
verification = json.loads((folder / "verification-120480.json").read_text())
final = json.loads((folder / "final-120480.json").read_text())
assert final["successful"] and final["candidate_sha256"] == digest
lane = verification["lanes"]
assert len(lane["entries"]) == 25 and len(lane["expected"]) == len(lane["declared"]) == 24
assert lane["expected"] == lane["declared"]
assert all(lane[key] == [] for key in ("unowned", "orphan_calls", "missing", "orphan_probes"))
hashes = verification["source_hashes"]
print(json.dumps({"retained_source_hashes": hashes}, indent=2))
report = {"work": "W116972", "claim": 120547, "candidate_sha256": digest,
          "base_sha256": hashlib.sha256(base).hexdigest(),
          "all_existing_scanner_functions_and_other_classes_unchanged": True,
          "all_existing_catalog_entries_and_lane_probe_body_preserved": True,
          "additions": {"delegation": 1, "private_check_classifications": 4, "probe_pairs": 7, "witness_tests": 7},
          "retained_lane_entries": 25, "retained_expected_and_declared_pairs": 24,
          "lane_residuals": 0, "retained_final_positive_control": final["result"],
          "source_hashes_from_verification": hashes}
with Path(__file__).with_suffix(".json").open("x") as output:
    output.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
