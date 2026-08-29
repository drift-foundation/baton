"""Record what the alleged post-create-failure case actually drives."""

import ast
import inspect
import textwrap

from tests.manager.test_negative_race_endings import NegativeEndings


source = textwrap.dedent(inspect.getsource(
    NegativeEndings.test_a_post_create_failure_converges_without_a_duplicate))
tree = ast.parse(source)
parents = {}
for node in ast.walk(tree):
    for child in ast.iter_child_nodes(node):
        parents[child] = node

contexts = []
for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    if not isinstance(node.func, ast.Name):
        continue
    if node.func.id != "request_runtime_start":
        continue
    current = node
    context = "bare"
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.With):
            context = "inside assertRaises"
            break
    contexts.append((node.lineno, context))

assert contexts == [(10, "bare"), (18, "inside assertRaises")], contexts
print("request_runtime_start calls:", contexts)
print("no post-create engine fault is injected before the successful start")
