"""Static inventory for the W32385 correction re-review."""

import ast
from pathlib import Path


SOURCE = (Path(__file__).resolve().parents[6] / "v12/python/tests/manager/"
          "test_ended_runtime_adoption.py")
tree = ast.parse(SOURCE.read_text())


def called(node):
    names = []
    for one in ast.walk(node):
        if not isinstance(one, ast.Call):
            continue
        if isinstance(one.func, ast.Name):
            names.append(one.func.id)
        elif isinstance(one.func, ast.Attribute):
            names.append(one.func.attr)
    return names


tests = [node for node in ast.walk(tree)
         if isinstance(node, ast.FunctionDef)
         and node.name.startswith("test_")]
ordering = next(node for node in tests if node.name ==
                "test_force_removal_absence_teardown_then_and_only_then_reuse")
names = called(ordering)

print("test methods:", len(tests))
print("ordering-case runtime starts:", names.count("request_runtime_start"))
print("ordering-case activations:", names.count("activated"))
print("ordering-case sibling materializations:", names.count("materialize"))
print("explicit multiple-candidate test methods:",
      [node.name for node in tests
       if "multiple" in node.name or "multiplicity" in node.name])
print("explicit mismatch test methods:",
      [node.name for node in tests if "mismatch" in node.name])
print("explicit sibling test methods:",
      [node.name for node in tests if "sibling" in node.name])
