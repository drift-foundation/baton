"""Offline bootstrap acceptance-boundary review; only disposable v12 stores."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[5]
DIST = REPO / "v12/python"
sys.path[:0] = [str(DIST), str(DIST / "src")]
from tests.tools.test_bootstrap import Fixture
from tools import bootstrap, stage_execution

started = time.monotonic()
dossier = Path(__file__).parent
expected = json.loads((dossier / "EVIDENCE-185774.json").read_text())["candidates"]
hashes = {path: hashlib.sha256((REPO / path).read_bytes()).hexdigest()
          for path in expected}
assert hashes == expected
evidence = {"claim": 185857, "candidate_hashes": hashes,
            "all_author_hashes_match": True}
# One existing author case owns this fixed scratch name. Refuse to run it if
# somebody already has material there, because its cleanup is unconditional.
assert not (DIST / "would-be-deployment").exists()
test_started = time.monotonic()
tests = subprocess.run([sys.executable, "-m", "unittest", "-v",
                        "tests.tools.test_environment", "tests.tools.test_bootstrap"],
                       cwd=DIST, capture_output=True, text=True, timeout=120)
evidence["tests"] = {"returncode": tests.returncode,
                     "seconds": time.monotonic() - test_started,
                     "stdout": tests.stdout, "stderr": tests.stderr}

case = Fixture()
case.setUp()
try:
    document = case.document()
    answer = bootstrap.prepare(document, stream=io.StringIO())
    try:
        stage_execution.held_configuration(answer["configuration"])
    except Exception as failure:
        evidence["bootstrap_accepts_incomplete_workers"] = {
            "bootstrap_returned_success": True,
            "authority_created": Path(answer["places"]["authority_store"]).exists(),
            "configuration_created": Path(answer["places"]["configuration"]).exists(),
            "deployment_validator_refusal": str(failure)}
    else:
        raise AssertionError("the incomplete author fixture unexpectedly validated")
    unknown = copy.deepcopy(document)
    unknown["integration_preparation"] = True
    evidence["silently_dropped_selection"] = {
        "input_integration_preparation": True,
        "output_present": "integration_preparation" in bootstrap.configuration(bootstrap.held(unknown))}
    assert not evidence["silently_dropped_selection"]["output_present"]
    output = Path(answer["places"]["configuration"])
    output.write_text("{ corrupted existing document")
    bootstrap.prepare(document, stream=io.StringIO())
    evidence["unreadable_existing_document"] = {
        "prepare_returned_success": True,
        "original_bytes_preserved": output.read_text() == "{ corrupted existing document"}
finally:
    case.doCleanups()

case = Fixture()
case.setUp()
try:
    multi = case.document(**case.several())
    first = bootstrap.prepare(multi, stream=io.StringIO())
    changed = case.document(jobs=[case.job(target="different-target", base="b" * 40)])
    second = bootstrap.prepare(changed, stream=io.StringIO())
    evidence["repeat_schema_transition_rebinds"] = {
        "before": bootstrap._bindings_of(first["configuration"]),
        "after": bootstrap._bindings_of(second["configuration"]),
        "prepare_returned_success": True}
finally:
    case.doCleanups()

evidence["verification_seconds_including_cleanup"] = time.monotonic() - started
evidence["cleanup"] = "Both fixture-owned temporary roots cleaned; test subprocess completed; no provider, engine, live Job, install or v11 store operations"
(dossier / "REVIEW-EVIDENCE-185857.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({"test_returncode": tests.returncode,
                  "seconds": evidence["verification_seconds_including_cleanup"],
                  "validator_refusal": evidence["bootstrap_accepts_incomplete_workers"]["deployment_validator_refusal"],
                  "counterexamples": ["incomplete workers reported prepared", "selection silently dropped", "corrupt configuration overwritten", "schema transition rebinds and removes Jobs"]}))
