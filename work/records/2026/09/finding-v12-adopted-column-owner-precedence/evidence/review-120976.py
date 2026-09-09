import ast
import hashlib
import json
import time
from pathlib import Path
from tests.manager import test_boundary_inventory as b

start = time.monotonic()
evidence = Path(__file__).resolve().parent
current = Path(b.__file__).read_bytes()
assert current == (evidence / "final-candidate-120897.py").read_bytes()
base = ast.parse((evidence / "base-120897.py").read_bytes())
candidate = ast.parse(current)
changed = {"_owned_here", "_boundary_claims", "_account_boundary_calls"}
by_name = {n.name: n for n in candidate.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
for node in base.body:
    name = getattr(node, "name", None)
    if name in changed:
        continue
    if name is not None:
        assert ast.dump(node) == ast.dump(by_name[name]), name
    else:
        assert any(ast.dump(node) == ast.dump(n) for n in candidate.body)

# Check the final delegate-only adjustment against the already measured candidate.
prior = ast.parse((evidence / "candidate-120897.py").read_bytes())
adjusted = ast.parse(current)
new_class = next(n for n in adjusted.body if isinstance(n, ast.ClassDef) and n.name == "DuplicateColumnChecksRequireOwnedWitnesses")
new_class.body = [n for n in new_class.body if getattr(n, "name", None) != "test_exact_delegate_queries_keep_their_existing_selection"]
owned = next(n for n in adjusted.body if isinstance(n, ast.FunctionDef) and n.name == "_owned_here")
guard = next(n for n in owned.body if isinstance(n, ast.If))
assert ast.unparse(guard.test) == "entry is not None and covering"
guard.test = guard.test.values[0]
assert ast.dump(adjusted) == ast.dump(prior)

research = json.loads((evidence / "research-120810.json").read_text())
for path, sha in research["hashes"].items():
    if not path.endswith("test_boundary_inventory.py"):
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha

rows = []
for site, table, column, label in (
    ("checkpoint_of", "line_checkpoints", "fence", "a persisted line checkpoint"),
    ("integration_checkpoint", "integration_eligibility", "verdict_id", "persisted integration eligibility"),
):
    case = b.EveryProbeProvesItArrived()
    case.setUp()
    entry = ("adopted", "review_cycles.py:" + site, table + "." + column)
    try:
        labels = b.layer_labels(entry)
        assert labels == [label]
        try:
            case.spoiling_review_row(site, table, column)()
        except b.ContractRefusal as refusal:
            assert (refusal.category, refusal.code) == ("integrity", "schema")
            assert label in refusal.message
            rows.append({"entry": entry, "selected": labels, "actual": [refusal.category, refusal.code, refusal.message]})
        else:
            raise AssertionError("malformed adopted column was accepted")
    finally:
        case.doCleanups()
report = {"work": "W120785", "claim": 120976, "candidate_sha256": hashlib.sha256(current).hexdigest(), "scope": "All prior AST preserved except three approved helpers; final adjustment is exactly covering guard plus additive control", "runtime_hashes_unchanged": True, "public_probes": rows, "seconds": time.monotonic() - start}
with (evidence / "review-120976.json").open("x") as output:
    json.dump(report, output, indent=2)
print(json.dumps(report, indent=2))
