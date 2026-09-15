"""Owner164359: two read-only Docker subprocess probes from the pinned interpreter."""
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
ledger = root / "verification-162766.json"
if sys.argv[1:] == ["version"]:
    command = ["docker", "version"]
    name = "subprocess-version-164363.json"
elif sys.argv[1:] == ["inspect"]:
    command = ["docker", "image", "inspect", "sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8"]
    name = "subprocess-image-inspect-164363.json"
else:
    raise SystemExit("unassigned probe selector")
rows = json.loads(ledger.read_text())
spent = sum(row.get("elapsed", row["timeout"]) for row in rows)
readiness = sum(row.get("elapsed", row["timeout"]) for row in rows if "readiness_claim" in row)
remaining, probe_remaining = 120 - spent, 20 - readiness
expected, margin = 2, 1
if min(remaining, probe_remaining) <= expected + margin:
    raise SystemExit("expected plus margin cannot fit both existing allowances")
timeout = min(10, remaining - margin, probe_remaining - margin)
row = dict(readiness_claim=164363, command=command, cap=120, readiness_cap=20,
    spent_before=spent, remaining_before=remaining, readiness_spent_before=readiness,
    readiness_remaining_before=probe_remaining, expected=expected, margin=margin,
    timeout=timeout, state="running", log=name, executable=sys.executable,
    python=sys.version, jsonschema=importlib.metadata.version("jsonschema"),
    invocation=sys.argv, cwd=str(Path.cwd()), boundary="pinned Python script via standalone managed exec, Docker via subprocess.run")
rows.append(row)
ledger.write_text(json.dumps(rows, indent=2) + "\n")
start = time.monotonic()
result = {}
try:
    completed = subprocess.run(command, capture_output=True, timeout=timeout)
    row.update(returncode=completed.returncode, state="completed")
    result.update(stdout=completed.stdout.decode("utf-8", "replace"), stderr=completed.stderr.decode("utf-8", "replace"))
except subprocess.TimeoutExpired as error:
    row.update(returncode=124, state="timed-out")
    result.update(stdout=(error.stdout or b"").decode("utf-8", "replace"), stderr=(error.stderr or b"").decode("utf-8", "replace"))
except OSError as error:
    row.update(returncode=127, state="failed-to-start")
    result["error"] = type(error).__name__ + ": " + str(error)
finally:
    row["elapsed"] = time.monotonic() - start
    ledger.write_text(json.dumps(rows, indent=2) + "\n")
    result.update(row)
    (root / name).write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
print(json.dumps(dict(author_spent=sum(one["elapsed"] for one in rows), readiness_spent=sum(one["elapsed"] for one in rows if "readiness_claim" in one))))
raise SystemExit(row["returncode"])
