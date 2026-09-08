"""Retain exact review inputs and reconcile existing transcripts, without tests."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
DOSSIER = HERE.parents[1]
REPO = HERE.parents[6]
recorded = json.loads((DOSSIER / "evidence/implementation-113667/audit.json").read_text())
paths = {**recorded["delivered"], **recorded["extended"], **recorded["unchanged_accepted"]}
audit = {"claim": 114048, "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "sources": {}}
for name, expected in paths.items():
    data = (REPO / name).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    dest = HERE / "candidate" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    audit["sources"][name] = {"sha256": actual, "recorded": expected, "matches": actual == expected}

retained = {
    "draft-progress.md": Path("/tmp/w110935_progress.md"),
    "gate-first.txt": Path("/tmp/w110935-gate.txt"),
    "gate-final.txt": Path("/tmp/w110935-gate-final.txt"),
    "gate-dossier.txt": DOSSIER / "evidence/implementation-113667/subtree-gate.txt",
    "focused-author.txt": DOSSIER / "evidence/implementation-113667/focused.txt",
    "progress-at-review.md": DOSSIER / "PROGRESS.md",
}
audit["retained"] = {}
for name, source in retained.items():
    data = source.read_bytes()
    (HERE / name).write_bytes(data)
    content = data.decode()
    audit["retained"][name] = {"source": str(source), "sha256": hashlib.sha256(data).hexdigest(),
        "summary": re.findall(r"^(?:Ran .*|FAILED .*|OK)$", content, re.M),
        "failures": re.findall(r"^(?:FAIL|ERROR): .*", content, re.M)}

testpath = "v12/python/tests/manager/test_integration_worker.py"
before = (DOSSIER / "evidence/review-113415/candidate" / testpath).read_text()
after = (REPO / testpath).read_text()
def methods(source):
    return {(node.name, child.name): ast.get_source_segment(source, child)
            for node in ast.parse(source).body if isinstance(node, ast.ClassDef)
            for child in node.body if isinstance(child, ast.FunctionDef)}
old, new = methods(before), methods(after)
audit["preserved_prior_worker_methods"] = all(new.get(key) == value for key, value in old.items())
audit["prior_worker_method_count"] = len(old)
audit["new_test_method_count"] = sum(key[1].startswith("test_") for key in new)
registry = "v12/python/tools/parallel_test.py"
reg_old = (DOSSIER / "evidence/review-113415/candidate" / registry).read_text()
reg_new = (REPO / registry).read_text()
import difflib
(HERE / "registry-diff.txt").write_text("".join(difflib.unified_diff(reg_old.splitlines(True), reg_new.splitlines(True))))
(HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps({"source_matches": {key: value["matches"] for key, value in audit["sources"].items()},
                  "preserved_prior_worker_methods": audit["preserved_prior_worker_methods"],
                  "summaries": {key: value["summary"] for key, value in audit["retained"].items()}}, indent=2))
