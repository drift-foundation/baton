"""Read-only W110772 baseline; run from the repository root with python3 -B."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path.cwd()
PATHS = (
    "v12/worker/claude_agent.py",
    "v12/worker/baton_worker.py",
    "v12/python/tools/stage_execution.py",
    "v12/python/tools/single_worker.py",
    "v12/python/src/baton_v12/job_manager/review_driver.py",
    "v12/python/src/baton_v12/worker_manager/review_cycles.py",
    "v12/python/src/baton_v12/worker_manager/output.py",
    "v12/python/src/baton_v12/worker_manager/manifests.py",
    "v12/python/src/baton_v12/integration/driver.py",
    "v12/python/tests/manager/test_claude_agent.py",
    "v12/python/tests/job_manager/test_review_driver.py",
)
files = {}
for name in PATHS:
    raw = (ROOT / name).read_bytes()
    files[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

# Import only the concrete worker; no store, Docker or provider is opened.
sys.path[:0] = [str(ROOT / "v12/worker"),
                str(ROOT / "v12/python/src/baton_v12")]
import claude_agent

try:
    claude_agent._one_declaration([{"name": "findings"}, {"name": "logs"}])
except claude_agent.TaskRefusal as refusal:
    two_outputs = {"refused": True, "reason": str(refusal)}
else:
    two_outputs = {"refused": False}

source = (ROOT / "v12/python/src/baton_v12/job_manager/review_driver.py").read_text()
tree = ast.parse(source)
ending = next(node for node in tree.body
              if isinstance(node, ast.FunctionDef) and node.name == "end_review")
required_keywords = [arg.arg for arg, default in
                     zip(ending.args.kwonlyargs, ending.args.kw_defaults)
                     if default is None]
report = {
    "work": "W110772", "claim_seq": 110843,
    "files": files, "review_declarations": two_outputs,
    "end_review_required_keywords": required_keywords,
    "note": "This reproduces the worker declaration refusal and inspects the existing ending signature; it does not prove the proposed provider works.",
}
assert two_outputs["refused"] and "verdict" in required_keywords
rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
if len(sys.argv) == 2:
    with open(sys.argv[1], "x", encoding="utf-8") as output:
        output.write(rendered)
print(rendered, end="")
