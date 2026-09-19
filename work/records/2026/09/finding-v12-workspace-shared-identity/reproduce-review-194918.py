"""Deterministic local review of observation settlement; no actual engine."""
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
root = Path(tempfile.mkdtemp(prefix="w194457-review194918-"))
identity = w.WorkspaceIdentity(os.geteuid(), os.getgid(), w._MINT)
result = {"fixture": str(root), "source_sha256": hashlib.sha256(Path(oci.__file__).read_bytes()).hexdigest()}

def scenario(case):
    place = root / case
    place.mkdir()
    calls, state = [], {}
    oci.UNRESOLVED.clear()
    def run(argv, seconds=None):
        calls.append(list(argv))
        if argv[1] == "run":
            state["nonce"] = next(a for a in argv if a.startswith(oci._PROBE_LABEL + "=")).split("=", 1)[1]
            state["object"] = "probe-object-id"
            source = next(a for a in argv if a.startswith("type=bind,")).split("source=", 1)[1].split(",", 1)[0]
            Path(source, "identity-probe").write_text("probe")
            return {"status": 0, "stdout": "", "stderr": ""}
        if argv[1] == "inspect":
            if case == "inspection-unavailable":
                return {"status": 1, "stdout": "", "stderr": "Cannot connect to engine daemon"}
            if case == "replacement-after-inspect":
                state["object"] = "unrelated-replacement-id"
            return {"status": 0, "stdout": state["nonce"], "stderr": ""}
        if argv[1] == "rm":
            state["removed_object"] = state.pop("object", None)
            state["removal_target"] = argv[-1]
            return {"status": 0, "stdout": "", "stderr": ""}
        raise AssertionError(argv)
    real_unlink = os.unlink
    def unlink(path, *args, **kwargs):
        if case == "directory-cleanup-fails" and path == "identity-probe":
            raise PermissionError("injected directory cleanup refusal")
        return real_unlink(path, *args, **kwargs)
    with mock.patch.object(oci.os, "unlink", side_effect=unlink):
        answer = oci.observe_runtime_identity("docker", oci.EnginePort(run),
            image_digest="sha256:" + "a" * 64, identity=identity, place=str(place))
    return {"answer": answer, "accepted": w.supported_identity_mapping(identity, answer) == identity,
            "verbs": [a[1] for a in calls], "state": state,
            "unresolved": list(oci.UNRESOLVED), "remaining": [str(p) for p in place.rglob("*")]}

for case in ("control", "inspection-unavailable", "replacement-after-inspect", "directory-cleanup-fails"):
    result[case] = scenario(case)
oci.UNRESOLVED.clear()
test_started = time.monotonic()
run = subprocess.run([sys.executable, "-B", "-m", "unittest", "tests.manager.test_workspaces",
                      "tests.manager.test_oci"], capture_output=True, text=True, timeout=60)
result["tests"] = {"returncode": run.returncode, "stdout": run.stdout,
                   "stderr": run.stderr, "seconds": time.monotonic() - test_started}
result["total_seconds"] = time.monotonic() - started
with (Path(__file__).parent / "REVIEW-EVIDENCE-194918.json").open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps(result, indent=2))
