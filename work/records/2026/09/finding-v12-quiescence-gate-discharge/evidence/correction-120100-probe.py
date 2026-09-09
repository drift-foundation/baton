"""W119548 claim120100: the presence cases, re-driven after the correction.

The four scenarios and the fixture surgery are the reviewer's, from
`review-120038-probe.py`; what differs is that this writes its OWN
claim-specific output and never touches theirs. That is the discipline the
14:53:10Z review asks for after my unmodified rerun of `review-119974-probe.py`
overwrote its fixed output path.

Disposable Worker Manager fixtures only: no coordination ledger, daemon, live
Authority, socket or application edit.
"""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[6]
sys.path[:0] = [str(root / "v12/python/src"), str(root / "v12/python")]
from tests.manager.test_intake import (
    ATTEMPT, TheQuiescenceGateIsDischargedFromTheCommittedCleanup as Case)
from baton_v12.worker_manager import gate_discharge_of

SPOILED = {"sql-null": ("result", None),
           "json-null": ("result", "null"),
           "foreign-kind": ("kind", "unrelated.operation"),
           "list-result": ("result", "[]")}

results = []
for scenario, (column, value) in SPOILED.items():
    case = Case("test_a_settled_cleanup_discharges_the_gate_and_frees_the_work")
    case.setUp()
    try:
        case.settled()
        case.gated()
        receipt = case.discharge()
        try:
            case.store._connection.execute(
                "UPDATE operations SET " + column + "=? WHERE operation_id=?",
                (value, receipt["operation_id"]))
        except Exception as error:
            # SQL NULL is refused by the store's own CHECK constraint, so it is
            # not a reachable counterexample. Recorded rather than skipped.
            results.append({"scenario": scenario,
                            "fixture_write_refused": type(error).__name__})
            continue
        outcomes = {}
        for name, call in (("discovery",
                            lambda: gate_discharge_of(case.store, ATTEMPT)),
                           ("replay", case.discharge)):
            try:
                outcomes[name] = {"returned": call()}
            except Exception as error:
                outcomes[name] = {"exception": type(error).__name__,
                                  "category": getattr(error, "category", None),
                                  "code": getattr(error, "code", None)}
        results.append({"scenario": scenario, "outcomes": outcomes,
                        "exits_agree": (
                            outcomes["discovery"].get("code")
                            == outcomes["replay"].get("code"))})
    finally:
        case.tearDown()
        case.doCleanups()

paths = ["src/baton_v12/worker_manager/authority_port.py",
         "src/baton_v12/worker_manager/intake.py",
         "src/baton_v12/worker_manager/__init__.py",
         "tests/manager/test_intake.py",
         "tests/manager/test_offers.py",
         "tests/manager/test_secrets.py",
         "tests/manager/test_text_sweep.py"]
report = {"claim": 120100,
          "question": "do both public exits agree on every present invalid "
                      "record, and does only genuine absence answer None",
          "sha256": {p: hashlib.sha256((root / "v12/python" / p).read_bytes())
                     .hexdigest() for p in paths},
          "results": results}
with (Path(__file__).parent / "correction-120100-probe.json").open("x") as out:
    out.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
