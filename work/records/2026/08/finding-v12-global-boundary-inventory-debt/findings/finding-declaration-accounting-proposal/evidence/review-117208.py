"""Independent candidate cache and exact-origin checks; budget15s."""
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import signal
import sys
import time
import unittest
from unittest.mock import patch

root = Path.cwd()
here = Path(__file__).resolve().parent
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
signal.alarm(15)
start = time.monotonic()
manifest = json.loads((here / "packet-hashes.json").read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for group in ("packet_hashes", "runtime_hashes_unchanged"):
    for path, expected in manifest[group].items():
        assert sha(root / path) == expected, path
assert sha(root / "v12/python/tests/manager/test_boundary_inventory.py") == manifest["live_sha256"]
name = "tests.manager._review117208"
spec = importlib.util.spec_from_file_location(name, here / "candidate.py")
b = importlib.util.module_from_spec(spec)
sys.modules[name] = b
spec.loader.exec_module(b)
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(b.TheDiscoveryProjectionsAreBoundedAndImmutable))
(here / "review-117208-cache.txt").write_text(stream.getvalue())
assert result.wasSuccessful(), stream.getvalue()
records = b.boundary_occurrences()
assert isinstance(records, frozenset)
assert all(isinstance(r.call, tuple) and all(isinstance(v, (str, int)) for v in r.call) for r in records)
entries = b.receiving_entries()
assert len(entries) == 1365
assert {(r.site, r.kind, r.label, r.subject) for r in records} == {(site, kind, label, subject) for site, rows in b.owning_validators().items() for kind, label, subject in rows}
claims = b._boundary_claims(records, entries, b.DELEGATED)
resolved, residual = b._account_boundary_calls(records, claims, b.NOT_AN_ENTRY)
research = json.loads((here / "research.json").read_text())
rows = sorted({(r.site, r.kind, r.label) for r in residual})
assert [list(row) for row in rows] == research["candidate_orphan_rows"]
assert len(records) == 697 and len(residual) == 79 and len(rows) == 77

fragment = '''
def _check(row):
    return boundaries.text(row["state"], "same state")
def first(connection):
    row = connection.execute("SELECT * FROM runtime_lanes").fetchone()
    return _check(row)
def second(connection):
    row = connection.execute("SELECT * FROM runtime_lanes").fetchone()
    return _check(row)
'''
b._clear_boundary_projections()
try:
    with patch.object(b, "_sources", lambda: ((Path("independent.py"), ast.parse(fragment)),)):
        entries = b.receiving_entries()
        records = b.boundary_occurrences()
        first = {entry for entry in entries if entry[1] == "independent.py:first"}
        claims = b._boundary_claims(records, first, {})
        _, residual = b._account_boundary_calls(records, claims, {})
        assert {(r.site, r.label, r.subject) for r in residual} == {("independent.py:second", "same state", "read:independent.py:second|runtime_lanes[state]")}
        owner = next(iter(claims))
        variants = {owner._replace(call=(*owner.call[:2], owner.call[2] + 1, *owner.call[3:])), owner._replace(subject=owner.subject + "[other]"), owner._replace(kind="identity")}
        _, residual2 = b._account_boundary_calls(records | variants, claims, {})
        assert residual2 == residual | variants
finally:
    b._clear_boundary_projections()
output = {"candidate_sha256": sha(here / "candidate.py"), "live_unchanged": True, "manifest_and_runtime_hashes_match": True, "existing_cache_checks_passed": result.testsRun, "source_origin_and_occurrence_discriminators_pass": True, "owner_projection_parity": True, "entries": 1365, "occurrences": 697, "residual_occurrences": 79, "residual_rows": 77, "retained_residuals_match": True, "elapsed_seconds": time.monotonic() - start}
(here / "review-117208.json").write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps(output, indent=2))
