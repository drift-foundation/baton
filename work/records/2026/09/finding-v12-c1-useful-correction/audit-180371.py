"""Static handoff/provenance audit; does not import product or run tests."""
import hashlib
import json
import stat
from pathlib import Path

repo = Path(__file__).resolve().parents[5]
root = Path(__file__).resolve().parent
evidence = json.loads((root / "EVIDENCE-180298.json").read_bytes())
base = json.loads((root / "BASE-180298.json").read_bytes())
checks = []

def check(path, digest, mode=None):
    info = path.lstat()
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    checks.append({"path": str(path.relative_to(repo)), "sha256": actual,
                   "matches": actual == digest and stat.S_ISREG(info.st_mode) and (mode is None or oct(stat.S_IMODE(info.st_mode)) == mode)})

check(root / "EVIDENCE-180298.json", "aa5cb5fd7ec48dc7a3b6393adcd793309c1f8bf3950866d160f40f4e4b02e17f")
for row in evidence["changed"]:
    check(repo / row["path"], row["sha256"], row["mode"])
    check(repo / row["snapshot"], row["sha256"])
for row in base["selected"]:
    check(repo / row["snapshot"], row["sha256"])
    if row["path"] in evidence["unchanged_selected"]:
        check(repo / row["path"], row["sha256"], row["mode"])
for row in base["read_only_inputs"]:
    check(repo / row["path"], row["sha256"], row["mode"])
for name, digest in evidence["artifacts"].items():
    check(root / name, digest)
observation = json.loads((root / "OBSERVATION-180298.json").read_bytes())["observation"]
log = (root / "run-C-180298-7.log").read_text()
parsed, _ = json.JSONDecoder().raw_decode(log.split("AssertionError: ", 1)[1])
retained = next(iter(observation["retained"].values()))
report = retained["prepared"]["preparation"]["report"]
stages = observation["integration_attempt"]["projection"]
result = {
    "claim": 180371, "checks": checks, "all_match": all(row["matches"] for row in checks),
    "observation_equals_log": observation == parsed,
    "managed_state": retained["state"], "report": report,
    "worker_traceback": observation["logs"]["apply-9.log"],
    "stage_projection": {name: {"state": row["state"], "ending": row["ending"], "exchange": row["observed"].get("exchange")} for name, row in stages.items()},
    "runs": evidence["runs"], "new_author_seconds_sum": sum(row["seconds"] for row in evidence["runs"]),
    "new_reviewer_test_seconds": 0, "prior_reviewer_test_seconds": 93.48170357503113,
    "method": "static files, hashes and parsed author logs; no test or engine rerun; no independent process-cleanup inspection",
}
print(json.dumps(result, indent=2, sort_keys=True))
