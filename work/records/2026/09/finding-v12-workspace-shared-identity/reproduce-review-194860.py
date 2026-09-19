"""Local deterministic probe cleanup review; never calls a real engine."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest import mock
from baton_v12.worker_manager import oci, workspaces as w

started = time.monotonic()
root = Path(tempfile.mkdtemp(prefix="w194457-review194860-"))
identity = w.WorkspaceIdentity(os.geteuid(), os.getgid(), w._MINT)
result = {"fixture": str(root), "source_sha256": hashlib.sha256(Path(oci.__file__).read_bytes()).hexdigest()}

def scenario(label, *, removal=0, collision=False):
    place = root / label
    place.mkdir()
    calls = []
    running = {"owned": False, "unrelated": collision}
    def run(argv, seconds=None):
        calls.append(list(argv))
        if argv[1] == "rm":
            if removal == 0:
                running.update(owned=False, unrelated=False)
            return {"status": removal, "stdout": "", "stderr": "removal refused" if removal else ""}
        if collision:
            return {"status": 125, "stdout": "", "stderr": "name already in use by unrelated container"}
        running["owned"] = True
        source = next(a for a in argv if a.startswith("type=bind,")).split("source=", 1)[1].split(",", 1)[0]
        Path(source, "identity-probe").write_text("probe")
        return {"status": 0, "stdout": "", "stderr": ""}
    answer = oci.observe_runtime_identity("docker", oci.EnginePort(run),
        image_digest="sha256:" + "a" * 64, identity=identity, place=str(place),
        name="already-owned-by-another-call" if collision else None)
    return {"answer": answer, "engine_verbs": [a[1] for a in calls],
            "modeled_state": running, "remaining_probe_directories": list(place.iterdir())}

result["successful_cleanup"] = scenario("control")
result["nonzero_cleanup_status"] = scenario("failed-removal", removal=1)
result["name_collision"] = scenario("collision", collision=True)

# Race after the root pin check but before rmtree performs its own lookup.
place = root / "replacement-race"
place.mkdir()
probe = place / "owned-probe"
probe.mkdir()
(probe / "owned").write_text("owned")
made = os.lstat(probe)
original_rmtree = oci.shutil.rmtree
def replace_then_remove(path):
    os.rename(path, place / "original-retained")
    Path(path).mkdir()
    (Path(path) / "unrelated-sentinel").write_text("not the pinned directory")
    return original_rmtree(path)
with mock.patch.object(oci.shutil, "rmtree", side_effect=replace_then_remove):
    try:
        oci._remove_probe(str(probe), made)
        outcome = "returned"
    except Exception as exc:
        outcome = type(exc).__name__ + ": " + str(exc)
result["replacement_after_pin_check"] = {"outcome": outcome,
    "unrelated_sentinel_survives": (probe / "unrelated-sentinel").exists(),
    "original_directory_survives": (place / "original-retained" / "owned").exists()}

test_started = time.monotonic()
run = subprocess.run([sys.executable, "-B", "-m", "unittest",
    "tests.manager.test_workspaces", "tests.manager.test_oci"],
    capture_output=True, text=True, timeout=60)
result["focused_tests"] = {"returncode": run.returncode, "stdout": run.stdout,
    "stderr": run.stderr, "seconds": time.monotonic() - test_started}
result["total_seconds"] = time.monotonic() - started
with (Path(__file__).parent / "REVIEW-EVIDENCE-194860.json").open("x") as stream:
    json.dump(result, stream, indent=2, default=str)
    stream.write("\n")
print(json.dumps(result, indent=2, default=str))
