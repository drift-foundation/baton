"""Read-only source/public-result baseline; no runtime, provider or target edits."""
import ast
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys

root = Path.cwd()
sys.path[:0] = [str(root / "v12/python/src"), str(root / "v12/python")]
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import runtime
from tests.integration.test_runtime import RuntimeCase

worker = root / "v12/worker/claude_agent.py"
tree = ast.parse(worker.read_text())
agent = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ClaudeAgent")
public_methods = [n.name for n in agent.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
assert "invoke_provider" not in public_methods
assert "work" in public_methods
consumers = []
for path in (root / "v12/worker").glob("*.py"):
    if runtime.ASSIGNMENT_SCHEMA in path.read_text():
        consumers.append(str(path.relative_to(root)))
assert not consumers
case = RuntimeCase()
case.setUp()
try:
    assignment = case.compose()
    accepted = {}
    for outcome, detail in (
        ("integrated", {"imported_paths": ["src/a.py"], "verification": {"synthetic": True}}),
        ("refused", {"reason": "scope", "detail": {"observed": "synthetic"}}),
        ("held", {"reason": "uncertain", "detail": {"observed": "synthetic"}})):
        result = case.result(assignment, outcome=outcome, detail=detail)
        accepted[outcome] = runtime.observed_result(assignment, result)
    failures = {}
    for name, values in (
        ("foreign-attempt", {"attempt_id": "foreign"}),
        ("wrong-fence", {"fence": assignment["fence"] + 1}),
        ("unsupported-outcome", {"outcome": "success"}),
        ("extra-member", {"extra": True})):
        try:
            runtime.observed_result(assignment, case.result(assignment, **values))
        except ContractRefusal as refusal:
            failures[name] = {"category": refusal.category, "code": refusal.code}
        else:
            raise AssertionError(name)
finally:
    case.doCleanups()
paths = [
    "v12/worker/claude_agent.py", "v12/worker/dogfood_entry.py",
    "v12/worker/Dockerfile.claude",
    "v12/python/src/baton_v12/integration/runtime.py",
    "v12/python/src/baton_v12/integration/execution.py",
    "v12/python/src/baton_v12/integration/admission.py",
    "v12/python/src/baton_v12/integration/driver.py",
    "v12/python/src/baton_v12/worker_manager/review_cycles.py",
    "v12/python/src/baton_v12/worker_manager/output.py",
    "v12/python/src/baton_v12/checkpoint_profiles.py",
]
report = {
    "public_provider_methods": public_methods,
    "integration_assignment_consumers": consumers,
    "accepted_generic_result_claims": accepted,
    "refusals": failures,
    "source_hashes": {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths},
    "limitations": "Public generic result adoption accepts synthetic claims without observing target bytes or a provider; that is its documented boundary, not integration proof. No engine, credential, provider, Git mutation or actual target operation.",
}
with Path(__file__).with_name("baseline.json").open("x") as out:
    json.dump(report, out, indent=2)
    out.write("\n")
print(json.dumps({k: v for k, v in report.items() if k != "accepted_generic_result_claims"}, indent=2))
