"""W117174: verify exact application and retain live module accounting."""
from pathlib import Path
import ast
import hashlib
import io
import json
import sys
import time
import unittest

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent.parent / "finding-declaration-accounting-proposal/evidence"
TARGET = ROOT / "v12/python/tests/manager/test_boundary_inventory.py"
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
from tests.manager import test_boundary_inventory as b


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plain(value):
    return json.loads(json.dumps(value))


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def suite(cls, name):
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, failfast=True).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    (HERE / name).write_text(stream.getvalue())
    print(stream.getvalue())
    assert result.wasSuccessful(), name
    return result.testsRun


def main():
    start = time.monotonic()
    assert Path(b.__file__).resolve() == TARGET.resolve()
    assert digest(TARGET) == "830496b44569e7a88c29771577d616f94b52bcd3066c48f6fa338aab24a30d04"
    packet = json.loads((PROPOSAL / "packet-hashes.json").read_text())
    for name, expected in packet["runtime_hashes_unchanged"].items():
        assert digest(ROOT / name) == expected, name
    # Audit every pre-existing top-level node, including catalogs and guards.
    base = ast.parse((HERE / "base.py").read_text())
    current = ast.parse(TARGET.read_text())
    named = {node.name: node for node in current.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    changed = []
    for node in base.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            other = named[node.name]
            if ast.dump(node) != ast.dump(other):
                assert node.name == "EveryReceivingEntryHasOneOwner"
                methods = {method.name: method for method in other.body if isinstance(method, ast.FunctionDef)}
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and ast.dump(method) != ast.dump(methods[method.name]):
                        changed.append(f"{node.name}.{method.name}")
            continue
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MEMOISED" for t in node.targets):
            continue
        assert any(ast.dump(node) == ast.dump(other) for other in current.body), ast.dump(node)[:120]
    assert changed == ["EveryReceivingEntryHasOneOwner.test_every_boundary_call_belongs_to_an_entry_or_is_declared"]
    focused = suite(b.HelperDeclarationsHaveExactAccounting, "focused.txt")
    b._clear_boundary_projections()
    records = b.boundary_occurrences()
    entries = b.receiving_entries()
    owners = {(site, kind, label, subject) for site, rows in b.owning_validators().items() for kind, label, subject in rows}
    assert {(r.site, r.kind, r.label, r.subject) for r in records} == owners
    claimed = b._boundary_claims(records, entries, b.DELEGATED)
    resolved, residual = b._account_boundary_calls(records, claimed, b.NOT_AN_ENTRY)
    rows = sorted({(r.site, r.kind, r.label) for r in residual})
    retained = json.loads((PROPOSAL / "research.json").read_text())
    assert plain(rows) == retained["candidate_orphan_rows"]
    assert plain([r._asdict() for r in sorted(residual)]) == retained["residuals"]
    links = [{"occurrence": r._asdict(), "owners": [{"occurrence": owner._asdict(), "entries": sorted(claimed[owner])} for owner in sorted(resolved[r])]} for r in sorted(resolved)]
    assert plain(links) == retained["resolved"]
    assert len(entries) == retained["entries"] == 1365
    assert len(records) == retained["occurrences"] == 697
    assert isinstance(records, frozenset) and b.boundary_occurrences() is records
    assert b.boundary_occurrences in b.MEMOISED
    try:
        b.EveryReceivingEntryHasOneOwner().test_every_boundary_call_belongs_to_an_entry_or_is_declared()
    except AssertionError as error:
        assert "boundary calls attributed to no entry" in str(error)
        (HERE / "expected-aggregate-failure.txt").write_text(str(error) + "\n")
    else:
        raise AssertionError("retained residuals must fail the actual aggregate")
    deltas = json.loads((PROPOSAL / "module-deltas.json").read_text())
    modules = []
    for delta in deltas:
        inputs_path = ROOT / delta["dossier"] / "evidence/inputs.json"
        inputs = json.loads(inputs_path.read_text())
        assert digest(ROOT / inputs["runtime_source"]) == inputs["runtime_sha256"]
        old = {tuple(row) for row in inputs["orphan_calls"]}
        new = {row for row in rows if row[0].split(".py:")[0] == delta["module"]}
        assert plain(sorted(new - old)) == delta["added_rows"]
        assert plain(sorted(old - new)) == delta["removed_rows"]
        modules.append({**delta, "state": "live accounting revalidated; independent implementation acceptance pending", "prior_inputs_sha256": digest(inputs_path), "runtime_source": inputs["runtime_source"], "runtime_sha256": inputs["runtime_sha256"], "prior_orphan_calls": sorted(old), "current_orphan_calls": sorted(new), "unchanged_input_counts": {key: len(inputs[key]) for key in ("unowned", "missing_probes", "orphan_probes", "failed_stimuli")}})
    assert sum(len(m["added_rows"]) for m in modules) == 18
    assert sum(len(m["removed_rows"]) for m in modules) == 13
    # Retain a unique owning dossier for every residual, including unchanged modules.
    assignments = []
    scope_paths = sorted(HERE.parent.parent.glob("*/evidence/inputs.json"))
    scope_paths.append(ROOT / "work/records/2026/09/finding-v12-worker-entry-inventory-followup/evidence/inputs.json")
    scopes = [json.loads(path.read_text()) | {"dossier": str(path.parent.parent.relative_to(ROOT))} for path in scope_paths]
    for row in rows:
        matches = [scope for scope in scopes if scope.get("module") == row[0].split(".py:")[0]]
        assert len(matches) == 1, (row, matches)
        scope = matches[0]
        assignments.append({"row": row, "work": scope["work"], "dossier": scope["dossier"]})
    save("module-deltas.json", modules)
    save("live-accounting.json", {"candidate_sha256": digest(TARGET), "entries": len(entries), "occurrences": len(records), "claimed_occurrences": len(claimed), "resolved_occurrences": len(resolved), "residual_occurrences": len(residual), "orphan_rows": rows, "residuals": [r._asdict() for r in sorted(residual)], "resolved": links, "residual_assignments": assignments, "runtime_hashes": packet["runtime_hashes_unchanged"]})
    cache = suite(b.TheDiscoveryProjectionsAreBoundedAndImmutable, "cache.txt")
    assert digest(TARGET) == digest(PROPOSAL / "candidate.py")
    for name, expected in packet["runtime_hashes_unchanged"].items():
        assert digest(ROOT / name) == expected, name
    report = {"focused_passed": focused, "cache_passed": cache, "changed_existing_methods": changed, "canonical_import": True, "matches_reviewed_bytes": True, "owner_projection_parity": True, "exact_retained_links_and_residuals": True, "aggregate_expected_failure": True, "module_delta_scopes": len(modules), "residual_rows_assigned_once": len(assignments), "elapsed_seconds": time.monotonic() - start}
    save("verification.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
