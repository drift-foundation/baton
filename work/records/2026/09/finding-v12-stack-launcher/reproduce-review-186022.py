"""Review selected bootstrap boundaries in /tmp; no live deployment."""
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
expected = json.loads((dossier / "EVIDENCE-185976.json").read_text())["candidates"]
hashes = {path: hashlib.sha256((REPO / path).read_bytes()).hexdigest() for path in expected}
assert hashes == expected
assert not (DIST / "would-be-deployment").exists()
suite, excluded = unittest.TestSuite(), []
for cls in vars(cases).values():
    if isinstance(cls, type) and cls.__module__ == cases.__name__ and issubclass(cls, unittest.TestCase):
        if issubclass(cls, cases.ValidFixture):
            excluded.extend(unittest.defaultTestLoader.getTestCaseNames(cls))
        elif cls is not cases.Fixture:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
out = io.StringIO()
test_start = time.monotonic()
result = unittest.TextTestRunner(stream=out, verbosity=2).run(suite)
evidence = {"claim": 186022, "candidate_hashes": hashes,
            "tests": {"count": result.testsRun, "successful": result.wasSuccessful(),
                      "seconds": time.monotonic() - test_start, "output": out.getvalue()},
            "not_run": {"count": len(excluded), "tests": excluded,
                        "reason": "ValidFixture requires external disk-backed writable storage outside this managed reviewer's authority"}}
case = cases.Fixture()
case.setUp()
try:
    document = case.document()
    places = bootstrap.layout(document["state_root"])
    record = bootstrap.record_of(document)
    configured = bootstrap.configuration(document)
    Path(case.root).mkdir()
    record_path, config_path = Path(places["record"]), Path(places["configuration"])
    def conflicts(old_record, old_config):
        record_path.write_text(json.dumps(old_record))
        config_path.write_text(json.dumps(old_config))
        return bootstrap.conflicts(places, record)
    incomplete = copy.deepcopy(record)
    incomplete["bindings"]["job-a"] = {}
    evidence["incomplete_record_now_refused"] = conflicts(incomplete, configured)
    record_path.write_text(json.dumps(record))
    config_path.write_text("{ broken JSON")
    evidence["corrupt_json_now_refused"] = bootstrap.conflicts(places, record)
    probes = {}
    for name, changed in (
        ("review_work", dict(configured, review_work_id="different-work")),
        ("unsupported_schema", dict(configured, schema="unsupported/99")),
    ):
        probes[name] = {"conflicts": conflicts(record, changed)}
    changed = copy.deepcopy(configured)
    changed["workers"][0]["worker_id"] = "different-producer"
    probes["sole_producer_identity"] = {"conflicts": conflicts(record, changed)}
    evidence["unrecognized_emitted_drift"] = probes
    null_config = bootstrap.configuration(bootstrap.held(dict(document, integration_preparation=None)))
    evidence["null_preserved_for_validator"] = "integration_preparation" in null_config and null_config["integration_preparation"] is None
    try:
        stage_execution._prepares(null_config)
    except Exception as failure:
        evidence["null_validator_refusal"] = str(failure)
    else:
        raise AssertionError("null was not refused")
    assert evidence["incomplete_record_now_refused"] and evidence["corrupt_json_now_refused"]
    assert all(one["conflicts"] == [] for one in probes.values())
finally:
    case.doCleanups()
evidence["verification_seconds_including_cleanup"] = time.monotonic() - started
evidence["scope"] = "Real conflict and selection helpers with controlled emitted-document stand-ins, not a full valid bootstrap or live rebind; no Authority mutation, subprocess, provider, engine, Job, install or production operation"
(dossier / "REVIEW-EVIDENCE-186022.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({"tests": result.testsRun, "successful": result.wasSuccessful(),
                  "not_run": len(excluded), "seconds": evidence["verification_seconds_including_cleanup"],
                  "remaining": list(evidence["unrecognized_emitted_drift"])}))
