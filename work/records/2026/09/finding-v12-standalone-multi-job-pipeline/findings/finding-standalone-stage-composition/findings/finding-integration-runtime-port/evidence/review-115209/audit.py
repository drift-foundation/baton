"""Retain the partial candidate and its reported canonical gate; no tests."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path.cwd()
here = Path(__file__).resolve().parent
paths = {
    "v12/python/src/baton_v12/integration/driver.py": "6af1fad3a23103353268592e38de336807239161f7346d7fa1ef915cf35034a8",
    "v12/python/src/baton_v12/integration/__init__.py": "523bbdb2da06f6b170debcfe270bee9867ba55791b5f551be4bdca604ce44d9e",
    "v12/python/tests/integration/test_driver.py": "eceabf0cfa5d452d4c69ea426f28a829dbcee524d57ce5e7cd255b5d4012c420",
}
candidate = {}
for name, expected in paths.items():
    data = (root / name).read_bytes()
    destination = here / "candidate" / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    measured = hashlib.sha256(data).hexdigest()
    candidate[name] = {"sha256": measured, "matches_author": measured == expected}
gate = Path("/tmp/w110774-gate.txt").read_bytes()
(here / "gate.txt").write_bytes(gate)
provider_baseline = json.loads((here.parent.parent / "evidence/research-115095/audit.json").read_text())
providers = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() == row["sha256"] for name, row in provider_baseline["provider_paths"].items()}
result = {"claim": 115209, "at": datetime.now(timezone.utc).isoformat(), "candidate": candidate, "providers_match": providers, "port_exists": (root / "v12/python/tools/integration_worker.py").exists(), "port_test_exists": (root / "v12/python/tests/tools/test_integration_worker.py").exists(), "gate_sha256": hashlib.sha256(gate).hexdigest(), "gate_failures": [line for line in gate.decode().splitlines() if line.startswith(("FAIL:", "ERROR:"))], "tests_run_this_review": False}
(here / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
