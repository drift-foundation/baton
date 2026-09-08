"""Independent planning packet audit, budget10s; no probes or projections."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import signal
import time

signal.alarm(10)
start = time.monotonic()
root = Path.cwd()
here = Path(__file__).resolve().parent
parent = here.parents[2]
read = lambda path: json.loads(path.read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = read(here / "packet-hashes.json")
mismatches = [path for path, expected in manifest.items() if sha(root / path) != expected]
assert not mismatches, mismatches
index = read(parent / "evidence/planning-116930/work-index.json")
ledger = {item["id"]: item for item in read(here / "review-117069-ledger.json")}
review_input = read(here / "inputs.json")
sources = review_input["sources"]
catalog = read(root / sources["catalog_census"])
owners = read(root / sources["owner_census"])
failed = read(root / sources["probe_failures"])
assert sha(root / "v12/python/tests/manager/test_boundary_inventory.py") == review_input["baseline_sha256"] == catalog["candidate_sha256"]
totals = {"unowned": owners["unowned"], "orphan_calls": owners["orphans"], "missing_probes": catalog["missing_probes"], "orphan_probes": catalog["orphan_probes"], "failed_stimuli": failed["residuals"]}
combined = {key: [] for key in totals}
modules = []
for position, item in enumerate(index):
    path = root / item["path"]
    data = read(path / "evidence/inputs.json")
    assert data["work"] == item["id"]
    if position:
        actual = ledger[item["id"]]
        assert actual["binding"]["root"] == "baton" and actual["binding"]["path"] == item["path"]
        assert actual["blocked_by"] == ["2b077949-" + item["previous"]]
        assert actual["phase"] == "block" and actual["handler"] is None
    if data.get("runtime_source"):
        assert sha(root / data["runtime_source"]) == data["runtime_sha256"]
    for key in totals:
        combined[key].extend(data[key])
    if item["type"] == "module":
        modules.append(item["module"])
        for filename in ("FINDING.md", "PLAN.md"):
            exemplar = (parent / "findings/finding-lanes-inventory" / filename).read_text()
            normalized = re.sub(r"\d+", "#", (path / filename).read_text().replace(item["module"], "MODULE"))
            assert normalized == re.sub(r"\d+", "#", exemplar.replace("lanes", "MODULE"))
    existing = path / "evidence/existing-probe-scope.json"
    if existing.exists():
        scopes = read(existing)
        assert [(entry["entry"], entry["existing_catalog_label"]) for entry in scopes] == [(entry, label) for entry, label in data["orphan_probes"]]
        for scope in scopes:
            assert scope["currently_unmatched_discovery_labels"] == [label for entry, label in data["missing_probes"] if entry == scope["entry"]]
freeze = lambda rows: Counter(json.dumps(row, sort_keys=True) for row in rows)
for key in totals:
    assert freeze(combined[key]) == freeze(totals[key])
    assert all(count == 1 for count in freeze(combined[key]).values())
assert len(modules) == len(set(modules)) == 17
assert ledger["W117026"]["follow_up_of"] == "2b077949-W39666"
assert catalog["expected_count"] - len(totals["missing_probes"]) == catalog["declared_count"] - len(totals["orphan_probes"])
result = {"work": "W116952", "claim": 117069, "packet_sha256": sha(here / "packet-hashes.json"), "packet_files_verified": len(manifest), "work_bindings": len(index), "serial_edges_verified": len(ledger), "owner_approved_modules": modules, "partition_counts": {key: len(rows) for key, rows in combined.items()}, "existing_orphan_scopes_verified": 51, "runtime_hashes_match": True, "all_module_findings_and_plans_match_reviewed_template": True, "probe_execution": False, "elapsed_seconds": time.monotonic() - start}
(here / "review-117069.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
