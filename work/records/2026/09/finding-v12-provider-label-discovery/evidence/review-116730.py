"""Independent provider pairing and retained-evidence audit; budget 10 seconds."""
import ast
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
signal.alarm(10)
start = time.monotonic()
spec = importlib.util.spec_from_file_location("tests.manager.review_inventory", HERE / "candidate.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

def project(body):
    tree = ast.parse('''
def _validate(part, caption):
    boundaries.document(part, f"ending {caption}")
def _forward(part, *, caption):
    _validate(part, caption)
def consume(answer, unknown):
''' + body)
    returns = b._returned_origins([(Path("independent.py"), tree)])
    site = "independent.py:consume"
    node = dict(b._functions(tree, "independent.py"))[site]
    origins = b._origins(node, site, returns, seed={"answer": "session:destroy"})
    rows = set(b._calls_in(node, origins, site))
    for where, helper, inside in b._delegations(node, origins, b._helpers(tree, "independent.py"), site=site, returns=returns):
        rows.update(b._calls_in(helper, inside, where))
    return rows

cases = {
    "nested_keyword_pair": ('''    for key in ("credentials", "launch"):
        _forward(answer[key], caption=key)
''', {("document", "ending " + key, "session:destroy[" + key + "]") for key in ("credentials", "launch")}),
    "actual_cross_pair": ('''    for key in ("credentials", "launch"):
        _forward(answer["launch"], caption=key)
''', {("document", "ending " + key, "session:destroy[launch]") for key in ("credentials", "launch")}),
    "nested_direct_pair": ('''    for key in ("credentials", "launch"):
        for field in ("state", "why"):
            boundaries.text(answer[key][field], f"{key}:{field}")
''', {("text", key + ":" + field, "session:destroy[" + key + "][" + field + "]") for key in ("credentials", "launch") for field in ("state", "why")}),
    "unknown_explicit": ('''    _forward(answer[unknown], caption=unknown)
''', {("document", "ending {caption}", "session:destroy")}),
}
results = {}
for name, (body, expected) in cases.items():
    actual = project(body)
    results[name] = {"passed": actual == expected, "actual": sorted(actual), "expected": sorted(expected)}
    assert actual == expected, name

hashes = json.loads((HERE / "hashes.json").read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(HERE / "before.py") == hashes["before_sha256"]
assert sha(HERE / "candidate.py") == hashes["candidate_sha256"] == sha(ROOT / "v12/python/tests/manager/test_boundary_inventory.py")
classes = lambda path: {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_text()).body if isinstance(node, ast.ClassDef)}
before, after = classes(HERE / "before.py"), classes(HERE / "candidate.py")
changed = sorted(name for name in before if before[name] != after.get(name))
assert changed == ["_OriginBindings"], changed
assert len(before) - len(changed) == 26
census = json.loads((HERE / "census.json").read_text())
assert census["candidate_sha256"] == hashes["candidate_sha256"]
for rows, grouped, expected_count, expected_modules in (("unowned", "unowned_by_module", 183, 15), ("orphans", "orphan_by_module", 72, 12)):
    values = census[rows]
    assert len(values) == len(set(map(tuple, values))) == expected_count
    actual = dict(collections.Counter(row[1 if rows == "unowned" else 0].split(":")[0] for row in values))
    assert actual == census[grouped] and len(actual) == expected_modules
assert census["entry_count"] == 1365 and len(census["failures"]) == 2 and not census["errors"]
symbolic = [row for row in census["orphans"] if "{provider}" in row[2]]
assert len(symbolic) == 2, symbolic
output = {"candidate_sha256": hashes["candidate_sha256"], "cases": results, "changed_baseline_classes": changed, "unchanged_baseline_classes": 26, "census_entries": 1365, "unowned": 183, "orphans": 72, "symbolic_provider_orphans": symbolic, "elapsed_seconds": time.monotonic() - start}
(HERE / "review-116730.json").write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps(output, indent=2))
