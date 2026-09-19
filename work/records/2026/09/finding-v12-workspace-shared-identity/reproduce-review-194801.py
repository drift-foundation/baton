"""Local simulated-engine review probes; no real engine or production store."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from baton_v12.worker_manager import oci, workspaces as w

started = time.monotonic()
record = Path(__file__).parent
root = Path(tempfile.mkdtemp(prefix="w194457-review194801-"))
identity = w.WorkspaceIdentity(os.geteuid(), os.getgid(), w._MINT)
image = "sha256:" + "a" * 64
calls = []

def producer(argv, seconds=None):
    calls.append(list(argv))
    mount = next(s for s in argv if s.startswith("type=bind,"))
    source = mount.split("source=", 1)[1].split(",", 1)[0]
    Path(source, "identity-probe").write_text("probe")
    return {"status": 0, "stdout": "", "stderr": ""}

def observe(place, port):
    return oci.observe_runtime_identity("docker", oci.EnginePort(port),
        image_digest=image, identity=identity, place=str(place))

result = {"fixture": str(root), "source_sha256": hashlib.sha256(Path(oci.__file__).read_bytes()).hexdigest()}

# Previously existing data at the helper's fixed path is not owned by this call.
place = root / "existing"
place.mkdir()
prior = place / ".identity-probe"
prior.mkdir()
sentinel = prior / "previous-attempt-evidence"
sentinel.write_text("retain me")
oci._OBSERVED.clear()
answer = observe(place, producer)
result["preexisting_data"] = {"answer": answer, "sentinel_survives": sentinel.exists()}

# A different engine connection and filesystem must not inherit this measurement.
other = root / "other-deployment"
other.mkdir()
second_calls = []
def unavailable(argv, seconds=None):
    second_calls.append(list(argv))
    raise OSError("different engine unavailable")
answer = observe(other, unavailable)
result["different_connection_cache"] = {"answer": answer, "second_engine_calls": len(second_calls),
    "accepted": w.supported_identity_mapping(identity, answer) == identity}

# A symlink to manager-owned data is not a new runtime-created regular-file owner.
place = root / "symlink"
place.mkdir()
outside = root / "manager-owned"
outside.write_text("not created by the runtime")
def symlink_result(argv, seconds=None):
    mount = next(s for s in argv if s.startswith("type=bind,"))
    source = mount.split("source=", 1)[1].split(",", 1)[0]
    Path(source, "identity-probe").symlink_to(outside)
    return {"status": 0, "stdout": "", "stderr": ""}
oci._OBSERVED.clear()
answer = observe(place, symlink_result)
result["symlink_observation"] = {"answer": answer,
    "accepted": w.supported_identity_mapping(identity, answer) == identity,
    "outside_unchanged": outside.read_text() == "not created by the runtime"}

# Model client timeout with a daemon-side helper still present: no real process.
place = root / "timeout"
place.mkdir()
timeout_calls = []
def timeout(argv, seconds=None):
    timeout_calls.append(list(argv))
    raise subprocess.TimeoutExpired(argv, seconds)
oci._OBSERVED.clear()
answer = observe(place, timeout)
result["client_timeout"] = {"answer": answer, "engine_verbs": [v[1] for v in timeout_calls],
    "cleanup_engine_call": any(v[1] in ("rm", "stop", "kill", "inspect") for v in timeout_calls)}
oci._OBSERVED.clear()

test_started = time.monotonic()
run = subprocess.run([sys.executable, "-B", "-m", "unittest",
    "tests.manager.test_workspaces", "tests.manager.test_oci"],
    capture_output=True, text=True, timeout=60)
result["focused_tests"] = {"returncode": run.returncode, "stdout": run.stdout,
    "stderr": run.stderr, "seconds": time.monotonic() - test_started}
result["total_seconds"] = time.monotonic() - started
with (record / "REVIEW-EVIDENCE-194801.json").open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps(result, indent=2))
