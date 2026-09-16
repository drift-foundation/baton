"""Bind independent C1 results and reconstruct the selected candidate patch."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time

here = Path(__file__).resolve().parent
root = here.parents[4]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

candidate = json.loads((here / "CANDIDATE-180423.json").read_bytes())
started = time.monotonic()
with tempfile.TemporaryDirectory(prefix="baton-c1-review-180553-") as temporary:
    destination = Path(temporary)
    for row in candidate["files"]:
        path = destination / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((root / row["base_snapshot"]).read_bytes())
    answer = subprocess.run(["patch", "--batch", "--fuzz=0", "-p1", "-i", str(root / candidate["patch"]["path"])], cwd=destination, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
    assert answer.returncode == 0, answer.stdout
    reconstructed = {row["path"]: sha(destination / row["path"]) == row["sha256"] for row in candidate["files"]}
    assert all(reconstructed.values())
reconstruction_seconds = time.monotonic() - started
positive = json.loads((here / "review-trace-180553-positive.json").read_bytes())
negative = json.loads((here / "review-trace-180553-negative.json").read_bytes())
runs = [json.loads((here / ("review-run-180553-" + name + ".json")).read_bytes()) for name in ("positive", "negative", "focused")]
assert all(row["status"] == 0 and row["group_gone"] and not row["timeout"] and row["before"] == row["after"] for row in runs)
initial, revised = positive["initial"], positive["revised"]
assert initial["settlement"]["attempt_id"] != revised["settlement"]["attempt_id"]
assert initial["content"]["scale.py"]["text"] == "def scale(value):\n    return value * 2\n"
assert revised["content"]["scale.py"]["text"] == "def scale(value):\n    return value * 3\n"
assert positive["target"]["code_digest"] == revised["content"]["scale.py"]["digest"]
assert len(negative["rejections"]) == 13
seconds = sum(row["seconds"] for row in runs)
names = ["CANDIDATE-180423.json", "EVIDENCE-180423.json", "review-run-180553.py", "review-audit-180553.py", "review-trace-180553-positive.json", "review-trace-180553-negative.json"]
names += ["review-run-180553-" + name + suffix for name in ("positive", "negative", "focused") for suffix in (".json", ".log")]
summary = {
    "claim": 180553,
    "candidate_sha256": sha(here / "CANDIDATE-180423.json"),
    "provenance_checks_per_run": len(runs[0]["checks"]),
    "reconstruction": {"all_match": all(reconstructed.values()), "paths": reconstructed, "seconds": reconstruction_seconds, "output": answer.stdout, "temporary_directory_cleaned": not destination.exists()},
    "runs": [{key: row[key] for key in ("selector_group", "command", "status", "seconds", "timeout", "group_gone", "signals")} for row in runs],
    "new_reviewer_test_seconds": seconds,
    "cumulative_reviewer_test_seconds": 93.48170357503113 + seconds,
    "author_cumulative_seconds_separate": 211.3880788211536,
    "positive": {"ticks": positive["ticks"], "different_attempts": True, "initial_code_digest": initial["content"]["scale.py"]["digest"], "revised_code_digest": revised["content"]["scale.py"]["digest"], "verifier_results": positive["verifications"], "first_verdict": positive["verdict"]["disposition"], "revised_verdict": positive["accepted_verdict"]["disposition"], "managed_state": positive["managed"]["state"], "target_revision": positive["target"]["revision"], "target_receipt_candidate": positive["target"]["receipt"]["candidate_digest"], "final_state": positive["final"]["state"], "capacity_root": positive["capacity"]["root"]["lifecycle"], "apply_receipt_path_exists": positive["apply"]["receipt_path_exists"]},
    "negative_cases": [row["case"] for row in negative["rejections"]],
    "artifacts": {name: sha(here / name) for name in names},
}
with (here / "REVIEW-EVIDENCE-180553.json").open("x") as output:
    output.write(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
