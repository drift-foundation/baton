"""Retain reviewer inputs and verify existing test assertions are preserved."""
import ast
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
DOSSIER = HERE.parents[1]
BASE = REPO / "work/records/2026/09/finding-v11-codex-copilot-notifier/evidence/review-110517/candidate"
manifest = json.loads((DOSSIER / "evidence/candidate-manifest.json").read_text())
audit = {"claim": 114371, "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "paths": {}}
for name, record in manifest.items():
    current = (REPO / name).read_bytes()
    supplied = (DOSSIER / "evidence/candidate" / name).read_bytes()
    baseline = (BASE / name).read_bytes()
    sha = hashlib.sha256(current).hexdigest()
    target = HERE / "candidate" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(current)
    audit["paths"][name] = {"sha256": sha, "matches_manifest": sha == record["sha256"],
                           "matches_snapshot": current == supplied,
                           "baseline_matches": hashlib.sha256(baseline).hexdigest() == record["baseline_sha256"]}
    if name.endswith("test_codex_copilot_notifier.py"):
        def methods(data):
            return {(node.name, item.name): ast.dump(item, include_attributes=False)
                    for node in ast.parse(data).body if isinstance(node, ast.ClassDef)
                    for item in node.body if isinstance(item, ast.FunctionDef) and item.name.startswith("test_")}
        before, after = methods(baseline), methods(current)
        audit["tests"] = {"prior_count": len(before), "added_count": len(after.keys() - before.keys()),
                          "all_prior_AST_identical": all(after.get(key) == value for key, value in before.items())}
audit["canonical_source_hashes"] = {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in
    ("src/baton_work/projection.py", "src/baton_work/transitions.py", "tools/codex-event-bridge/src/event_bridge.mjs")}
(HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps(audit, indent=2))
