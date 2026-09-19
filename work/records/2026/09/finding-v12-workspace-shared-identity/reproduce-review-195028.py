"""Simulated engine protocol and observation-failure checks; no real engine."""
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
root = Path(tempfile.mkdtemp(prefix="w194457-review195028-"))
identity = w.WorkspaceIdentity(os.geteuid(), os.getgid(), w._MINT)
prefix = "abcdef123456"
owned_id = prefix + "a" * 52
other_id = prefix + "b" * 52
result = {"fixture": str(root), "source_sha256": hashlib.sha256(Path(oci.__file__).read_bytes()).hexdigest(),
          "id_format_source": "https://raw.githubusercontent.com/docker/cli/master/cli/command/formatter/container.go"}

def scenario(case):
    place = root / case
    place.mkdir()
    calls, state = [], {}
    oci.UNRESOLVED.clear()
    def run(argv, seconds=None):
        calls.append(list(argv))
        verb = argv[1]
        if verb == "run":
            state["nonce"] = next(a for a in argv if a.startswith(oci._PROBE_LABEL + "=")).split("=", 1)[1]
            state["current_id"] = owned_id
            source = next(a for a in argv if a.startswith("type=bind,")).split("source=", 1)[1].split(",", 1)[0]
            Path(source, "identity-probe").write_text("probe")
            return {"status": 0, "stdout": "", "stderr": ""}
        if verb == "ps":
            if case == "unavailable":
                return {"status": 1, "stdout": "", "stderr": "daemon unreachable"}
            shown = owned_id if "--no-trunc" in argv else prefix
            return {"status": 0, "stdout": shown + "\n", "stderr": ""}
        if verb == "inspect":
            if case == "prefix-replacement":
                state["current_id"] = other_id
            return {"status": 0, "stdout": state["nonce"], "stderr": ""}
        if verb == "rm":
            state["target"] = argv[-1]
            current = state.get("current_id")
            if current and current.startswith(argv[-1]):
                state["removed_id"] = state.pop("current_id")
                return {"status": 0, "stdout": "", "stderr": ""}
            return {"status": 1, "stdout": "", "stderr": "no such object"}
        raise AssertionError(argv)
    keeper = oci._probe_owner
    def reading(*args):
        if case == "observation-error":
            raise OSError("injected ownership-read failure")
        return keeper(*args)
    with mock.patch.object(oci, "_probe_owner", side_effect=reading):
        try:
            answer = oci.observe_runtime_identity("docker", oci.EnginePort(run),
                image_digest="sha256:" + "a" * 64, identity=identity, place=str(place))
            outcome = {"answer": answer}
        except Exception as exc:
            outcome = {"error": type(exc).__name__, "message": str(exc)}
    return {**outcome, "calls": calls, "state": state, "unresolved": list(oci.UNRESOLVED)}

for case in ("control", "unavailable", "prefix-replacement", "observation-error"):
    result[case] = scenario(case)
oci.UNRESOLVED.clear()
test_started = time.monotonic()
run = subprocess.run([sys.executable, "-B", "-m", "unittest", "tests.manager.test_workspaces",
                      "tests.manager.test_oci"], capture_output=True, text=True, timeout=60)
result["tests"] = {"returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
                   "seconds": time.monotonic() - test_started}
result["total_seconds"] = time.monotonic() - started
with (Path(__file__).parent / "REVIEW-EVIDENCE-195028.json").open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
summary = {k: {a:b for a,b in v.items() if a != "calls"} if isinstance(v, dict) else v for k,v in result.items()}
print(json.dumps(summary, indent=2))
