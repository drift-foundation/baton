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
initial = json.loads((evidence / "verification-121130.json").read_text())
report = {"initial_seconds": initial["seconds"], "reused_initial_controls": 3}
stream = io.StringIO()


def deadline(*_):
    raise TimeoutError("15s verification budget exhausted")


def verify():
    path = Path("v12/python/tests/manager/test_boundary_inventory.py")
    base = (evidence / "base-121130.py").read_text()
    candidate = path.read_text()
    report.update(base_sha256=hashlib.sha256(base.encode()).hexdigest(), candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest())
    assert report["base_sha256"] == "912cce9a3fcd6b26c8cab3b36418ff35b0db3f2d6a91d3d6e895aef80dbb9532"
    accepted = json.loads((evidence.parents[1] / "finding-reader-identity-coverage/evidence/audit-121055.json").read_text())
    for name, sha in accepted["runtime_hashes"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    report["runtime_hashes"] = accepted["runtime_hashes"]

    site = "review_cycles.py:consumption_subject"
    envelope = ("adopted", site, "line_writers")
    member = ("adopted", site, "line_writers.writer_id")
    new_pairs = {(member, "a line writer identity"), (("caller", site, "attempt_id"), "a runtime attempt identity"), (("caller", site, "generation"), "an assignment generation")}
    initial_candidate = (evidence / "candidate-121130.py").read_text()
    corrected = initial_candidate.replace('review_cycles.consumption_subject(self.store, attempt_id="writer-attempt-1", generation=0)', 'review_cycles.consumption_subject(self.store, attempt_id="writer-attempt-1", generation=SURROGATE)')
    corrected = corrected.replace('    return fixture, line, writer\n', '    return fixture, review_cycles.line_of(fixture.store, line["line_id"]), review_cycles.writer_of(fixture.store, writer["writer_id"])\n', 1)
    assert corrected == candidate, "only the two recorded corrections differ from the initial candidate"
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

    assert candidate == (evidence / "final-candidate-121130.py").read_text()
    assert report['candidate_sha256'] == 'e92579485bc5074b26a83d953fc08f428723c84c459fc5750f20278b81b1d401'
    report['mode'] = oct(path.stat().st_mode & 0o777)
    report['scope'] = 'Exact scheduled additive nodes; previous AST and runtime hashes preserved'
    report['retained_controls_and_census_reused'] = True
    report['successful'] = True

signal.signal(signal.SIGALRM, deadline)
signal.setitimer(signal.ITIMER_REAL, 5)
try:
    verify()
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
    report['seconds'] = time.monotonic() - start
    with (evidence / 'review-121190-audit.json').open('x') as output:
        json.dump(report, output, indent=2)
    print(json.dumps(report, indent=2))
