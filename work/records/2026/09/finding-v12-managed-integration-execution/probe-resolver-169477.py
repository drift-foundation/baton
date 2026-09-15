"""Diagnostic evidence of current resolver API mismatches, not acceptance."""
import json
from tools import stage_execution

deployment = stage_execution.StageDeployment.__new__(stage_execution.StageDeployment)
deployment.jobs = object()  # Neither defect reaches this owner's implementation.
resolver = stage_execution.PreparationResolver(deployment, participant="baton.impl-a", home="/tmp")
answers = []
for label, call, expected in (
    ("required_tests_owner", lambda: resolver.required({}, "job-a"), AttributeError),
    ("job_execution_reader_call", lambda: resolver.limits("job-a"), TypeError),
):
    try:
        call()
    except expected as error:
        answers.append({"case": label, "observed": type(error).__name__, "message": str(error)})
    else:
        raise AssertionError("Expected the recorded API mismatch: " + label)
assert hasattr(stage_execution.Integration, "required_tests")
assert not hasattr(stage_execution.StageDeployment, "required_tests")
print(json.dumps({"observations": answers, "limit": "Real production methods/classes; deliberately uninitialized deployment sufficient because both failures precede owner work. No live deployment, owner store, worker or engine proof."}, indent=2))
