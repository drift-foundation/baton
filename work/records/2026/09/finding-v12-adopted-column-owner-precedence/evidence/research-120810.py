import hashlib
import json
import time
from pathlib import Path
from tests.manager import test_boundary_inventory as b

start = time.monotonic()
evidence = Path(__file__).resolve().parent
entries = b.receiving_entries()
records = b.boundary_occurrences()
claims = b._boundary_claims(records, entries, b.DELEGATED)
resolved, residual = b._account_boundary_calls(records, claims, b.NOT_AN_ENTRY)
targets = {
    ("adopted", "review_cycles.py:checkpoint_of", "line_checkpoints.fence"): "a persisted line checkpoint",
    ("adopted", "review_cycles.py:integration_checkpoint", "integration_eligibility.verdict_id"): "persisted integration eligibility",
}
collisions = []
for entry in sorted(entries):
    if entry[0] != "adopted" or "." not in entry[2]:
        continue
    stem = b._claims(entry)
    here = [r for r in records if r.site == entry[1]]
    exact = [r for r in here if r.subject == stem or r.subject.startswith(stem + ".")]
    rows = [r for r in here if r.kind == "row" and stem.startswith(r.subject + "[")]
    if exact and rows:
        collisions.append({"entry": entry, "exact": [r._asdict() for r in sorted(exact)], "rows": [r._asdict() for r in sorted(rows)]})
before = {(entry, label) for entry in entries if entry not in b.NO_PROBE for label in b.layer_labels(entry)}
after = {pair for pair in before if pair[0] not in targets}
after.update(targets.items())
selected = [one for one in collisions if tuple(one["entry"]) in targets]
assert len(selected) == 2
for one in selected:
    assert targets[tuple(one["entry"])] in {r["label"] for r in one["rows"]}
linked = Path("work/records/2026/08/finding-v12-global-boundary-inventory-debt/findings/finding-review-cycles-inventory/evidence/census-120754.json")
prior = json.loads(linked.read_text())
declared = {(tuple(entry), label) for entry, label in prior["declared"]}
old_module = {p for p in before if p[0][1].startswith("review_cycles.py:")}
new_module = {p for p in after if p[0][1].startswith("review_cycles.py:")}
paths = [Path(b.__file__), Path("v12/python/src/baton_v12/worker_manager/review_cycles.py"), Path("v12/python/src/baton_v12/worker_manager/schema.py"), Path("v12/python/src/baton_v12/worker_manager/boundaries.py")]
report = {
    "work": "W120785", "claim": 120810,
    "hashes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    "entries": len(entries), "occurrences": len(records), "residual_occurrences": len(residual),
    "row_exact_collisions": collisions, "collision_count": len(collisions),
    "selected": selected, "removed_pairs": sorted(before - after), "added_pairs": sorted(after - before),
    "module_missing_before": sorted(old_module - declared), "module_missing_after": sorted(new_module - declared),
    "module_orphan_pairs_before": sorted(declared - old_module), "module_orphan_pairs_after": sorted(declared - new_module),
    "simulation_limits": "Only pair selection simulated; all occurrence obligations retained, no duplicate-call exemption implemented",
    "seconds": time.monotonic() - start,
}
with (evidence / "research-120810.json").open("x") as output:
    json.dump(report, output, indent=2)
print(json.dumps({k: v for k, v in report.items() if k not in ("row_exact_collisions", "selected")}, indent=2))
