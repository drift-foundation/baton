"""Static packet audit, no scanner projection or test execution."""
from pathlib import Path
import hashlib
import json

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
PARENT = HERE.parents[2]
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
research = json.loads((HERE / "research.json").read_text())
catalog = json.loads((PARENT / "evidence/planning-116930/catalog.json").read_text())
index = json.loads((PARENT / "evidence/planning-116930/work-index.json").read_text())
scopes = {item["module"]: item for item in index if item["type"] == "module"}
modules = sorted({row[0].split(":")[0][:-3] for kind in ("added_rows", "removed_rows") for row in research[kind]})
deltas = [{"module": module, "work": scopes[module]["id"], "dossier": scopes[module]["path"],
           "added_rows": [row for row in research["added_rows"] if row[0].split(":")[0] == module + ".py"],
           "removed_rows": [row for row in research["removed_rows"] if row[0].split(":")[0] == module + ".py"],
           "state": "proposal observation only; W117174 must revalidate after approved implementation"} for module in modules]
assert sum(len(d["added_rows"]) for d in deltas) == 18
assert sum(len(d["removed_rows"]) for d in deltas) == 13
(HERE / "module-deltas.json").write_text(json.dumps(deltas, indent=2, sort_keys=True) + "\n")
live = ROOT / "v12/python/tests/manager/test_boundary_inventory.py"
assert digest(live) == research["baseline_sha256"]
runtime = {name: digest(ROOT / name) for name in catalog["runtime_hashes"]}
assert runtime == catalog["runtime_hashes"], "runtime drift since accepted planning snapshot"
files = [HERE.parent / name for name in ("FINDING.md", "PLAN.md", "PROGRESS.md", "PROPOSAL.md")]
files += [HERE / name for name in ("inputs.json", "proposal.py", "research.py", "research.json", "controls.txt", "build_candidate.py", "candidate.py", "candidate.patch", "candidate-audit.json", "candidate-controls.txt", "candidate-verification.json", "verify_candidate.py", "module-deltas.json", "freeze.py")]
files += [PARENT / "findings/finding-declaration-accounting-implementation" / name for name in ("FINDING.md", "PLAN.md")]
audit = {"live_sha256": digest(live), "runtime_hashes_unchanged": runtime, "packet_hashes": {str(p.relative_to(ROOT)): digest(p) for p in files}, "module_delta_partition": {"added": 18, "removed": 13, "scopes": len(deltas)}, "implementation_work": "W117174", "candidate_applied": False}
(HERE / "packet-hashes.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
print(json.dumps({"manifest_sha256": digest(HERE / "packet-hashes.json"), "files": len(files), "live_sha256": audit["live_sha256"], "runtime_files_unchanged": len(runtime), "module_delta_partition": audit["module_delta_partition"]}, indent=2))
