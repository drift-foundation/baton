"""W103874: a nonempty worker claim through real sealing and manifest retention.

Uses the existing isolated sealing fixture. No Docker or live authority is
opened. Leaves the exact temporary evidence path printed below for inspection.
This is a defect reproduction, not a passing acceptance regression.
"""

import json
from pathlib import Path
import sys

repo = next(one for one in Path(__file__).resolve().parents if (one / "AGENTS.md").is_file())
sys.path[:0] = [str(repo / "v12/python/src"), str(repo / "v12/python")]

from tests.manager.test_sealing import SealingCase, NOW
from baton_v12.worker_manager.manifests import load_manifest, retain_manifest
from baton_v12.worker_manager.store import ControlStore

case = SealingCase()
case.setUp()
case.wrote({"report.txt": b"bounded output\n"})
envelope = case.published()
metadata = {"review.carrier-probe/1": {"recap": "worker-owned fact"}}
envelope["outputs"][0]["result_metadata"] = metadata
envelope = case.published(outputs=envelope["outputs"])
adapter = case.adapter(publish=False)
sealed = adapter.seal(case.request())
store = ControlStore.open(str(Path(case.root) / "control.sqlite3"), incarnation="review-carrier-probe", clock=lambda: NOW)
try:
    retained = retain_manifest(store, sealed, "resultManifest")
    loaded = load_manifest(store, retained["digest"], "resultManifest")
    replay = adapter.seal(case.request())
    report = {
        "temporary_evidence": case.root,
        "worker_metadata": metadata,
        "sealed_metadata": sealed["outputs"][0]["result_metadata"],
        "loaded_metadata": loaded["outputs"][0]["result_metadata"],
        "completion_digest_bound": sealed["completion_manifest_digest"] == envelope["manifest_digest"],
        "completion_load": load_manifest(store, sealed["completion_manifest_digest"], "completionManifest"),
        "exact_seal_replay": replay == sealed,
        "result_digest": retained["digest"],
    }
    assert report["completion_digest_bound"] and report["exact_seal_replay"]
    assert report["sealed_metadata"] == report["loaded_metadata"] == {}
    assert report["completion_load"] is None
    print(json.dumps(report, indent=2, sort_keys=True))
finally:
    store.close()
