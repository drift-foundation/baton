"""Independent correction replay and source scope audit; no source mutation."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import time

started = time.monotonic()
root = Path(__file__).resolve().parents[6]
folder = Path(__file__).parent
sys.path[:0] = [str(root / "v12/python"), str(root / "v12/python/src")]
from tests.manager.test_boundary_inventory import OptionalCapabilityAliasesKeepTheirCrossing

current = (root / "v12/python/tests/manager/test_boundary_inventory.py").read_bytes()
assert current == (folder / "final-candidate-120344.py").read_bytes()
digest = hashlib.sha256(current).hexdigest()
assert digest == "05c45eba60d79ec3c940305259d35b2c3cc59e32586db3d8da75bded0195c8d8"
dump = lambda node: ast.dump(node, include_attributes=False)
named = lambda tree: {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
before = ast.parse((folder / "base-120344.py").read_text())
after = ast.parse(current)
old, new = named(before), named(after)
changed = sorted(name for name in old if dump(old[name]) != dump(new[name]))
assert set(changed) == {"_OriginBindings", "_invoked_capabilities", "_origins", "OptionalCapabilityAliasesKeepTheirCrossing"}
assert set(old) == set(new)
assert [dump(n) for n in before.body if not hasattr(n, "name")] == [dump(n) for n in after.body if not hasattr(n, "name")]
old_methods = named(old["OptionalCapabilityAliasesKeepTheirCrossing"])
new_methods = named(new["OptionalCapabilityAliasesKeepTheirCrossing"])
assert all(dump(node) == dump(new_methods[name]) for name, node in old_methods.items())
assert len(set(new_methods) - set(old_methods)) == 10

previous = ast.parse((folder / "review-120317-probe.py").read_text())
cases = next(ast.literal_eval(node.value) for node in previous.body
             if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "cases" for t in node.targets))
cases["keyword_rebinding_current_and_later"] = '''
def public(session, other):
    performing = getattr(session, "release_token", None)
    answer = performing(key=(performing := other))
    return answer["kind"], performing({})["wrong"]
'''
cases["augmented_rhs_before_rebinding"] = '''
def public(session):
    performing = getattr(session, "release_token", None)
    performing += performing({})["kind"]
    return performing({})["wrong"]
'''
case = OptionalCapabilityAliasesKeepTheirCrossing()
results = {}
for name, source in cases.items():
    crossings, entries = case.model(source)
    injected = case.injected(entries)
    expected = set() if name == "delete_binding_kills_callable" else case.expected(".kind")
    assert injected == expected, (name, injected, expected)
    results[name] = {"source": source, "crossings": crossings, "injected": sorted(injected), "passed": True}
report = {"work": "W120204", "claim": 120459, "candidate_sha256": digest,
          "changed_existing_nodes_since_review": changed, "existing_nodes_and_assertions_preserved": True,
          "added_tests": 10, "results": results, "seconds": time.monotonic() - started}
with Path(__file__).with_suffix(".json").open("x") as output:
    output.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
