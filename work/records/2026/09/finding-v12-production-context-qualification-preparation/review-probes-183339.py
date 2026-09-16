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
e = json.loads((R / "EVIDENCE-183316.json").read_text())
checks = []
for row in e["files"]:
    for p, expected in ((R / row["path"], row["candidate_sha256"]), (R / row["retained_copy"], row["candidate_sha256"]), (R / "candidate-183267" / Path(row["path"]).name, row["base_sha256"])):
        checks.append({"path": str(p.relative_to(R)), "sha256": sha(p), "matches": sha(p) == expected})
    assert oct(stat.S_IMODE((R / row["path"]).stat().st_mode)) == row["mode"]
assert all(x["matches"] for x in checks)
assert sha(R / "operator-result-183114/qualification.json") == "008b79672a42b8d5a6c95a1cb7ce28bf91b4950846ee26dbed0d0f300da71707"
assert sha(R / "OFFLINE-CORRECTION-CYCLE-183114.md") == "54e00a9b5892b123e3703024088695b90702e70ad58bc7e13b18b9a44d2a6727"
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
            assert not row["canary_exported"] and row["arms"] == 0, row
            assert row["failure_code"] == ("worker-failure-shape" if failed else "terminal-record-values")
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
        assert record["outcome"] == "failed" and record["failure_code"] == "publish-type"
        assert record["publication"] == {"check": "target-metadata", "errno": expected} and record["observed"] is not None
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
    assert row == {"case": "malformed-publication-" + field, "verdict": False}
    results.append(row)


for field in ("check", "errno"):
    for bad in ([canary], {"private": canary}, None):
        case = t.Controller()
        case.setUp()
        try:
            diagnostic = {"check": "credential-name", "errno": "none"}
            diagnostic[field] = bad
            with mock.patch.object(c, "publication_detail", return_value=diagnostic):
                fake, result = case.execute(bad_state=True)
            assert result["failure_code"] == "worker-failure-shape"
            assert result["outcome"] == "failed" and len(fake.containers) == 1
            assert not result["arms"] and canary not in json.dumps(result)
            results.append({"case": "controller-invalid-publication", "field": field, "type": type(bad).__name__, "refused": True, "canary_absent": True})
        finally:
            assert case.doCleanups()
case = t.Controller()
case.setUp()
try:
    fake, result = case.execute(bad_state=True)
    assert result["failure_code"] == "publish-shape" and result["outcome"] == "failed"
    assert len(fake.containers) == 1 and len(result["arms"]) == 1
    preserved = result["arms"][0]["observed"]
    assert preserved["provider_exit"] == 0 and c.valid_terminal(preserved["terminal"], result["session"])
    assert "promoted" not in result
    results.append({"case": "valid-preserved-observation", "preserved": True, "arm_still_failed": True, "containers": 1, "promoted": False})
finally:
    assert case.doCleanups()


# The new shared validator should reject malformed JSON values without raising.
for field, bad in (("members", [{"private": canary}]), ("model_fields", [{"private": canary}]), ("model_diagnostic", [canary]), ("model_usage_diagnostic", {"private": canary})):
    for failed in (False, True):
        case = t.Controller()
        case.setUp()
        try:
            fake, result = case.execute(bad_state=failed, forged_terminal={field: bad})
            assert result["outcome"] == "failed" and len(fake.containers) == 1
            assert result["failure_code"] == ("worker-failure-shape" if failed else "terminal-record-values")
            assert not result["arms"] and canary not in json.dumps(result)
            results.append({"case": "shared-validator-unhashable", "field": field, "publication_failed": failed, "failure_code": result["failure_code"], "failure_detail": result.get("failure_detail"), "canary_absent": True, "arms": 0, "containers": 1})
        finally:
            assert case.doCleanups()

seconds = time.monotonic() - started
assert all(sha(R / row["path"]) == row["candidate_sha256"] for row in e["files"])
record = {"claim": 183339, "manifest": e["manifest_sha256"], "checks": checks, "current_modes_match": 7, "trigger_and_scope_hashes_match": True, "results": results, "seconds": seconds, "source_unchanged": True, "python": sys.version, "scope": "synthetic same-UID controller and actual worker.main; provider/engine fake; no subprocesses or live/private roots; helper temporary trees cleaned"}
with (R / "review-probes-183339.json").open("x") as out:
    json.dump(record, out, indent=2)
    out.write(chr(10))
print(json.dumps({"seconds": seconds, "results": results}, indent=2))
