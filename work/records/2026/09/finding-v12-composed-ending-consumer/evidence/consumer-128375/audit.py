import ast
import difflib
import hashlib
import json
from pathlib import Path
import stat

here = Path(__file__).resolve().parent
repo = next(parent for parent in here.parents if (parent / "v12/python/src").is_dir())
base = json.loads((here / "base.json").read_text())
allowed = {"v12/python/tools/stage_execution.py", "v12/python/tests/tools/test_stage_execution.py"}
rows = []
for entry in base:
    path = repo / entry["path"]
    payload = path.read_bytes()
    row = {"path": entry["path"], "sha256": hashlib.sha256(payload).hexdigest(), "mode": oct(stat.S_IMODE(path.stat().st_mode))}
    assert not path.is_symlink() and int(row["mode"], 8) == int(entry["mode"].replace("0o", ""), 8), row
    row["changed"] = row["sha256"] != entry["sha256"]
    if entry["path"] not in allowed:
        assert not row["changed"], row
    else:
        original = (here / path.name).read_text()
        current = payload.decode()
        ast.parse(current)
        retained = here / "candidate" / path.name
        retained.parent.mkdir(exist_ok=True)
        retained.write_bytes(payload)
        (here / (path.name + ".patch")).write_text("".join(difflib.unified_diff(original.splitlines(True), current.splitlines(True), fromfile=entry["path"], tofile=entry["path"])))
        if path.name == "test_stage_execution.py":
            start = current.index("    READONLY_PROCESS = r'''")
            end = current.index("\n\nclass TheWrongRouteClaimDefersInsteadOfStoppingTheSweep", start)
            assert current[:start - 1] + current[end:] == original
    rows.append(row)
used = 8.87630141095724 + sum(run["elapsed_seconds"] for run in json.loads((here / "verification.json").read_text()))
result = {"files": rows, "all_existing_test_bytes_unchanged": True,
          "prior_claim_seconds": 8.87630141095724, "cumulative_seconds": used, "remaining_seconds": 20 - used}
(here / "final.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"changed": [row for row in rows if row["changed"]], "cumulative_seconds": used, "remaining_seconds": 20 - used}, indent=2))
