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
(evidence / "final-candidate-121055.py").write_text(candidate)
(evidence / "final-candidate-121055.patch").write_text("".join(difflib.unified_diff(base.splitlines(True), candidate.splitlines(True), fromfile="a/v12/python/tests/manager/test_boundary_inventory.py", tofile="b/v12/python/tests/manager/test_boundary_inventory.py")))

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
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestSuite([b.ReviewReaderIdentitiesReachTheirOwners("test_exact_reader_entries_have_only_their_forwarded_identity_owner")]))
report["focused"] = {"tests": result.testsRun, "successful": result.wasSuccessful(), "output": stream.getvalue()}
if not result.wasSuccessful():
    report["seconds"] = time.monotonic() - start
    (evidence / "final-verification-121055.json").write_text(json.dumps(report, indent=2))
    print(stream.getvalue())
    raise SystemExit(1)

# Reuse discovery/cache once; replay only the old catalog against this same
# source snapshot. No second module import or duplicate whole-suite run.
entries = b.receiving_entries()
records = b.boundary_occurrences()
old_delegated = {entry: value for entry, value in b.DELEGATED.items() if entry not in added}
old_method = named(named(old, "EveryProbeProvesItArrived"), "review_cycle_probes")
namespace = dict(vars(b))
exec(compile(ast.Module(body=[old_method], type_ignores=[]), "<accepted-reader-catalog>", "exec"), namespace)
case = b.EveryProbeProvesItArrived()
case.setUp()
owner = b.EveryReceivingEntryHasOneOwner()
try:
    with patch.object(b, "DELEGATED", old_delegated), patch.object(b.EveryProbeProvesItArrived, "review_cycle_probes", namespace["review_cycle_probes"]):
        before_expected = case.expected()
        before_declared = set(case.all_probes())
        before_owners = {entry: owner.owner_of(entry) for entry in entries}
        before_claims = b._boundary_claims(records, entries, b.DELEGATED)
        before_resolved, before_residual = b._account_boundary_calls(records, before_claims, b.NOT_AN_ENTRY)
    after_expected = case.expected()
    after_declared = set(case.all_probes())
    after_owners = {entry: owner.owner_of(entry) for entry in entries}
    after_claims = b._boundary_claims(records, entries, b.DELEGATED)
    after_resolved, after_residual = b._account_boundary_calls(records, after_claims, b.NOT_AN_ENTRY)
finally:
    case.doCleanups()
assert {entry for entry in entries if before_owners[entry] != after_owners[entry]} == set(added)
assert all(before_owners[entry] == (None, None) for entry in added)
assert after_expected - before_expected == set(labels.items())
assert after_declared - before_declared == set(labels.items())
assert not before_expected - after_expected
assert not before_declared - after_declared
assert before_residual == after_residual
assert before_resolved == after_resolved
assert before_expected - before_declared == after_expected - after_declared
assert before_declared - before_expected == after_declared - after_expected
module = lambda values: sorted(entry for entry in values if entry[1].startswith("review_cycles.py:"))
missing = lambda pairs: sorted(pair for pair in pairs if pair[0][1].startswith("review_cycles.py:"))
report.update(entries=len(entries), occurrences=len(records), changed_owners=sorted(added), added_pairs=sorted(labels.items()), module_unowned_before=module(entry for entry in entries if before_owners[entry][0] is None), module_unowned_after=module(entry for entry in entries if after_owners[entry][0] is None), module_expected_before=len(missing(before_expected)), module_expected_after=len(missing(after_expected)), module_declared_before=len(missing(before_declared)), module_declared_after=len(missing(after_declared)), module_missing_unchanged=missing(after_expected - after_declared), module_orphan_unchanged=missing(after_declared - after_expected), residual_occurrences_unchanged=len(after_residual), all_other_owners_pairs_and_resolutions_unchanged=True, seconds=time.monotonic() - start)
for name, sha in runtime_hashes.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
report["combined_seconds"] = report["seconds"] + initial["seconds"]
assert report["combined_seconds"] < 15
with (evidence / "final-verification-121055.json").open("x") as output:
    json.dump(report, output, indent=2)
print(json.dumps(report, indent=2))
