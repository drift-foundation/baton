"""Independent closed-export and publication-diagnostic probes; offline only."""
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time
from unittest import mock
R = Path(__file__).resolve().parent
sys.path.insert(0, str(R / "evidence"))
import test_qualification as t
c, w = t.c, t.worker
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
e = json.loads((R / "EVIDENCE-183197.json").read_text())
checks = []
for row in e["files"]:
    for p, expected in ((R / row["path"], row["candidate_sha256"]), (R / row["retained_copy"], row["candidate_sha256"]), (R / "candidate-183114" / Path(row["path"]).name, row["base_sha256"])):
        checks.append({"path": str(p.relative_to(R)), "sha256": sha(p), "matches": sha(p) == expected})
    assert oct(stat.S_IMODE((R / row["path"]).stat().st_mode)) == row["mode"]
assert all(x["matches"] for x in checks)
assert sha(R / "operator-result-183114/qualification.json") == e["triggering_result"]["sha256"]
assert sha(R / e["cycle"]) == e["cycle_sha256"]
started = time.monotonic()
results = []
canary = "PRIVATE-CANARY"
for field, value in (("type", canary), ("subtype", canary), ("is_error", canary), ("session_matches", canary), ("unknown_member_hashes", [canary]), ("api_error_status", canary)):
    for failed in (False, True):
        case = t.Controller()
        case.setUp()
        try:
            fake, result = case.execute(bad_state=failed, forged_terminal={field: value})
            row = {"case": "terminal-field", "field": field, "publication_failed": failed, "outcome": result["outcome"], "failure_code": result.get("failure_code"), "canary_exported": canary in json.dumps(result), "containers": len(fake.containers), "arms": len(result["arms"])}
            assert result["outcome"] == "failed" and len(fake.containers) == 1
            assert row["canary_exported"] == failed, row
            results.append(row)
        finally:
            assert case.doCleanups()

for number, expected in ((errno.EACCES, "EACCES"), (errno.EIO, "EIO"), (errno.ENOENT, "ENOENT")):
    case = t.TheCollectionCustodyCorrection()
    case.setUp()
    try:
        before = case.modes()
        with mock.patch.object(os, "fstat", side_effect=OSError(number, canary)):
            record = case.run_main()
        row = {"case": "target-fstat-" + expected, "record": record, "canary_exported": canary in json.dumps(record), "modes_unchanged": case.modes() == before}
        assert record["outcome"] == "failed" and record["failure_code"] == "unclassified"
        assert record["publication"] is None and record["observed"] is not None
        assert row["modes_unchanged"] and not row["canary_exported"]
        results.append(row)
    finally:
        assert case.doCleanups()

for field in ("check", "errno"):
    value = {"check": "listing", "errno": "EACCES"}
    value[field] = [canary]
    try:
        verdict = c.valid_publication(value)
        row = {"case": "malformed-publication-" + field, "verdict": verdict}
    except Exception as error:
        row = {"case": "malformed-publication-" + field, "raised": type(error).__name__}
    results.append(row)

seconds = time.monotonic() - started
assert all(sha(R / row["path"]) == row["candidate_sha256"] for row in e["files"])
record = {"claim": 183243, "manifest": e["manifest_sha256"], "checks": checks, "current_modes_match": 7, "trigger_and_scope_hashes_match": True, "results": results, "seconds": seconds, "source_unchanged": True, "python": sys.version, "scope": "synthetic same-UID controller and actual worker.main; provider/engine fake; no subprocesses or live/private roots; helper temporary trees cleaned"}
with (R / "review-probes-183243.json").open("x") as out:
    json.dump(record, out, indent=2)
    out.write(chr(10))
print(json.dumps({"seconds": seconds, "results": results}, indent=2))
