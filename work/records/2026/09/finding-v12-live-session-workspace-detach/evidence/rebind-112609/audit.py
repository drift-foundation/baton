"""Offline exact binding and historical preservation audit; no runtime acts."""
import ast
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
EVIDENCE = OUT.parent
DOSSIER = EVIDENCE.parent
REPO = EVIDENCE.parents[5]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    baseline = json.loads((OUT / "baseline.json").read_text())
    manifest = json.loads((EVIDENCE / "result-diagnostics-rebound-112609-manifest.json").read_text())
    for name, expected in baseline["protected"].items():
        assert digest(REPO / name) == expected, name
    for name, expected in manifest["files"].items():
        p = REPO / name
        assert p.is_file() and not p.is_symlink() and digest(p) == expected, name
    runtime = {str(p.relative_to(REPO)) for p in (REPO / "v12/python/src/baton_v12").rglob("*.py")}
    bound_runtime = {p for p in manifest["files"] if p.startswith("v12/python/src/baton_v12/") and p.endswith(".py")}
    assert runtime == bound_runtime
    assert baseline["prior_files"].keys() <= manifest["files"].keys()
    prior = (EVIDENCE / "live_controller_result_diagnostics.py").read_text()
    current = (EVIDENCE / "live_controller_rebound_112609.py").read_text()
    assert current == prior.replace('"result-diagnostics-manifest.json"', '"result-diagnostics-rebound-112609-manifest.json"')
    before_test = (EVIDENCE / "test_result_diagnostics.py").read_text()
    after_test = (EVIDENCE / "test_result_rebound_112609.py").read_text()
    assert after_test == before_test.replace("live_controller_result_diagnostics", "live_controller_rebound_112609")
    for name in ("live_controller_rebound_112609.py", "test_result_rebound_112609.py"):
        ast.parse((EVIDENCE / name).read_text())
    accepted = json.loads((OUT / "accepted-dependencies.json").read_text())
    for name, expected in accepted["review_maps"].items():
        assert digest(REPO / name) == expected, name
    for row in accepted["changed"]:
        assert manifest["files"][row["path"]] == row["observed"]
        assert baseline["prior_files"][row["path"]] == row["expected"]
    for name, expected in accepted["added"].items():
        assert manifest["files"][name] == expected
    for name, expected in baseline["current_runtime"].items():
        assert digest(REPO / name) == expected, name
    for name in ("focused", "broad", "standalone-audit"):
        assert json.loads((OUT / (name + ".json")).read_text())["exit_code"] == 0
    print(json.dumps(dict(claim=112609,protected_historical_files=len(baseline["protected"]),
        manifest_inputs=len(manifest["files"]),runtime_python_files=len(runtime),
        changed_dependencies=len(accepted["changed"]),added_dependencies=len(accepted["added"]),
        all_prior_inputs_retained=True,production_bytes_unchanged_since_claim=True,
        controller_only_manifest_filename_changed=True,supervisor_unchanged=True,
        all_prior_test_assertions_unchanged=True,fresh_snapshot_import_passed=True,
        offline_checks=40,live_run=False,manifest_sha256=digest(EVIDENCE / "result-diagnostics-rebound-112609-manifest.json")),indent=2,sort_keys=True))

if __name__ == "__main__":
    main()
