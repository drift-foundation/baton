import ast
import copy
import difflib
import hashlib
import io
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch

start = time.monotonic()
from tests.manager import test_boundary_inventory as b

evidence = Path(__file__).resolve().parent
path = Path(b.__file__)
base = (evidence / "base-121055.py").read_text()
candidate = path.read_text()
report = {"base_sha256": hashlib.sha256(base.encode()).hexdigest(), "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest()}
assert report["base_sha256"] == "918f8d9a9b8d342c6ed276c49f5c84c2326312d70ecb650a63d7f961480f2e7d"

# Reuse the accepted runtime/schema/boundary digest evidence.
accepted = json.loads(Path("work/records/2026/09/finding-v12-adopted-column-owner-precedence/evidence/research-120810.json").read_text())
runtime_hashes = {name: sha for name, sha in accepted["hashes"].items() if not name.endswith("test_boundary_inventory.py")}
for name, sha in runtime_hashes.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
report["runtime_hashes"] = runtime_hashes

old = ast.parse(base)
new = ast.parse(candidate)
stripped = copy.deepcopy(new)
added = {
    ("caller", "review_cycles.py:review_of", "attachment_id"): ("review_cycles.py:_attachment", "caller:attachment_id"),
    ("caller", "review_cycles.py:verdict_of", "verdict_id"): ("review_cycles.py:_verdict_row", "caller:verdict_id"),
}
labels = {
    ("caller", "review_cycles.py:review_of", "attachment_id"): "a review attachment identity",
    ("caller", "review_cycles.py:verdict_of", "verdict_id"): "a checkpoint verdict identity",
}
named = lambda tree, name: next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name)
delegation = next(node.value for node in stripped.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DELEGATED" for t in node.targets))
assert dict(zip(map(ast.literal_eval, delegation.keys[:2]), map(ast.literal_eval, delegation.values[:2]))) == added
del delegation.keys[:2]
del delegation.values[:2]
probes = named(named(stripped, "EveryProbeProvesItArrived"), "review_cycle_probes")
direct = next(node.value for node in probes.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "direct" for t in node.targets))
for key, (entry, label) in zip(direct.keys[:2], labels.items()):
    site = entry[1].split(":")[1]
    expected = ast.parse(f"(at({site!r}, {entry[2]!r}), {label!r})", mode="eval").body
    assert ast.dump(key) == ast.dump(expected)
del direct.keys[:2]
del direct.values[:2]
stripped.body.remove(named(stripped, "ReviewReaderIdentitiesReachTheirOwners"))
assert ast.dump(stripped) == ast.dump(old), "change outside two additive mappings/probes and one new control class"
report["all_existing_ast_preserved"] = True

initial = json.loads((evidence / "verification-121055.json").read_text())
initial_source = (evidence / "candidate-121055.py").read_text()
assert initial_source.count('self.assertEqual(owner.owner_of(entry), ("delegated", {label}))') == 1
assert initial_source.replace('self.assertEqual(owner.owner_of(entry), ("delegated", {label}))', 'self.assertEqual(owner.owner_of(entry), ("delegated", [label]))') == candidate
report["reused_initial_passes"] = 5
report["initial_seconds"] = initial["seconds"]
report["reused_corrected_control"] = "Passed in verify-final-121055.py before its resolution-equality assertion failed; no product change since."
assert candidate == (evidence / "final-candidate-121055.py").read_text()
out = io.StringIO()
suite = unittest.defaultTestLoader.loadTestsFromName("tests.manager.test_boundary_inventory.ReviewReaderIdentitiesReachTheirOwners.test_exact_reader_entries_have_only_their_forwarded_identity_owner")
result = unittest.TextTestRunner(stream=out, verbosity=2).run(suite)
report.update(work="W121031", claim=121106, test_log=out.getvalue(), success=result.wasSuccessful(), seconds=time.monotonic()-start)
with (evidence / "review-121106.json").open("x") as output:
    json.dump(report, output, indent=2)
print(json.dumps(report, indent=2))
assert result.wasSuccessful(), out.getvalue()
