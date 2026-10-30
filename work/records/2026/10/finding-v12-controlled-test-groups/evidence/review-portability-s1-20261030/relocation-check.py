"""Independent copy-only fixture check; no Git mutations or live engines/providers.

Run with the prepared Python: relocation-check.py REPOSITORY EVIDENCE_DIRECTORY.
Temporary copy/trace are owned disk-backed scratch; retained logs and summaries
are written to the evidence directory supplied by the caller.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

repo = Path(sys.argv[1]).resolve()
evidence = Path(sys.argv[2]).resolve()
identity = json.loads(subprocess.check_output(
    [sys.executable, "-m", "tools.source_identity", "--declared", "v12"],
    cwd=repo / "v12/python"))
paths = set(os.fsdecode(p) for p in subprocess.check_output(
    ["git", "-C", str(repo), "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "v12"]
).split(b"\0") if p)
paths.update(entry["path"] for entry in identity["consumed"])
modules = ["tests.manager." + name for name in (
    "test_proposing_fixture", "test_fixture_dispatch", "test_importing_fixture",
    "test_w197661_verifier", "test_attempt_logs", "test_claude_agent")]
manifest = []
with tempfile.TemporaryDirectory(prefix="baton-independent-portability-", dir="/var/tmp") as scratch:
    scratch = Path(scratch)
    target = scratch / "different-checkout"
    for relative in sorted(paths):
        source = repo / relative
        assert source.is_file() and not source.is_symlink(), relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        manifest.append({"path": relative, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
    (evidence / "copied-inputs.json").write_text(json.dumps(manifest, indent=1) + "\n")
    (scratch / "temporary").mkdir()
    environment = dict(os.environ, TMPDIR=str(scratch / "temporary"),
                       BATON_V12_DISK_ROOT=str(scratch / "temporary"),
                       BATON_V12_VENV=str(Path(sys.executable).parent.parent),
                       PYTHONDONTWRITEBYTECODE="1", PYTHONPATH="src")
    environment.pop("PWD", None)
    environment.pop("OLDPWD", None)
    trace = scratch / "files.trace"
    command = ["timeout", "-k", "10s", "120s", "strace", "-f", "-qq", "-e", "trace=%file", "-o", str(trace),
               "just", "test-one", *modules]
    started = time.monotonic()
    with (evidence / "relocated-tests.log").open("w") as log:
        result = subprocess.run(command, cwd=target / "v12/python", env=environment, stdout=log, stderr=subprocess.STDOUT)
    elapsed = time.monotonic() - started
    matches = []
    total = 0
    digest = hashlib.sha256()
    with trace.open("rb") as lines:
        for line in lines:
            digest.update(line)
            total += 1
            if os.fsencode(str(repo)) in line:
                matches.append(line.decode(errors="replace").rstrip())
    summary = {"command": command, "copied_files": len(paths), "declared_paths": len(identity["inputs"]),
               "consumed_files": identity["consumed_count"], "exit_code": result.returncode,
               "wall_seconds": elapsed, "trace_lines": total, "trace_sha256": digest.hexdigest(),
               "original_checkout_accesses": matches,
               "limitations": "Observed file syscalls; original checkout was not bind-hidden. Prepared interpreter and PATH are explicitly supplied host tools. Raw trace and copy removed as disposable scratch."}
    (evidence / "relocation-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    assert result.returncode == 0, "relocated tests failed"
    assert not matches, "original checkout accessed"
