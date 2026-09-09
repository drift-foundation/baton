"""Retain candidate bytes and verify this claim only added its fixture class."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import stat

here = Path(__file__).resolve().parent
repo = next(parent for parent in here.parents if (parent / "v12/python/src").is_dir())
base = json.loads((here / "base.json").read_text())
final = []
for row in base:
    path = repo / row["path"]
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    final.append({**row, "sha256": digest, "mode": oct(stat.S_IMODE(path.stat().st_mode)),
                  "changed": digest != row["sha256"]})
    assert final[-1]["mode"] == row["mode"]
    if path.name != "test_stage_execution.py":
        assert digest == row["sha256"], path
    else:
        original = (here / "base-test_stage_execution.py").read_text()
        current = payload.decode()
        tree = ast.parse(current)
        added = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "OrdinaryTerminalLifecycle"]
        assert len(added) == 1
        tree.body.remove(added[0])
        assert ast.dump(tree) == ast.dump(ast.parse(original))
        start = current.index("class OrdinaryTerminalLifecycle(")
        end = current.index("class TheWrongRouteClaimDefersInsteadOfStoppingTheSweep(", start)
        assert current[:start] + current[end:] == original
        (here / "candidate-test_stage_execution.py").write_bytes(payload)
        (here / "candidate.patch").write_text("".join(difflib.unified_diff(original.splitlines(True), current.splitlines(True), fromfile=row["path"], tofile=row["path"])))
(here / "final.json").write_text(json.dumps({"files": final, "existing_test_bytes_unchanged": True,
    "existing_test_ast_unchanged": True, "only_added_class": "OrdinaryTerminalLifecycle"}, indent=2) + "\n")
print((here / "final.json").read_text())
