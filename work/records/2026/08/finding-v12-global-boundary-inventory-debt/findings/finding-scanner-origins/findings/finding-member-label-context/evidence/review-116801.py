"""Independent joined-evidence identity/count audit; no tests; budget 10s."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import signal
import time

signal.alarm(10)
start = time.monotonic()
root = Path.cwd()
here = Path(__file__).resolve().parent
audit = json.loads((here / "joined-116776/audit.json").read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for path, expected in audit["hashes"].items():
    assert sha(root / path) == expected, path
provider = root / "work/records/2026/09/finding-v12-provider-label-discovery/evidence"
copy = here / "joined-116776/census.json"
assert copy.read_bytes() == (provider / "census.json").read_bytes()
assert sha(copy) == audit["copied_census_sha256"]
census = json.loads(copy.read_text())
assert census["entry_count"] == 1365
for rows, module_index, grouped, count in (("unowned", 1, "unowned_by_module", 183), ("orphans", 0, "orphan_by_module", 72)):
    assert len(census[rows]) == len(set(map(tuple, census[rows]))) == count
    assert dict(Counter(row[module_index].split(":")[0] for row in census[rows])) == census[grouped] == audit[grouped]
table = {}
for line in (here.parent / "JOINED-RESULT.md").read_text().splitlines():
    if line.startswith("| ") and ".py |" in line:
        module, unowned, orphan = (part.strip() for part in line.strip("|").split("|"))
        table[module] = (int(unowned), int(orphan))
assert table == {module: (census["unowned_by_module"].get(module, 0), census["orphan_by_module"].get(module, 0)) for module in census["unowned_by_module"].keys() | census["orphan_by_module"].keys()}
assert len(census["failures"]) == 2 and census["failures"] == audit["failures"] and not census["errors"]
lines = (provider / "verification.txt").read_text().splitlines()
passes = []
current = None
for line in lines:
    if line.startswith("test_"):
        current = line
    if current is not None and line.endswith(" ... ok"):
        passes.append(current)
        current = None
assert len(passes) == 62, len(passes)
assert any("test_the_universe_sees_every_persisted_column_that_is_read" in line for line in passes)
symbolic = [row for row in census["orphans"] if "{provider}" in row[2]]
assert symbolic == audit["symbolic_provider_orphans"] and len(symbolic) == 2
worker = [row for row in census["orphans"] if row[0].startswith("worker_entry.py:")]
assert len(worker) == 1
result = {"claim": 116801, "all_retained_hashes_match": True, "census_copy_identical": True, "report_table_matches": True, "combined_passing_tests": len(passes), "failures": census["failures"], "entries": 1365, "unowned": 183, "orphans": 72, "symbolic_provider_orphans": symbolic, "worker_entry_orphan": worker, "elapsed_seconds": time.monotonic() - start, "new_test_execution": False}
(here / "review-116801.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
