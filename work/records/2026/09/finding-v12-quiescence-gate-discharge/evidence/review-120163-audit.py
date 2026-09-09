"""Read-only candidate/scope audit; writes only a new exclusive evidence file."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[6]
evidence = Path(__file__).parent
reported = json.loads((evidence / "correction-120100-probe.json").read_text())
paths = list(reported["sha256"])
actual = {p: hashlib.sha256((root / "v12/python" / p).read_bytes()).hexdigest()
          for p in paths}
assert actual == reported["sha256"], "candidate changed since retained probe"

def baseline(path):
    return subprocess.check_output(["git", "show", "HEAD:v12/python/" + path],
                                   cwd=root, text=True)

def methods(tree):
    return {cls.name + "." + method.name: ast.dump(method)
            for cls in tree.body if isinstance(cls, ast.ClassDef)
            for method in cls.body if isinstance(method, ast.FunctionDef)
            and method.name.startswith("test_")}

tests = {}
for path in paths:
    if not path.startswith("tests/"):
        continue
    old = ast.parse(baseline(path))
    new = ast.parse((root / "v12/python" / path).read_text())
    before, after = methods(old), methods(new)
    changed = [name for name, value in before.items() if after.get(name) != value]
    tests[path] = {"baseline_methods": len(before), "changed_or_removed": changed,
                   "added_methods": sorted(set(after) - set(before))}
    if path.endswith("test_text_sweep.py"):
        # The exact approved two dictionary entries are the only AST change.
        class RemoveApproved(ast.NodeTransformer):
            def visit_Dict(self, node):
                self.generic_visit(node)
                kept = [(key, value) for key, value in zip(node.keys, node.values)
                        if not (isinstance(key, ast.Constant) and key.value in
                                ("discharge_quiescence_gate", "gate_discharge_of"))]
                node.keys = [key for key, _ in kept]
                node.values = [value for _, value in kept]
                return node
        assert ast.dump(RemoveApproved().visit(new)) == ast.dump(old)
        tests[path]["only_two_approved_entries_added"] = True
    else:
        assert not changed, (path, changed)

path = "src/baton_v12/worker_manager/intake.py"
old = ast.parse(baseline(path))
new = ast.parse((root / "v12/python" / path).read_text())
unchanged_helpers = {}
for name in ("authorize_cleanup", "destroy_operation", "_committed"):
    before = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == name)
    after = next(node for node in new.body if isinstance(node, ast.FunctionDef) and node.name == name)
    unchanged_helpers[name] = ast.dump(before) == ast.dump(after)
assert all(unchanged_helpers.values())
diff_check = subprocess.run(["git", "diff", "--check", "--"] +
                            ["v12/python/" + p for p in paths], cwd=root,
                            capture_output=True, text=True)
assert diff_check.returncode == 0, diff_check.stdout + diff_check.stderr
manifest_digest = hashlib.sha256(json.dumps(actual, sort_keys=True,
                                           separators=(",", ":")).encode()).hexdigest()
report = {"claim": 120163, "sha256": actual,
          "manifest_sha256": manifest_digest,
          "manifest_encoding": "UTF-8 json.dumps(sha256, sort_keys=True, separators=(',', ':'))",
          "baseline": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
          "test_scope": tests, "unchanged_helpers": unchanged_helpers,
          "diff_check": "passed", "test_execution": "none; retained candidate evidence audited"}
with (evidence / "review-120163-audit.json").open("x") as output:
    output.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
