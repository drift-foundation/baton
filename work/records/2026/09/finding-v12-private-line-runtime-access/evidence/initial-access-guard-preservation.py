"""Verify only approved guard additions, preserving all earlier executable bytes."""
import ast
import hashlib
import json
from pathlib import Path

repo = Path.cwd()
evidence = Path(__file__).parent
paths = ["v12/python/tests/manager/test_boundary_inventory.py",
         "v12/python/tests/tools/test_parallel_runner.py"]
keys = {
    ast.dump(ast.parse(expression, mode="eval").body)
    for expression in [
        '("caller", "workspaces.py:AllocatedRoots.__init__", "_line")',
        '("caller", "workspaces.py:AllocatedRoots.__init__", "_line_proof")',
        '(at("workspaces.py:AllocatedRoots.__init__", "_line_proof"), "a development-line launch proof")'
    ]
}
methods = {"test_line_launch_proof_has_an_exact_live_capability_probe",
           "test_line_launch_metadata_keeps_mint_and_durable_binding"}
counts = {"new_methods": 0, "new_table_or_probe_entries": 0, "new_serial_member": 0}


class RemoveApprovedAdditions(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        if node.name in methods:
            counts["new_methods"] += 1
            return None
        return self.generic_visit(node)

    def visit_Dict(self, node):
        kept = []
        for key, value in zip(node.keys, node.values):
            if key is not None and ast.dump(key) in keys:
                counts["new_table_or_probe_entries"] += 1
            else:
                kept.append((key, value))
        node.keys = [key for key, _ in kept]
        node.values = [value for _, value in kept]
        return self.generic_visit(node)

    def visit_Tuple(self, node):
        kept = []
        for element in node.elts:
            if isinstance(element, ast.Constant) and element.value == "tests.manager.test_private_line_access_engine":
                counts["new_serial_member"] += 1
            else:
                kept.append(element)
        node.elts = kept
        return self.generic_visit(node)


hashes = {}
for name in paths:
    before = (evidence / "initial-access-guard-base" / name).read_bytes()
    after = (repo / name).read_bytes()
    reduced = RemoveApprovedAdditions().visit(ast.parse(after))
    assert ast.dump(reduced) == ast.dump(ast.parse(before)), name
    hashes[name] = {"before": hashlib.sha256(before).hexdigest(),
                    "after": hashlib.sha256(after).hexdigest()}
assert counts == {"new_methods": 2, "new_table_or_probe_entries": 4, "new_serial_member": 1}, counts
initial = json.loads((evidence / "initial-access-manifest.json").read_text())
for name, expected in initial["candidate_sha256"].items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == expected, name
print(json.dumps({"result": "pass", "assertions_and_existing_executable_structure": "unchanged",
                  "approved_additions": counts, "guard_hashes": hashes,
                  "reviewed_initial_candidate_paths_unchanged": 8}, indent=2))
