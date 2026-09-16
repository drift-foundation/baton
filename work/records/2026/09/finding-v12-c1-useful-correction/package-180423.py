"""Package the exact C1 candidate and audit preserved run receipts; no tests run."""
import datetime
import difflib
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[5]
D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def write(name, value):
    path = D / name
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")
    return {"path": rel(path), "sha256": sha(path)}


old = json.loads((D / "BASE-180298.json").read_text())
new = json.loads((D / "BASE-180423.json").read_text())
bases = {one["path"]: one for one in new["selected"]}
bases.update({one["path"]: one for one in old["selected"]})
for one in new["read_only_inputs"]:
    assert sha(ROOT / one["path"]) == one["sha256"], one["path"]
    assert oct(stat.S_IMODE((ROOT / one["path"]).stat().st_mode)) == one["mode"]
changed = []
unchanged = []
patches = []
for name, base in sorted(bases.items()):
    before, after = ROOT / base["snapshot"], ROOT / name
    assert before.is_file() and not before.is_symlink()
    assert sha(before) == base["sha256"]
    assert after.is_file() and not after.is_symlink()
    mode = oct(stat.S_IMODE(after.stat().st_mode))
    assert mode == base["mode"] and after.stat().st_mode & stat.S_IWUSR
    if sha(after) == base["sha256"]:
        unchanged.append(base)
        continue
    snapshot = D / "candidate-180423" / name
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    with snapshot.open("xb") as stream:
        stream.write(after.read_bytes())
    snapshot.chmod(0o444)
    changed.append({"path": name, "base_sha256": base["sha256"], "base_snapshot": base["snapshot"], "base_mode": base["mode"], "sha256": sha(snapshot), "snapshot": rel(snapshot), "target_mode": mode, "custody_mode": "0o444"})
    patches.extend(difflib.unified_diff(before.read_text().splitlines(True), after.read_text().splitlines(True), fromfile="a/" + name, tofile="b/" + name))
assert len(changed) == 7
patch = D / "candidate-180423.patch"
with patch.open("x") as stream:
    stream.write("".join(patches))
with tempfile.TemporaryDirectory(prefix="baton-c1-patch-audit-") as tmp:
    for one in changed:
        path = Path(tmp) / one["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / one["base_snapshot"]).read_bytes())
    applied = subprocess.run(["patch", "--batch", "--fuzz=0", "-p1", "-i", str(patch)], cwd=tmp, capture_output=True, text=True, timeout=10)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    for one in changed:
        assert sha(Path(tmp) / one["path"]) == one["sha256"]

runs = []
for number in range(1, 12):
    path = D / f"run-C-180423-{number}.json"
    receipt = json.loads(path.read_text())
    assert not receipt["timeout"] and receipt["group_gone"] and receipt["subreaper"]
    assert receipt["before"] == receipt["after"]
    if number in (9, 10, 11):
        assert receipt["status"] == 0
        for name, digest in receipt["after"].items():
            assert sha(ROOT / name) == digest, name
    log = path.with_suffix(".log")
    runs.append({"run": number, "receipt": {"path": rel(path), "sha256": sha(path)}, "log": {"path": rel(log), "sha256": sha(log)}, "status": receipt["status"], "seconds": receipt["seconds"], "timeout": receipt["timeout"], "group_gone": receipt["group_gone"], "selectors": receipt["selectors"]})
seconds = sum(one["seconds"] for one in runs)
artifacts = []
for name in ("trace-C-180423-9.json", "trace-C-180423-10.json", "verify-180423.py", "BASE-180298.json", "BASE-180423.json", "EVIDENCE-180298.json", "review-2026-09-15T18-48-11Z.md"):
    path = D / name
    artifacts.append({"path": rel(path), "sha256": sha(path)})
trace = json.loads((D / "trace-C-180423-10.json").read_text())
negative = json.loads((D / "trace-C-180423-9.json").read_text())
assert len(negative["rejections"]) == 13 and trace["ticks"] <= 100
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
candidate = write("CANDIDATE-180423.json", {"schema": "baton.c1-candidate/1", "work": "W180245", "claim": 180423, "owner_decisions": [180294, 180421], "created_at": now, "root": "baton", "files": changed, "unchanged_selected": unchanged, "read_only_inputs": new["read_only_inputs"], "patch": {"path": rel(patch), "sha256": sha(patch), "reconstruction": "patch --batch --fuzz=0 -p1 on exact base snapshots; every resulting SHA256 matches candidate"}, "custody_note": "Snapshot mode0444 protects evidence only. Existing repository targets remain owner-writable at their recorded modes. Candidate is already in the working tree, pending independent review; no import or Git mutation performed."})
evidence = write("EVIDENCE-180423.json", {"schema": "baton.c1-evidence/1", "work": "W180245", "claim": 180423, "created_at": now, "candidate": candidate, "artifacts": artifacts, "runs": runs, "final_acceptance_runs": [9, 10, 11], "acceptance": {"useful_correction_and_unchanged_predecessor_artifact_tests": 2, "invalid_evidence_test_groups": 5, "synthetic_rejections": 13, "focused_regression_tests": 36, "predecessor_artifact_schedules_validated_without_execution": 18, "positive_scenario_ticks": trace["ticks"]}, "verification_seconds": {"this_author_claim": seconds, "prior_author": 179.28393344706274, "cumulative_author": 179.28393344706274 + seconds, "prior_reviewer_separate": 93.48170357503113}, "execution": "Deterministic provider and simulated OCI boundary; real Python worker/provider children, Git/verifiers and coordination/managed owner transitions. No live model, real OCI, C2 scenario, predecessor schedule rerun or production qualification.", "cleanup": "All eleven receipts show subreaping, no timeout and positive process-group absence. Source hashes are stable within every run; all final runs match packaged bytes."})
print(json.dumps({"candidate": candidate, "evidence": evidence, "seconds": seconds, "cumulative_author": 179.28393344706274 + seconds, "files": changed}, indent=2))
