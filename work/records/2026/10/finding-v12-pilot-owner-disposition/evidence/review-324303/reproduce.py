"""Disposable supported-command probes; no production authority or runtime."""
import json
from pathlib import Path
from tests.tools.test_disposition_command import Fixture, WORK, COMMIT

results = {}
f = Fixture()
f.setUp()
try:
    f.delivered()
    other = "work/records/2026/10/finding-pilot/OTHER.json"
    changed_commit = "a" * 40
    f.write_record(f.record_document(commit=changed_commit), reference=other)
    code, out, err = f.integrated(reference=other, **{
        "--commit": changed_commit, "--evidence-operation-id": "op-cite-other"})
    results["changed_integration_retry"] = {
        "exit": code, "answer": json.loads(out) if out else None,
        "stderr": err, "original_commit": COMMIT,
        "citation_count": len(f.citations())}
finally:
    f.doCleanups()

f = Fixture()
f.setUp()
try:
    f.delivered()
    code, out, err = f.close()
    assert code == 0, err
    pending_code, pending_out, pending_err = f.run_verb(
        "pending", *f.base(), "--work", WORK)
    results["closed_readback"] = {
        "close_acceptance": json.loads(out)["acceptance"],
        "pending_exit": pending_code, "pending": json.loads(pending_out)}
    f.write_record(f.record_document(notes="changed after successful close"))
    again, out, err = f.close()
    results["exact_close_retry_after_evidence_change"] = {
        "exit": again, "stdout": out, "stderr": err,
        "stored_status": f.work_now()["status"]}
finally:
    f.doCleanups()

print(json.dumps(results, indent=2, sort_keys=True))
