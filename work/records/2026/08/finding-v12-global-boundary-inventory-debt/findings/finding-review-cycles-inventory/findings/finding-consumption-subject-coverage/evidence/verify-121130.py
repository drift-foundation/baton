import ast
import copy
import difflib
import hashlib
import io
import json
import signal
import time
import traceback
import unittest
from pathlib import Path
from unittest.mock import patch

start = time.monotonic()
evidence = Path(__file__).resolve().parent
report = {}
stream = io.StringIO()


def deadline(*_):
    raise TimeoutError("15s verification budget exhausted")


def verify():
    from tests.manager import test_boundary_inventory as b
    path = Path(b.__file__)
    base = (evidence / "base-121130.py").read_text()
    candidate = path.read_text()
    report.update(base_sha256=hashlib.sha256(base.encode()).hexdigest(), candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest())
    assert report["base_sha256"] == "912cce9a3fcd6b26c8cab3b36418ff35b0db3f2d6a91d3d6e895aef80dbb9532"
    (evidence / "candidate-121130.py").write_text(candidate)
    (evidence / "candidate-121130.patch").write_text("".join(difflib.unified_diff(base.splitlines(True), candidate.splitlines(True), fromfile="a/v12/python/tests/manager/test_boundary_inventory.py", tofile="b/v12/python/tests/manager/test_boundary_inventory.py")))
    accepted = json.loads((evidence.parents[1] / "finding-reader-identity-coverage/evidence/audit-121055.json").read_text())
    for name, sha in accepted["runtime_hashes"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    report["runtime_hashes"] = accepted["runtime_hashes"]

    site = "review_cycles.py:consumption_subject"
    envelope = ("adopted", site, "line_writers")
    member = ("adopted", site, "line_writers.writer_id")
    new_pairs = {(member, "a line writer identity"), (("caller", site, "attempt_id"), "a runtime attempt identity"), (("caller", site, "generation"), "an assignment generation")}
    old = ast.parse(base)
    new = ast.parse(candidate)
    stripped = copy.deepcopy(new)
    named = lambda tree, name: next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name)
    mapping = lambda tree, name: next(node.value for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets))
    for name, key in (("STATED_OWNERS", envelope), ("DELEGATED", member)):
        target = mapping(stripped, name)
        assert ast.literal_eval(target.keys[0]) == key
        del target.keys[0]
        del target.values[0]
    probe_class = named(stripped, "EveryProbeProvesItArrived")
    probe_class.body.remove(named(probe_class, "spoiling_consumption_writer"))
    direct = mapping(named(probe_class, "review_cycle_probes"), "direct")
    expected_keys = ['(at("consumption_subject", "attempt_id"), "a runtime attempt identity")', '(at("consumption_subject", "generation"), "an assignment generation")', '(("adopted", "review_cycles.py:consumption_subject", "line_writers.writer_id"), "a line writer identity")']
    assert [ast.dump(key) for key in direct.keys[:3]] == [ast.dump(ast.parse(text, mode="eval").body) for text in expected_keys]
    del direct.keys[:3]
    del direct.values[:3]
    witness = next(node for node in stripped.body if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Subscript) and isinstance(node.targets[0].value, ast.Name) and node.targets[0].value.id == "WITNESSES" and ast.literal_eval(node.targets[0].slice) == envelope)
    assert ast.literal_eval(witness.value) == "test_consumption_requires_one_live_writer_before_delegating"
    stripped.body.remove(witness)
    stated = named(stripped, "StatedRules")
    stated.body.remove(named(stated, "test_consumption_requires_one_live_writer_before_delegating"))
    for name in ("_consumption_fixture", "ConsumptionEntriesReachTheirOwners"):
        stripped.body.remove(named(stripped, name))
    assert ast.dump(stripped) == ast.dump(old), "change outside exact additive scope"
    report["all_existing_ast_preserved"] = True

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(b.ConsumptionEntriesReachTheirOwners)
    suite.addTest(b.StatedRules("test_consumption_requires_one_live_writer_before_delegating"))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report["focused"] = {"tests": result.testsRun, "successful": result.wasSuccessful()}
    assert result.wasSuccessful(), "new focused controls failed"

    entries = b.receiving_entries()
    records = b.boundary_occurrences()
    old_delegated = {entry: value for entry, value in b.DELEGATED.items() if entry != member}
    old_stated = {entry: value for entry, value in b.STATED_OWNERS.items() if entry != envelope}
    old_witnesses = {entry: value for entry, value in b.WITNESSES.items() if entry != envelope}
    assert set(b.STATED_OWNERS) == set(b.WITNESSES)
    old_method = named(named(old, "EveryProbeProvesItArrived"), "review_cycle_probes")
    namespace = dict(vars(b))
    exec(compile(ast.Module(body=[old_method], type_ignores=[]), "<accepted-consumption-catalog>", "exec"), namespace)
    case = b.EveryProbeProvesItArrived()
    case.setUp()
    owner = b.EveryReceivingEntryHasOneOwner()
    try:
        with patch.object(b, "DELEGATED", old_delegated), patch.object(b, "STATED_OWNERS", old_stated), patch.object(b, "WITNESSES", old_witnesses), patch.object(b.EveryProbeProvesItArrived, "review_cycle_probes", namespace["review_cycle_probes"]):
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
    assert {entry for entry in entries if before_owners[entry] != after_owners[entry]} == {envelope, member}
    assert before_owners[envelope] == before_owners[member] == (None, None)
    assert after_expected - before_expected == {(member, "a line writer identity")}
    assert not before_expected - after_expected
    assert after_declared - before_declared == new_pairs
    assert not before_declared - after_declared
    assert before_residual == after_residual
    assert before_resolved == after_resolved
    assert before_declared - before_expected == after_declared - after_expected
    assert (before_expected - before_declared) - (after_expected - after_declared) == new_pairs - {(member, "a line writer identity")}
    module = lambda values: sorted(entry for entry in values if entry[1].startswith("review_cycles.py:"))
    pairs = lambda values: sorted(pair for pair in values if pair[0][1].startswith("review_cycles.py:"))
    report.update(entries=len(entries), occurrences=len(records), changed_owners=sorted((envelope, member)), added_declared_pairs=sorted(new_pairs), added_expected_pairs=sorted(after_expected - before_expected), module_unowned_after=module(entry for entry in entries if after_owners[entry][0] is None), module_expected_before=len(pairs(before_expected)), module_expected_after=len(pairs(after_expected)), module_declared_before=len(pairs(before_declared)), module_declared_after=len(pairs(after_declared)), module_missing_after=pairs(after_expected - after_declared), module_orphan_after=pairs(after_declared - after_expected), residual_occurrences_unchanged=len(after_residual), all_other_owners_pairs_resolutions_unchanged=True)
    for name, sha in accepted["runtime_hashes"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    report["successful"] = True


signal.signal(signal.SIGALRM, deadline)
signal.setitimer(signal.ITIMER_REAL, 14.8)
try:
    verify()
except BaseException:
    report["error"] = traceback.format_exc()
    raise
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
    report["test_output"] = stream.getvalue()
    report["seconds"] = time.monotonic() - start
    with (evidence / "verification-121130.json").open("x") as output:
        json.dump(report, output, indent=2)
    print(json.dumps(report, indent=2))
