"""Current lanes census and public lane_reference boundary observations."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
from tests.manager import test_boundary_inventory as b
from baton_v12 import worker_manager

started = time.monotonic()
entries = b.receiving_entries()
lanes_entries = sorted(e for e in entries if e[1].startswith("lanes.py:"))
owner = b.EveryReceivingEntryHasOneOwner()
records = b.boundary_occurrences()
claimed = b._boundary_claims(records, entries, b.DELEGATED)
_, residual = b._account_boundary_calls(records, claimed, b.NOT_AN_ENTRY)
case = b.EveryProbeProvesItArrived()
try:
    case.setUp()
    expected = {pair for pair in case.expected() if pair[0][1].startswith("lanes.py:")}
    declared = {pair for pair in case.all_probes() if pair[0][1].startswith("lanes.py:")}
finally:
    case.doCleanups()
valid = dict(runtime_attempt_id="attempt-1", authority_uuid=b.UUID, work_id=b.WORK,
             assignment_principal="principal-probe", assignment_scope="scope")
cases = [("valid", valid), ("inactive", dict(valid, assignment_principal=None)),
         ("non-document", []), ("missing-members", {})]
for field in valid:
    cases.append(("malformed-" + field, dict(valid, **{field: []})))
observations = []
for name, value in cases:
    before = copy.deepcopy(value)
    try:
        answer = worker_manager.lane_reference(value)
        observation = {"outcome": "returned", "answer": answer}
    except b.ContractRefusal as failure:
        observation = {"outcome": "ContractRefusal", "category": failure.category,
                       "code": failure.code, "message": failure.message}
    except Exception as failure:
        observation = {"outcome": type(failure).__name__, "message": str(failure)}
    observations.append({"case": name, "input": value, "input_unchanged": value == before, **observation})
paths = [ROOT / "v12/python/tests/manager/test_boundary_inventory.py"]
paths.extend(ROOT / "v12/python/src/baton_v12/worker_manager" / name for name in ("lanes.py", "schema.py", "__init__.py", "attempts.py", "intake.py"))
result = {"source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
          "entries": lanes_entries, "unowned": [e for e in lanes_entries if owner.owner_of(e)[0] is None],
          "orphan_calls": sorted({(r.site, r.kind, r.label) for r in residual if r.site.startswith("lanes.py:")}),
          "expected_count": len(expected), "declared_count": len(declared),
          "missing_probes": sorted(expected - declared), "orphan_probes": sorted(declared - expected),
          "public_export": "lane_reference" in worker_manager.__all__,
          "public_observations": observations, "seconds": time.monotonic() - started}
(HERE / "revalidation-119463.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in ("entries", "source_hashes")}, indent=2))
