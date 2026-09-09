import copy
import hashlib
import json
import time
from pathlib import Path
from unittest import mock
from tests.integration import test_driver as t

start = time.monotonic()
evidence = Path(__file__).resolve().parent
results = {}
case = t.TheCommittedPublicationSurvivesTheProcessThatMadeIt()
case.setUp()
try:
    held, recorded = case.published()
    case.reopened()
    calls = copy.deepcopy(case.publisher.calls)
    changes = case.store._connection.total_changes
    with mock.patch.object(case.publisher, "publish", side_effect=AssertionError("external publish")), mock.patch.object(case.publisher, "proposal", side_effect=AssertionError("external read")), mock.patch.object(case.publisher, "canonical_target", side_effect=AssertionError("external target")):
        answer = case.read(held)
        assert answer["published"] == recorded
        assert case.store._connection.total_changes == changes
        results["honest_local_replay"] = {"accepted": True, "no_writes_or_publisher_calls": True}
        row = case.store._connection.execute("SELECT operation_id, result FROM operations WHERE kind = ?", (t.driver.PUBLICATION_KIND,)).fetchone()
        for name, key in (("receipt_assignment_bool_generation", "assignment"), ("published_assignment_bool_generation", "published")):
            changed = json.loads(row["result"])
            assignment = changed[key] if key == "assignment" else changed[key]["assignment_ref"]
            assignment["generation"] = bool(assignment["generation"])
            with case.damaged("UPDATE operations SET result = ? WHERE operation_id = ?", (json.dumps(changed), row["operation_id"])):
                before = case.store._connection.total_changes
                try:
                    answer = case.read(held)
                    found = answer[key] if key == "assignment" else answer[key]["assignment_ref"]
                    results[name] = {"accepted": True, "generation_type": type(found["generation"]).__name__, "generation": found["generation"]}
                except t.ContractRefusal as exc:
                    results[name] = {"accepted": False, "refused": [exc.category, exc.code, exc.message]}
                assert before == case.store._connection.total_changes
    assert case.publisher.calls == calls
finally:
    case.doCleanups()

case = t.TheCommittedPublicationSurvivesTheProcessThatMadeIt()
case.setUp()
try:
    held = case.produced()
    original = case.publisher.proposal
    def bool_readback(proposal_id):
        answer = original(proposal_id)
        answer["assignment_ref"]["generation"] = bool(answer["assignment_ref"]["generation"])
        return answer
    with case.owners(), mock.patch.object(case.publisher, "proposal", side_effect=bool_readback):
        try:
            answer = t.driver.publish_candidate(case.store, case.publisher, attempt_id=case.ATTEMPT, proposal_manifest_digest=held)
            results["publish_commits_bool_readback"] = {"accepted": True, "rows": case.rows(), "generation_type": type(answer["assignment_ref"]["generation"]).__name__}
        except t.ContractRefusal as exc:
            results["publish_commits_bool_readback"] = {"accepted": False, "rows": case.rows(), "refused": [exc.category, exc.code, exc.message]}
finally:
    case.doCleanups()

assert results['honest_local_replay']['no_writes_or_publisher_calls']
for key in ('receipt_assignment_bool_generation', 'published_assignment_bool_generation', 'publish_commits_bool_readback'):
    assert results[key]['accepted'] is False, (key, results[key])
assert results['publish_commits_bool_readback']['rows'] == 0

paths = ("src/baton_v12/integration/driver.py", "src/baton_v12/integration/__init__.py", "tests/integration/test_driver.py")
hashes = {}
for name in paths:
    raw = (Path("v12/python") / name).read_bytes()
    hashes[name] = hashlib.sha256(raw).hexdigest()
    with (evidence / ("review-121144-bool-" + name.replace("/", "__"))).open("xb") as output:
        output.write(raw)
report = {"work": "W120763", "claim": 121144, "sha256": hashes, "fixture_limits": "Reuses author's actual retained manifests and publication fixture; frozen_output_of and assignment_of remain its declared stand-ins", "results": results, "seconds": time.monotonic() - start}
with (evidence / "review-121144-bool-probe.json").open("x") as output:
    json.dump(report, output, indent=2)
print(json.dumps(report, indent=2))
