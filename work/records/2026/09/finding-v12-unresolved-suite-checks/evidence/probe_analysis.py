"""Two focused diagnostic questions; no source/test mutation or engine access.

Budget 15 seconds: can the real writer reader reject a malformed returned key,
and does the scanner retain the adopted interrogation origin through _view?
"""
import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[6]
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
from tests.manager import test_boundary_inventory as b
from baton_v12.worker_manager import review_cycles
from baton_v12.contracts import ContractRefusal

case = b.EveryProbeProvesItArrived()
case.setUp()
facts = {}
try:
    case.review_cycle_world()
    facts["uncorrupted_writer"] = review_cycles.writer_of(case.store, "writer-probe")["writer_id"]
    original = case.store._connection.row_factory
    def returned_row(cursor, values):
        result = original(cursor, values)
        if tuple(col[0] for col in cursor.description) == tuple(b.schema.LINE_WRITER_COLUMNS):
            result = dict(result)
            result["writer_id"] = ""
        return result
    case.store._connection.row_factory = returned_row
    try:
        review_cycles.writer_of(case.store, "writer-probe")
    except ContractRefusal as error:
        facts["corrupt_returned_key"] = {"category": error.category, "code": error.code, "message": error.message}
    else:
        raise AssertionError("malformed returned writer identity was accepted")
    finally:
        case.store._connection.row_factory = original
finally:
    case.doCleanups()

tree = next(tree for path, tree in b._sources() if path.name == "interrogation.py")
site, node = next((site, node) for site, node in b._functions(tree, "interrogation.py") if node.name == "interrogation_of")
origins = b._origins(node, site, b._helper_returns())
facts["interrogation_of_origins"] = origins
facts["interrogation_helper_reads"] = sorted(b._through_helpers(b._crossings(), site, node, origins, b._helpers(tree, "interrogation.py")))
facts["flat_column_gap"] = sorted(b.columns_read() - {e[2].split(".")[-1] for e in b.receiving_entries() if e[0] == "adopted" and "." in e[2]})
(Path(__file__).parent / "probe-analysis.json").write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n")
print(json.dumps(facts, sort_keys=True))
