"""Read-only candidate/preservation review; run from the repository root.

Writes only exclusive evidence files beside this script. The candidate is
invoked with --audit only; no runtime/test/credential operation is requested.
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

repo = Path.cwd()
record = repo / "work/records/2026/09/finding-v12-live-session-workspace-detach"
evidence = record / "evidence"
destination = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest_path = evidence / "restore-constructor-manifest.json"
manifest = json.loads(manifest_path.read_text())
prior_path = evidence / "restore-only-manifest.json"
prior = json.loads(prior_path.read_text())
assert sha(manifest_path) == "b6058f4774775c63113f0f9721e264dd317a4f57692b2ebfdf3264511c032c4b"
assert sha(prior_path) == manifest["base_manifest_sha256"]
for path, expected in manifest["files"].items():
    target = repo / path
    assert target.is_file() and not target.is_symlink(), path
    assert sha(target) == expected, path
for path, expected in prior["files"].items():
    assert manifest["files"][path] == expected, path

old = evidence / "live_controller_restore.py"
new = evidence / "live_controller_restore_constructor.py"
expected = old.read_text().replace('MANIFEST = HERE / "restore-only-manifest.json"',
                                   'MANIFEST = HERE / "restore-constructor-manifest.json"')
expected = expected.replace('for name in ("work", "home", "cache"):\n                place = self.session_home / name',
                            'for subdirectory in ("work", "home", "cache"):\n                place = self.session_home / subdirectory')
assert new.read_text() == expected
for path in (old, new, evidence / "live_supervisor_restore.py", evidence / "test_restore_constructor.py"):
    ast.parse(path.read_text(), filename=str(path))

export = evidence / "live-partial-export-2026-09-07"
provenance = json.loads((export / "PROVENANCE.json").read_text())
for name, expected in provenance["files"].items():
    assert sha(export / name) == expected, name

answer = subprocess.run(["/usr/bin/python3", "-B", str(new), "--audit"],
                        capture_output=True, text=True, timeout=30, check=False)
with (destination / "standalone-audit.txt").open("x") as writing:
    writing.write(answer.stdout + answer.stderr)
assert answer.returncode == 0, answer.returncode
assert json.loads(answer.stdout) == {"outcome": "offline-hash-audit-passed", "files": 125}

copies = [new, evidence / "live_supervisor_restore.py", evidence / "test_restore_constructor.py", manifest_path]
for path in copies:
    with (destination / ("reviewed-" + path.name)).open("xb") as writing:
        writing.write(path.read_bytes())
result = {"claim": 110810, "work": "W106673", "manifest_sha256": sha(manifest_path),
          "inputs_matched": len(manifest["files"]), "prior_inputs_unchanged": len(prior["files"]),
          "accepted_exports_unchanged": len(provenance["files"]),
          "exact_controller_delta": "manifest basename and private-subdirectory loop variable only",
          "reviewed_files": {path.name: sha(path) for path in copies},
          "standalone_audit_exit": answer.returncode, "tests_rerun": False,
          "runtime_or_credentials_used": False}
with (destination / "input-and-preservation-audit.json").open("x") as writing:
    json.dump(result, writing, indent=2, sort_keys=True)
    writing.write("\n")
print(json.dumps(result, sort_keys=True))
