"""Independent three-catalog identity and additive-only audit; budget5s."""
import ast
import hashlib
import json
from pathlib import Path
import signal
import time

signal.alarm(5)
start = time.monotonic()
root = Path.cwd()
here = Path(__file__).resolve().parent
final = here / "final-118934"
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = json.loads((final / "packet-hashes.json").read_text())
for path, expected in manifest.items():
    assert sha(root / path) == expected, path
report = json.loads((final / "verification.json").read_text())
new_drivers = {"tests.integration.test_driver", "tests.job_manager.test_review_driver"}
facts = {}
for path, expected in report["hashes"].items():
    live = root / path
    candidate = final / "candidate" / path
    assert sha(live) == sha(candidate) == expected
    before = here / ("proposed-runner-before.py" if path.endswith("test_parallel_runner.py") else "before/" + path)
    removed = []
    additions = {"test_work_label_exposure.py"} if path.endswith("test_catalog.py") else new_drivers
    class StripAdditions(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str) and node.value in additions:
                removed.append(node.value)
                return None
            return node
    tree = StripAdditions().visit(ast.parse(candidate.read_text()))
    assert ast.dump(tree) == ast.dump(ast.parse(before.read_text())), path
    assert len(removed) == len(additions) and set(removed) == additions
    if path.endswith("test_catalog.py"):
        assert candidate.read_text().index('"test_work_label_exposure.py"') < candidate.read_text().index('"test_work_labels.py"')
    else:
        assert removed == ["tests.integration.test_driver", "tests.job_manager.test_review_driver"]
    facts[path] = {"sha256": expected, "only_added_members": removed, "other_ast_unchanged": True}
approved = "690241cb9f51e1405c6d3246bd8a66620a95d4f8ecf561e8d5d4553dfd736406"
assert sha(here / "proposed-runner-candidate.py") == report["hashes"]["v12/python/tests/tools/test_parallel_runner.py"] == approved
log = (final / "modules.txt").read_text()
assert len([line for line in log.splitlines() if line.endswith(" ... ok")]) == 41
assert "Ran 41 tests" in log and log.rstrip().endswith("OK")
assert all(result["exit_code"] == 0 for result in report["results"])
assert report["cumulative_seconds"] < report["budget_seconds"] == 30
output = {"work": "W116014", "claim": 118966, "files": facts, "packet_hashes_match": True, "approved_third_file_matches": True, "retained_module_tests_passed": 41, "new_test_execution": False, "elapsed_seconds": time.monotonic() - start}
(here / "review-118966.json").write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps(output, indent=2))
