"""Bind C2 candidate and verification receipts; reconstruct patch in owned temp."""
import datetime
import difflib
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import tempfile

D = Path(__file__).resolve().parent
ROOT = D.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def write(name, value):
    path = D / name
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")
    return record(path)


base = json.loads((D / "BASE-182279.json").read_text())
for one in base["read_only_inputs"]:
    path = ROOT / one["path"]
    assert sha(path) == one["sha256"]
    assert oct(stat.S_IMODE(path.stat().st_mode)) == one["mode"]
files, patches = [], []
for one in base["selected"]:
    before, after = ROOT / one["snapshot"], ROOT / one["path"]
    assert sha(before) == one["sha256"]
    assert after.is_file() and not after.is_symlink()
    assert oct(stat.S_IMODE(after.stat().st_mode)) == one["mode"]
    assert after.stat().st_mode & stat.S_IWUSR
    assert sha(after) != sha(before)
    target = D / "candidate-182279" / one["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(after.read_bytes())
    target.chmod(0o444)
    files.append({"path": one["path"], "base_sha256": one["sha256"], "base_snapshot": one["snapshot"], "base_mode": one["mode"], "sha256": sha(after), "snapshot": str(target.relative_to(ROOT)), "target_mode": one["mode"], "custody_mode": "0o444"})
    patches.extend(difflib.unified_diff(before.read_text().splitlines(True), after.read_text().splitlines(True), fromfile="a/" + one["path"], tofile="b/" + one["path"]))
patch = D / "candidate-182279.patch"
with patch.open("x") as stream:
    stream.write("".join(patches))
with tempfile.TemporaryDirectory(prefix="baton-c2-patch-audit-") as tmp:
    for one in files:
        path = Path(tmp) / one["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / one["base_snapshot"]).read_bytes())
    result = subprocess.run(["patch", "--batch", "--fuzz=0", "-p1", "-i", str(patch)], cwd=tmp, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert all(sha(Path(tmp) / one["path"]) == one["sha256"] for one in files)

runs = []
for number in range(1, 10):
    path = D / f"run-C-182279-{number}.json"
    receipt = json.loads(path.read_text())
    assert receipt["group_gone"] and not receipt["timeout"] and receipt["subreaper"]
    assert receipt["before"] == receipt["after"]
    if number in (6, 7, 8, 9):
        assert receipt["status"] == 0
        assert all(sha(ROOT / name) == digest for name, digest in receipt["after"].items())
    runs.append({"run": number, "receipt": record(path), "log": record(path.with_suffix(".log")), **{key: receipt[key] for key in ("selectors", "status", "seconds", "timeout", "group_gone")}})
seconds = sum(one["seconds"] for one in runs)
trace = json.loads((D / "trace-C-182279-7.json").read_text())
boundary = trace["reopen"]
first = trace["initial"]["binding"]["attempt_id"]
second = trace["revised"]["binding"]["attempt_id"]
counts = {name: {"before_old": len([one for one in boundary["before"][name] if one["attempt_id"] == first]), "after_old": len([one for one in boundary["after"][name] if one["attempt_id"] == first]), "observed_old": len([one for one in boundary["observed"][name] if one["attempt_id"] == first]), "final_old": len([one for one in trace["final_counters"][name] if one["attempt_id"] == first]), "final_new": len([one for one in trace["final_counters"][name] if one["attempt_id"] == second])} for name in ("provider", "engine")}
assert all(value == 1 for stream in counts.values() for value in stream.values())
negative = json.loads((D / "trace-C-182279-6.json").read_text())
assert len(negative["rejections"]) == 15
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
candidate = write("CANDIDATE-182279.json", {"schema": "baton.c2-candidate/1", "work": "W180252", "claim": 182279, "owner_decision": 182276, "created_at": now, "root": "baton", "files": files, "base_manifest": record(D / "BASE-182279.json"), "read_only_inputs": base["read_only_inputs"], "patch": {**record(patch), "reconstruction": "patch --batch --fuzz=0 -p1 on exact accepted C1 bases reproduces both SHA256 values"}, "custody_note": "Snapshot0444 is evidence protection only, not a checkout mode instruction. Existing owner-writable target modes unchanged. Candidate already in shared working tree; independent review pending, no import or Git mutation."})
artifacts = [record(D / name) for name in ("BASE-182279.json", "verify-182279.py", "package-182279.py", "trace-C-182279-6.json", "trace-C-182279-7.json", "trace-C-182279-8.json", "trace-C-182279-9.json")]
evidence = write("EVIDENCE-182279.json", {"schema": "baton.c2-evidence/1", "work": "W180252", "claim": 182279, "created_at": now, "candidate": candidate, "artifacts": artifacts, "runs": runs, "final_runs": {"C2_negative": 6, "C2_positive": 7, "C1_positive": 8, "C1_negative": 9}, "acceptance": {"tests": 15, "C2_negative_groups": 6, "C2_synthetic_rejections": 15, "C1_synthetic_rejections": 13, "predecessor_artifact_schedules_validated_without_execution": 18, "C2_ticks": trace["ticks"], "boundary_ticks": [boundary["before_tick"], boundary["after_tick"]], "counts": counts}, "verification_seconds": {"this_author_claim": seconds, "prior_author": 211.3880788211536, "cumulative_author": 211.3880788211536 + seconds, "prior_reviewer_separate": 104.8836736070516}, "cleanup": "All nine runs: subreaper, no timeout, positive group absence, source bytes stable. Final four runs match candidate. Runs7/8/9 ran concurrently in independent supervised process groups with separate fixture stores and logs; durations are summed, not elapsed-wall substitution.", "limit": "Manager recomposition in one process after initial runtime destroyed and result retained. Deterministic real provider child and simulated OCI; no host/power-loss exactly-once or production restoration qualification."})
print(json.dumps({"candidate": candidate, "evidence": evidence, "files": files, "author_seconds": seconds, "cumulative_author": 211.3880788211536 + seconds}, indent=2))
