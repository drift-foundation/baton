"""Independent writer query/factory seam audit; 10s budget."""
import ast
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

root = Path.cwd()
here = Path(__file__).resolve().parent
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
os.environ["PYTHONPATH"] = str(root / "v12/python/src")
os.chdir(root / "v12/python")
signal.alarm(10)
start = time.monotonic()
from tests.manager import test_boundary_inventory as b

results = {}
for mode in ("malformed", "valid", "factory_exception"):
    case = b.EveryProbeProvesItArrived()
    case.setUp()
    try:
        connection = case.store._connection
        original = connection.row_factory
        seen = []
        queries = []
        def observing_factory(cursor, values):
            row = original(cursor, values)
            if tuple(column[0] for column in cursor.description) == tuple(b.schema.LINE_WRITER_COLUMNS):
                seen.append(dict(row))
                if mode == "factory_exception":
                    raise RuntimeError("review factory failure")
            return row
        connection.row_factory = observing_factory
        connection.set_trace_callback(queries.append)
        if mode == "valid":
            case.SPOILED = dict(case.SPOILED, identity="writer-probe")
        refusal = None
        try:
            case.spoiling_review_row("writer_of", "line_writers", "writer_id")()
            assert mode == "valid"
        except b.ContractRefusal as error:
            assert mode == "malformed"
            assert (error.category, error.code) == ("integrity", "schema")
            assert "a persisted line writer's writer_id" in error.message
            refusal = error.message
        except RuntimeError as error:
            assert mode == "factory_exception" and str(error) == "review factory failure"
        assert connection.row_factory is observing_factory
        assert len(seen) == 1 and seen[0]["writer_id"] == "writer-probe"
        assert any("SELECT * FROM line_writers WHERE writer_id = 'writer-probe'" in query for query in queries)
        assert not any(query.lstrip().upper().startswith("UPDATE LINE_WRITERS") for query in queries)
        connection.row_factory = original
        connection.set_trace_callback(None)
        assert b.review_cycles.writer_of(case.store, "writer-probe")["writer_id"] == "writer-probe"
        assert connection.execute("SELECT writer_id FROM line_writers WHERE writer_id = ''").fetchone() is None
        results[mode] = {"passed": True, "returned_stored_key": seen[0]["writer_id"], "factory_restored": True, "refusal": refusal}
    finally:
        case.doCleanups()

hashes = json.loads((here / "hashes.json").read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(here / "before.py") == hashes["base_sha256"]
assert sha(here / "candidate.py") == hashes["candidate_sha256"] == sha(root / "v12/python/tests/manager/test_boundary_inventory.py")
def nodes(path):
    tree = ast.parse(path.read_text())
    return {node.name: node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}
before, after = nodes(here / "before.py"), nodes(here / "candidate.py")
changed = [name for name in before if ast.dump(before[name]) != ast.dump(after[name])]
assert changed == ["EveryProbeProvesItArrived"], changed
methods = lambda node: {part.name: ast.dump(part) for part in node.body if isinstance(part, ast.FunctionDef)}
old, new = methods(before[changed[0]]), methods(after[changed[0]])
assert [name for name in old if old[name] != new[name]] == ["spoiling_review_row"]
output = {"candidate_sha256": hashes["candidate_sha256"], "cases": results, "changed_existing_method": "EveryProbeProvesItArrived.spoiling_review_row", "all_other_existing_top_level_functions_and_classes_unchanged": True, "elapsed_seconds": time.monotonic() - start}
(here / "review-116899.json").write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps(output, indent=2))
