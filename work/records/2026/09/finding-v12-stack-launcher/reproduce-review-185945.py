"""Focused review within /tmp; no disk-backed success fixture or live stack."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest

REPO = Path(__file__).resolve().parents[5]
DIST = REPO / "v12/python"
sys.path[:0] = [str(DIST), str(DIST / "src")]
from tests.tools import test_bootstrap as cases
from tools import bootstrap, stage_execution

started = time.monotonic()
dossier = Path(__file__).parent
expected = json.loads((dossier / "EVIDENCE-185884.json").read_text())["candidates"]
hashes = {path: hashlib.sha256((REPO / path).read_bytes()).hexdigest() for path in expected}
assert hashes == expected
assert not (DIST / "would-be-deployment").exists()
suite = unittest.TestSuite()
excluded = []
for name, cls in vars(cases).items():
    if isinstance(cls, type) and cls.__module__ == cases.__name__ and issubclass(cls, unittest.TestCase):
        if issubclass(cls, cases.ValidFixture):
            excluded.extend(unittest.defaultTestLoader.getTestCaseNames(cls))
        elif cls is not cases.Fixture:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
output = io.StringIO()
test_start = time.monotonic()
result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
evidence = {"claim": 185945, "candidate_hashes": hashes,
            "tests": {"count": result.testsRun, "successful": result.wasSuccessful(),
                      "seconds": time.monotonic() - test_start, "output": output.getvalue()},
            "not_run": {"count": len(excluded), "tests": excluded,
                        "reason": "ValidFixture requires disk-backed writable root outside checkout; /tmp is tmpfs and /var/tmp is outside managed write authority"}}
case = cases.Fixture()
case.setUp()
try:
    document = case.document()
    places = bootstrap.layout(document["state_root"])
    record = bootstrap.record_of(document)
    Path(case.root).mkdir()
    Path(places["record"]).write_text(json.dumps(record))
    Path(places["configuration"]).write_text("{ broken deployment JSON")
    evidence["corrupt_emitted_document"] = {
        "conflicts": bootstrap.conflicts(places, record),
        "record_is_complete": True}
    incomplete = copy.deepcopy(record)
    incomplete["bindings"]["job-a"] = {}
    Path(places["record"]).write_text(json.dumps(incomplete))
    changed = copy.deepcopy(document)
    changed["jobs"][0]["canonical_target_id"] = "different-target"
    changed["jobs"][0]["line_declared_base"] = "b" * 40
    evidence["incomplete_record_permits_rebind"] = {
        "record": incomplete,
        "requested": bootstrap.record_of(changed),
        "conflicts": bootstrap.conflicts(places, bootstrap.record_of(changed))}
    null_selection = dict(document, integration_preparation=None)
    configured = bootstrap.configuration(bootstrap.held(null_selection))
    null_result = {"input": None, "output_present": "integration_preparation" in configured,
                   "output_preparation": stage_execution._prepares(configured)}
    try:
        stage_execution._prepares({"integration_preparation": None})
    except Exception as failure:
        null_result["accepted_validator_on_original_value"] = str(failure)
    evidence["null_selection_is_dropped"] = null_result
    true_configuration = bootstrap.configuration(bootstrap.held(dict(document, integration_preparation=True)))
    evidence["true_selection_preserved"] = true_configuration["integration_preparation"] is True
    assert evidence["corrupt_emitted_document"]["conflicts"] == []
    assert evidence["incomplete_record_permits_rebind"]["conflicts"] == []
    assert not null_result["output_present"] and null_result["output_preparation"] is False
finally:
    case.doCleanups()
evidence["verification_seconds_including_cleanup"] = time.monotonic() - started
evidence["scope"] = "Real bootstrap conflict/input helpers over controlled /tmp documents; no claimed end-to-end repeat, Authority mutation, provider, engine, Job, install or production deployment"
(dossier / "REVIEW-EVIDENCE-185945.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({"tests": evidence["tests"]["count"], "successful": result.wasSuccessful(),
                  "not_run": len(excluded), "seconds": evidence["verification_seconds_including_cleanup"],
                  "observations": ["incomplete record permits changed binding", "emitted corruption ignored", "null selection silently defaults false"]}))
