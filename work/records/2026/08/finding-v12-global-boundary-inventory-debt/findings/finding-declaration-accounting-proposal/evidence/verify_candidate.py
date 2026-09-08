from pathlib import Path
import importlib.util
import io
import json
import sys
import time
import unittest

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
start = time.monotonic()
name = "tests.manager._w116962_candidate"
spec = importlib.util.spec_from_file_location(name, HERE / "candidate.py")
m = importlib.util.module_from_spec(spec)
sys.modules[name] = m
spec.loader.exec_module(m)
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(m.HelperDeclarationsHaveExactAccounting))
(HERE / "candidate-controls.txt").write_text(stream.getvalue())
print(stream.getvalue())
assert result.wasSuccessful()
m._clear_boundary_projections()
records = m.boundary_occurrences()
claimed = m._boundary_claims(records, m.receiving_entries(), m.DELEGATED)
_, residual = m._account_boundary_calls(records, claimed, m.NOT_AN_ENTRY)
rows = sorted({(r.site, r.kind, r.label) for r in residual})
retained = json.loads((HERE / "research.json").read_text())
assert [list(row) for row in rows] == retained["candidate_orphan_rows"]
case = m.EveryReceivingEntryHasOneOwner()
with case.assertRaisesRegex(AssertionError, "boundary calls attributed to no entry"):
    case.test_every_boundary_call_belongs_to_an_entry_or_is_declared()
assert m.boundary_occurrences() is records
assert isinstance(records, frozenset)
assert m.boundary_occurrences in m.MEMOISED
report = {"candidate_controls_passed": result.testsRun, "matches_proposal_rows": True, "orphan_rows": len(rows), "aggregate_still_fails_on_residuals": True, "new_projection_cached_immutable_registered": True, "elapsed_seconds": time.monotonic() - start}
(HERE / "candidate-verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
