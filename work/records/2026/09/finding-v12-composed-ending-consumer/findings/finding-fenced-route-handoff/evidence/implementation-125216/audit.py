"""Bind the five-path candidate and audit additive implementation/test scope."""
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
records = []
new_tests = 0
for row in json.loads((here / "base.json").read_text()):
    path = repo / row["path"]
    original = (here / ("base-" + path.name)).read_text()
    final = path.read_text()
    if path.suffix == ".py":
        before, after = ast.parse(original), ast.parse(final)
        if path.name == "core.py":
            core = next(node for node in after.body if isinstance(node, ast.ClassDef) and node.name == "Core")
            added = [node for node in core.body if isinstance(node, ast.FunctionDef) and node.name == "route_fenced"]
            assert len(added) == 1
            core.body.remove(added[0])
        elif path.name == "session.py":
            for node in after.body:
                if not isinstance(node, ast.Assign):
                    continue
                names = [target.id for target in node.targets if isinstance(target, ast.Name)]
                if "_TRANSITIONS" in names:
                    index = next(i for i, key in enumerate(node.value.keys) if key.value == "route_fenced")
                    assert ast.literal_eval(node.value.values[index]) == {"required": ("expect", "operation_id", "fence_operation_id", "from_route", "to_route"), "optional": ()}
                    del node.value.keys[index]
                    del node.value.values[index]
                if "_ASSIGNMENT_FIRST" in names:
                    elements = node.value.args[0].elts
                    elements.remove(next(value for value in elements if value.value == "route_fenced"))
        else:
            name = "FencedRouteHandoff" if path.name == "test_assignment.py" else "FencedRouteSession"
            added = [node for node in after.body if isinstance(node, ast.ClassDef) and node.name == name]
            assert len(added) == 1
            new_tests += sum(isinstance(node, ast.FunctionDef) and node.name.startswith("test_") for node in added[0].body)
            after.body.remove(added[0])
            if path.name == "test_session.py":
                old = '"publish", "reject_plan", "review", "satisfy_gate",'
                assert original.count(old) == 1
                before = ast.parse(original.replace(old, '"publish", "reject_plan", "review", "route_fenced", "satisfy_gate",'))
        assert ast.dump(before) == ast.dump(after), f"Unscheduled prior AST change: {path}"
    else:
        start = final.index("## Committed next-role handoff\n")
        end = final.index("## Deployment wiring\n", start)
        assert final[:start] + final[end:] == original
    mode = oct(stat.S_IMODE(path.stat().st_mode))
    assert mode == row["mode"]
    assert all(line == line.rstrip() for line in final.splitlines())
    records.append({"path": row["path"], "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "mode": mode})
    (here / ("final-" + path.name)).write_bytes(path.read_bytes())
    (here / ("final-" + path.name + ".patch")).write_text("".join(difflib.unified_diff(original.splitlines(True), final.splitlines(True), fromfile="base/" + row["path"], tofile=row["path"])))
assert new_tests == 15
result = {"scope_audit": "PASS", "new_tests": new_tests, "files": records, "elapsed_seconds": time.monotonic() - started}
(here / "final.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
