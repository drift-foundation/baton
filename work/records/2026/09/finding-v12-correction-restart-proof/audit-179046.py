"""Read-only source/evidence audit for packet triage; no product execution."""
import datetime
import hashlib
import json
from pathlib import Path
import stat

record = Path(__file__).resolve().parent
root = record.parents[4]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
evidence_path = record / "EVIDENCE-178810.json"
assert sha(evidence_path) == "f55243131fe03dbb35799050d08b0cabdd768d841f0246f75157cdae0e8991e3"
evidence = json.loads(evidence_path.read_bytes())
checks = []
for name, expected in evidence["files"].items():
    actual = sha(record / name)
    checks.append({"path": name, "expected": expected, "actual": actual, "match": actual == expected})
for name, expected in evidence["conflict_source_hashes"].items():
    actual = sha(root / name)
    checks.append({"path": "baton:" + name, "expected": expected, "actual": actual, "match": actual == expected})
base = json.loads((record / "BASE-178810.json").read_bytes())
for row in base["files"]:
    path = root / row["path"]
    if row["exists"]:
        match = not path.is_symlink() and stat.S_ISREG(path.stat().st_mode) and sha(path) == row["sha256"] == sha(root / row["snapshot"]) and oct(stat.S_IMODE(path.stat().st_mode)) == row["mode"]
    else:
        match = not path.exists() and not path.is_symlink()
    checks.append({"path": row["path"], "kind": "restored-base-and-mode", "match": match})
partial = json.loads((record / "partial-178810/manifest.json").read_bytes())
for row in partial["files"]:
    if "partial_path" in row:
        checks.append({"path": row["partial_path"], "kind": "retained-partial", "match": sha(root / row["partial_path"]) == row["partial_sha256"]})
for manifest_path, digest, field in (
        (record / "candidate-175150.json", evidence["accepted_A_manifest_sha256"], "sha256"),
        (root / "work/records/2026/09/finding-live-worker-log-observability/correction-178427/candidate.json", evidence["producer_manifest_sha256"], "candidate_sha256")):
    assert sha(manifest_path) == digest
    for row in json.loads(manifest_path.read_bytes())["files"]:
        path = root / row["path"].removeprefix("baton:")
        checks.append({"path": row["path"], "kind": "accepted-source", "match": sha(path) == row[field]})
receipt = {"work": "W161234", "claim": 179046, "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "activity": "static source and retained-evidence verification; no tests or product execution",
           "checks": checks, "all_match": all(row["match"] for row in checks),
           "new_runtime_verification_seconds": 0,
           "handoff_sha256": sha(record / "HANDOFF-178810.md"),
           "packet_sha256": sha(record / "EXECUTION-B-177536.md"),
           "author_run2": json.loads((record / "run-178810-2.json").read_bytes())}
with (record / "TRIAGE-179046.json").open("x") as output:
    output.write(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"all_match": receipt["all_match"], "checks": len(checks), "mismatches": [row for row in checks if not row["match"]]}))
raise SystemExit(0 if receipt["all_match"] else 1)
