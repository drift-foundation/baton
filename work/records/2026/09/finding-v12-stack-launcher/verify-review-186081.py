"""Available bootstrap checks and isolated normalized-binding comparison."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[5]
DIST = REPO / "v12/python"
sys.path[:0] = [str(DIST), str(DIST / "src")]
from tests.tools import test_bootstrap as cases
from tools import bootstrap, stage_execution

started = time.monotonic()
dossier = Path(__file__).parent
expected = json.loads((dossier / "EVIDENCE-186044.json").read_text())["candidates"]
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
evidence = {"claim": 186081, "candidate_hashes": hashes,
            "tests": {"count": result.testsRun, "successful": result.wasSuccessful(),
                      "seconds": time.monotonic() - test_start, "output": out.getvalue()},
            "not_run": {"count": len(excluded), "tests": excluded,
                        "reason": "ValidFixture requires authorized external disk-backed writable storage"}}
case = cases.Fixture()
case.setUp()
try:
    document = case.document()
    places = bootstrap.layout(document["state_root"])
    record = bootstrap.record_of(document)
    configured = bootstrap.configuration(document)
    Path(case.root).mkdir()
    Path(places["record"]).write_text(json.dumps(record))
    config_path = Path(places["configuration"])
    actual_refusals = {}
    for name, changed in (("schema", dict(configured, schema="unsupported/99")),
                          ("review_work", dict(configured, review_work_id="different-work"))):
        config_path.write_text(json.dumps(changed))
        actual_refusals[name] = bootstrap.conflicts(places, record)
        assert actual_refusals[name]
    evidence["real_validator_refusals_on_controlled_documents"] = actual_refusals

    # Isolate only the comparison after validation. These controlled normalized
    # results do not claim successful deployment validation or composition.
    config_path.write_text(json.dumps(configured))
    binding = {"job_id": None, "job_work_id": "0000000a-W1", "review_work_id": "0000000a-W1",
               "line_declared_base": "a" * 40, "canonical_target_id": "target-1",
               "source_worker_id": "impl-a"}
    comparisons = []
    for variant in ("one", "multi"):
        base = dict(binding, job_id=None if variant == "one" else "job-a")
        changes = [("unchanged", base, False)]
        for member in ("job_work_id", "line_declared_base", "canonical_target_id", "source_worker_id"):
            changes.append((member, dict(base, **{member: "changed"}), True))
        if variant == "multi":
            changes.append(("job_set", dict(base, job_id="different-job"), True))
        for name, normalized_binding, should_refuse in changes:
            normalized = {"authority_uuid": document["authority_uuid"], "job_bindings": [normalized_binding]}
            with mock.patch.object(stage_execution, "held_configuration", return_value=normalized) as validation:
                problem = bootstrap._drifted(places, record)
                validation.assert_called_once_with(configured)
            assert bool(problem) is should_refuse, (variant, name, problem)
            comparisons.append({"variant": variant, "case": name, "refused": bool(problem), "detail": problem})
    evidence["isolated_normalized_comparisons"] = comparisons
finally:
    case.doCleanups()
evidence["verification_seconds_including_cleanup"] = time.monotonic() - started
evidence["scope"] = "21 real negative tests, real schema/review-Work refusals on controlled documents, and 11 isolated normalized-result comparison checks. No full valid deployment acceptance is claimed. Scratch cleaned; no Authority mutation, processes, provider, engine, Job or install."
(dossier / "REVIEW-EVIDENCE-186081.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({"tests": result.testsRun, "successful": result.wasSuccessful(),
                  "comparison_checks": len(comparisons), "not_run": len(excluded),
                  "seconds": evidence["verification_seconds_including_cleanup"]}))
