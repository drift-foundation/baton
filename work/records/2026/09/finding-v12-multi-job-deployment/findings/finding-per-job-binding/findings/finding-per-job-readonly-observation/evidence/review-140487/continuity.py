"""Independent read-only candidate and retained-evidence reconciliation."""
import hashlib
import json
from pathlib import Path
import stat
import time

started = time.monotonic()
root = Path.cwd()
out = Path(__file__).resolve().parent
author_path = out.parent / "claim-140438/result.json"
author = json.loads(author_path.read_bytes())
prior_path = out.parents[2] / "finding-two-job-serving/evidence/review-140405/result.json"
prior = json.loads(prior_path.read_bytes())
errors = []
actual = {}
for name, wanted in prior["accepted_union"].items():
    path = root / name
    if wanted.get("state") == "absent":
        got = {"state": "absent" if not path.exists() and not path.is_symlink() else "present"}
    else:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            errors.append(name + ": not regular")
        data = path.read_bytes()
        got = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "mode": oct(stat.S_IMODE(info.st_mode))}
    actual[name] = got
    if got != wanted or got != author["accepted_union"].get(name):
        errors.append(name + ": drift")
for name, wanted in author["retained_evidence"].items():
    data = (root / name).read_bytes()
    if {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} != wanted:
        errors.append(name + ": retained evidence drift")
elapsed = time.monotonic() - started
result = {
    "work": "W130229", "review_claim": 140487, "accepted_candidate": 140229,
    "accepted_union": actual, "errors": errors,
    "retained_evidence": author["retained_evidence"],
    "author_manifest_sha256": hashlib.sha256(author_path.read_bytes()).hexdigest(),
    "verification_seconds": elapsed, "outer_reserve_seconds": 0.1,
    "review_charge_seconds": elapsed + 0.1,
    "review_cumulative_seconds": 4.52145815199789 + elapsed + 0.1,
    "review_cap_seconds": 5, "runtime_tests": 0, "database_opens": 0,
    "source_test_changes": [],
    "limitations": "Static continuity only; no new execution or owner/database preservation proof. All prior unmeasured activity and overruns retained; no allocation transfer."
}
(out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in ("accepted_union", "retained_evidence")}, indent=2))
assert not errors, errors
assert result["review_cumulative_seconds"] < 5
