"""Final scanner handoff identity audit; 10s budget, no test execution."""
import hashlib
import json
from pathlib import Path
import signal
import time

signal.alarm(10)
start = time.monotonic()
root = Path.cwd()
here = Path(__file__).resolve().parent
audit = json.loads((here / "final-116824/audit.json").read_text())
for name, expected in audit["hashes"].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
joined = here.parent / "findings/finding-member-label-context/evidence"
prior = json.loads((joined / "review-116801.json").read_text())
census = json.loads((joined / "joined-116776/census.json").read_text())
assert audit["census_entries"] == prior["entries"] == census["entry_count"] == 1365
assert audit["unowned_rows"] == prior["unowned"] == len(census["unowned"]) == 183
assert audit["orphan_rows"] == prior["orphans"] == len(census["orphans"]) == 72
assert audit["symbolic_provider_rows"] == prior["symbolic_provider_orphans"]
assert audit["separate_worker_entry_rows"] == prior["worker_entry_orphan"]
assert prior["combined_passing_tests"] == 62 and len(prior["failures"]) == 2
result = {"work": "W116031", "claim": 116837, "all_final_manifest_hashes_match": True, "prior_independent_census_matches": True, "candidate_sha256": audit["hashes"]["v12/python/tests/manager/test_boundary_inventory.py"], "entries": 1365, "unowned": 183, "orphans": 72, "new_test_execution": False, "elapsed_seconds": time.monotonic() - start}
(here / "review-116837.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
