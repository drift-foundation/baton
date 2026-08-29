"""Static review of the W32385 acceptance witnesses.

This does not replace the real-daemon gate. It answers the narrower review
question: which manager acts the new module actually performs after cleanup,
and whether its negative case constructs an unrelated attempt/runtime.
"""

import ast
from pathlib import Path


SOURCE = (Path(__file__).resolve().parents[6] / "v12/python/tests/manager/"
          "test_ended_runtime_adoption.py")
tree = ast.parse(SOURCE.read_text())


def calls(node):
    names = []
    for one in ast.walk(node):
        if not isinstance(one, ast.Call):
            continue
        called = one.func
        if isinstance(called, ast.Name):
            names.append(called.id)
        elif isinstance(called, ast.Attribute):
            names.append(called.attr)
    return names


tests = {
    node.name: calls(node)
    for node in ast.walk(tree)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name.startswith("test_")
}

ending = tests["test_force_removal_and_absence_precede_provider_teardown"]
uncertain = tests[
    "test_an_observation_the_adapter_cannot_make_never_releases_the_lane"]

print("post-cleanup runtime starts:", ending.count("request_runtime_start"))
print("post-cleanup new attempts:", ending.count("record_attempt"))
print("post-cleanup new offers:", ending.count("issue_offer"))
print("uncertainty-case attempts:", uncertain.count("record_attempt"))
print("uncertainty-case runtime starts:",
      uncertain.count("request_runtime_start"))
print("test methods:", *sorted(tests), sep="\n- ")
