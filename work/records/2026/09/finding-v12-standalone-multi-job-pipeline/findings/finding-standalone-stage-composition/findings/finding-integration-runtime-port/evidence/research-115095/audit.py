"""Read-only source revalidation; writes only its dossier evidence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
OCI = ROOT / "work/records/2026/09/finding-v12-integration-oci-delivery/evidence/review-112000/audit.json"
WORKER = ROOT / "work/records/2026/09/finding-v12-integration-worker-workload/evidence/review-115023/audit.json"
oci = json.loads(OCI.read_text())["candidate"]
worker = json.loads(WORKER.read_text())["paths"]
providers = {}
for path, expected in {**oci, **worker}.items():
    measured = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    providers[path] = {"sha256": measured, "accepted_sha256": expected["sha256"], "matches": measured == expected["sha256"]}
scope = ["tools/integration_worker.py", "tests/tools/test_integration_worker.py", "tools/parallel_test.py", "src/baton_v12/integration/driver.py", "src/baton_v12/integration/__init__.py", "tests/integration/test_driver.py"]
baseline = {}
for relative in scope:
    path = ROOT / "v12/python" / relative
    baseline[str(path.relative_to(ROOT))] = {"exists": path.exists(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None}
result = {"claim": 115095, "at": datetime.now(timezone.utc).isoformat(), "provider_paths": providers, "all_provider_paths_match": all(row["matches"] for row in providers.values()), "scope_baseline": baseline, "registry_note": "The shared registry uses the newer accepted W110935 hash; the older W110934 registry is historical.", "executed_tests": False}
(HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
