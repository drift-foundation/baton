"""Owner host-terminal launcher selected by M164398; prepared, not executed.

Runs the unchanged reviewed supervisor once. The receipt records observation,
not independent acceptance. No build, install or follow-up cleanup is performed.
"""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    record = Path(__file__).resolve().parent
    repo = record.parents[6]
    bindings = record / "execution-bindings-164414.json"
    if hashlib.sha256(bindings.read_bytes()).hexdigest() != "fce9420fa1bc442c4cde748146b2bad73d58a15adab0684c4f3af89695b6e836":
        raise SystemExit("Execution bindings changed; return for review")
    selected = json.loads(bindings.read_text())
    if sys.executable != selected["python"] or importlib.metadata.version("jsonschema") != selected["jsonschema"]:
        raise SystemExit("Selected interpreter/dependency mismatch; no execution")
    for entry in selected["files"]:
        path = repo / entry["path"]
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise SystemExit("Reviewed source changed: " + entry["path"])
    watchdog = Path("/usr/bin/timeout")
    if not watchdog.is_file() or not os.access(watchdog, os.X_OK):
        raise SystemExit("Selected watchdog unavailable; no execution")
    envelope = record / "owner-execution-164414"
    envelope.mkdir()  # Exactly one attempt; never overwrite/reuse prior evidence.
    command = [str(watchdog), "--signal=TERM", "--kill-after=1s", "177s",
               selected["python"], "-W", "error", str(record / "engine-gate.py"),
               "--python", selected["python"], "--run-dir", str(envelope / "run")]
    guard = {"work": "W32577", "owner_selection": 164398, "executor": "owner host terminal",
             "command": command, "cwd": str(repo), "candidate_manifest_sha256": selected["candidate_manifest_sha256"],
             "image": selected["image"], "python": sys.version, "jsonschema": selected["jsonschema"],
             "cap_seconds": 180.0, "spent_seconds_before": 0.0, "expected_seconds": 30.0,
             "margin_seconds": 10.0, "watchdog_seconds": 177.0, "kill_grace_seconds": 1.0,
             "supervisor_phase_seconds": [120, 5, 50, 5], "status": "guarded-not-started"}
    with (envelope / "guard.json").open("x") as stream:
        json.dump(guard, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    result = dict(guard, independent_acceptance=False, status="unresolved", returncode=None)
    with (envelope / "stdout.log").open("xb") as stdout, (envelope / "stderr.log").open("xb") as stderr:
        started = time.monotonic()
        try:
            completed = subprocess.run(command, cwd=repo,
                env={**os.environ, "BATON_W32577_IMAGE_DIGEST": selected["image"], "PYTHONDONTWRITEBYTECODE": "1"},
                stdout=stdout, stderr=stderr)
            result["returncode"] = completed.returncode
            result["status"] = "exited"
        except BaseException as error:
            result["error"] = type(error).__name__ + ": " + str(error)
        finally:
            result["elapsed_seconds"] = time.monotonic() - started
    result["remaining_seconds"] = 180.0 - result["elapsed_seconds"]
    result["candidate_pass"] = result["returncode"] == 0 and result["elapsed_seconds"] < 180.0 and "error" not in result
    result["cleanup_claim"] = "requires inspection of reviewed supervisor evidence; timeout/interruption is not cleanup proof"
    with (envelope / "receipt.json").open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(str(envelope / "receipt.json"))
    return 0 if result["candidate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
