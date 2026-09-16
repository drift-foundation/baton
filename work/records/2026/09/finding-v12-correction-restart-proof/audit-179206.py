"""Static media-conflict triage; no fixture imports or product execution."""
import datetime
import hashlib
import json
from pathlib import Path
import stat

record = Path(__file__).resolve().parent
root = record.parents[4]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
checks = []

def hashed(path, expected, kind):
    actual = sha(path)
    checks.append({"path": str(path.relative_to(root)), "kind": kind, "expected": expected, "actual": actual, "match": actual == expected})

hashed(record / "EVIDENCE-179121.json", "2af899a64251373a2a7fd04385d2272ce7d6fd12d34de536b57b15c8d9274cc7", "handoff-evidence")
hashed(record / "HANDOFF-179121.md", "828a749c3c060db3b16e53b9ea24207d7d6a5f26f084575633233bf94ec80c1d", "handoff")
evidence = json.loads((record / "EVIDENCE-179121.json").read_bytes())
for name, expected in evidence["files"].items():
    hashed(record / name, expected, "retained-evidence")
for name, expected in evidence["conflict_sources"].items():
    hashed(root / name, expected, "conflict-source")
for row in json.loads((record / "BASE-179121.json").read_bytes())["files"]:
    path = root / row["path"]
    if row["exists"]:
        info = path.lstat()
        match = stat.S_ISREG(info.st_mode) and sha(path) == row["sha256"] == sha(root / row["snapshot"]) and oct(stat.S_IMODE(info.st_mode)) == row["mode"]
    else:
        match = not path.exists() and not path.is_symlink()
    checks.append({"path": row["path"], "kind": "restored-baseline-mode", "match": match})
for row in json.loads((record / "partial-179121/manifest.json").read_bytes())["files"]:
    if "partial_path" in row:
        hashed(root / row["partial_path"], row["partial_sha256"], "unreviewed-partial-snapshot")
old = json.loads((record / "EVIDENCE-178810.json").read_bytes())
for path, expected, field in (
    (record / "candidate-175150.json", old["accepted_A_manifest_sha256"], "sha256"),
    (root / "work/records/2026/09/finding-live-worker-log-observability/correction-178427/candidate.json", old["producer_manifest_sha256"], "candidate_sha256"),
):
    hashed(path, expected, "accepted-manifest")
    for row in json.loads(path.read_bytes())["files"]:
        hashed(root / row["path"].removeprefix("baton:"), row[field], "accepted-source")
runs = [json.loads((record / f"run-179121-{n}.json").read_bytes()) for n in range(1, 6)]
for run in runs:
    checks.append({"path": f"run-179121-{run['run']}.json", "kind": "retained-run-candidate-and-cleanup", "match": run["before"] == run["after"] and run["group_gone"] is True and run["timeout"] is False})
hashed(root / "v12/python/requirements.lock", evidence["requirements_lock_sha256"], "environment-reference")
hashed(root / "v12/python/pyproject.toml", evidence["pyproject_sha256"], "environment-reference")
report = {"work": "W161234", "claim": 179206, "at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "activity": "static source/evidence comparison; no tests, fixture imports, product execution or resource inspection", "checks": checks, "all_match": all(row["match"] for row in checks), "new_reviewer_runtime_seconds": 0, "prior_reviewer_seconds": evidence["prior_reviewer_seconds"], "author_new_seconds": evidence["new_author_seconds"], "author_cumulative_seconds": evidence["cumulative_author_seconds"], "author_run_seconds_sum": sum(r["seconds"] for r in runs), "author_run_statuses": [r["status"] for r in runs], "additional_read_sources": {name: sha(root / name) for name in ("v12/python/src/baton_v12/worker_manager/review_cycles.py",)}}
with (record / "TRIAGE-179206.json").open("x") as stream:
    json.dump(report, stream, indent=2)
    stream.write("\n")
print(json.dumps({"all_match": report["all_match"], "checks": len(checks), "mismatches": [r for r in checks if not r["match"]]}))
raise SystemExit(0 if report["all_match"] else 1)
