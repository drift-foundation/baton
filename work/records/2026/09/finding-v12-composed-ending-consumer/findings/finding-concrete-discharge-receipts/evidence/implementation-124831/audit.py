"""Bind final bytes and verify the exact pre-existing test mutation scope."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import stat
import time

started = time.monotonic()
here = Path(__file__).resolve().parent
repo = next(parent for parent in here.parents if (parent / "v12/python/src").is_dir())
base = json.loads((here / "base.json").read_text())
records = []
for row in base:
    path = repo / row["path"]
    original = (here / ("base-" + path.name)).read_text()
    final = path.read_text()
    before, after = ast.parse(original), ast.parse(final)
    if path.name == "test_intake.py":
        expected = original
        for old, new in (
            ('kind="runtime-quiescence", phase=phase)', 'kind="runtime-absent", phase=phase)'),
            ('self.assertEqual(answered["kind"], "runtime-quiescence")', 'self.assertEqual(answered["kind"], "runtime-absent")'),
            ('for kind in ([], 1, "", "contract-runtime"):', 'for kind in ([], 1, "", "contract-runtime", "runtime-quiescence"):'),
            ('for members in ({"kind": "contract-runtime"}, {"phase": "block"},',
             'for members in ({"kind": "contract-runtime"}, {"kind": "runtime-quiescence"}, {"phase": "block"},'),
        ):
            assert expected.count(old) == 1, old
            expected = expected.replace(old, new)
        added = [node for node in after.body if isinstance(node, ast.ClassDef) and node.name == "ConcreteAuthorityDischargeReceipts"]
        assert len(added) == 1
        assert len([node for node in added[0].body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]) == 6
        after.body.remove(added[0])
        gate_class = next(node for node in after.body if isinstance(node, ast.ClassDef) and node.name == "TheQuiescenceGateIsDischargedFromTheCommittedCleanup")
        setup = next(node for node in gate_class.body if isinstance(node, ast.FunctionDef) and node.name == "setUp")
        assert ast.dump(setup) == ast.dump(ast.parse('def setUp(self):\n    super().setUp()\n    self.session.discharge_answer["kind"] = "runtime-absent"\n').body[0])
        gate_class.body.remove(setup)
        assert ast.dump(after) == ast.dump(ast.parse(expected)), "Unscheduled test change"
    else:
        permitted = {"discharge_quiescence_gate", "_adopted_discharge"}
        for tree in (before, after):
            tree.body = [node for node in tree.body if not (isinstance(node, ast.FunctionDef) and node.name in permitted)]
        assert ast.dump(before) == ast.dump(after), "Unrelated application change"
    mode = oct(stat.S_IMODE(path.stat().st_mode))
    assert mode == row["mode"]
    assert all(line == line.rstrip() for line in final.splitlines()), "Trailing whitespace"
    records.append({"path": row["path"], "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "mode": mode})
    (here / ("final-" + path.name)).write_bytes(path.read_bytes())
    (here / ("final-" + path.name + ".patch")).write_text("".join(difflib.unified_diff(original.splitlines(True), final.splitlines(True), fromfile="base/" + row["path"], tofile=row["path"])))
result = {"scope_audit": "PASS", "new_controls": 6, "files": records, "elapsed_seconds": time.monotonic() - started}
(here / "final.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
