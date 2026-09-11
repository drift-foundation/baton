"""Read retained candidate/evidence bytes; never open an authority or store."""
import hashlib
import json
from pathlib import Path
import stat
import time

started = time.monotonic()
root = Path.cwd()
out = Path(__file__).resolve().parent
serving = out.parents[2] / "finding-two-job-serving"
accepted_path = serving / "evidence/review-140405/result.json"
accepted = json.loads(accepted_path.read_text())
actual, errors = {}, []
for name, wanted in accepted["accepted_union"].items():
    path = root / name
    if wanted.get("state") == "absent":
        value = {"state": "absent" if not path.exists() and not path.is_symlink() else "present"}
    else:
        data = path.read_bytes()
        value = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "mode": oct(stat.S_IMODE(path.stat().st_mode))}
        if path.is_symlink() or not path.is_file():
            errors.append(name + ": not a regular non-symlink file")
    actual[name] = value
    if value != wanted:
        errors.append(name + ": differs from accepted serving/R union")
r = root / "work/records/2026/09/finding-v12-line-rebase-after-target-advance/findings/finding-integration-result-composition"
evidence = {}
for name in ("result.json", "independent-ab-and-binding.log", "ancestry.json", "ancestry.py"):
    path = r / "evidence/review-140320" / name
    data = path.read_bytes()
    evidence[str(path.relative_to(root))] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
elapsed = time.monotonic() - started
result = {
    "work": "W130229", "claim": 140438, "accepted_candidate": 140229,
    "accepted_union": actual, "errors": errors, "retained_evidence": evidence,
    "runtime_tests_run": 0, "databases_opened": 0,
    "source_test_changes": [], "assertion_changes": [],
    "continuity_elapsed_seconds": elapsed, "outer_reserve_seconds": 0.1,
    "observation_charge_seconds": elapsed + 0.1,
    "campaign_cumulative_charge_seconds": 383.25 + elapsed + 0.1,
    "campaign_cap_seconds": 450, "observation_cap_seconds": 20,
    "reviewer_carry_seconds": 4.52145815199789,
    "note": "Retained execution evidence only; no new A/B execution or database byte/mode assertion. Historical uncertainty and unmeasured static reads/dossier work retained. No budget transfer."
}
(out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in ("accepted_union", "retained_evidence")}, indent=2))
assert not errors, errors
assert elapsed + 0.1 < 20
