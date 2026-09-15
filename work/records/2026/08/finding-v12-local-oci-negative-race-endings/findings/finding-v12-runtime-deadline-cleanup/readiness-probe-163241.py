"""Read-only readiness children charged within the original W32577 author ledger."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
ledger = root / "verification-162766.json"
mode, *operands = sys.argv[1:]
if mode == "version" and not operands:
    command = ["docker", "version", "--format", "{{json .}}"]
elif mode == "images" and not operands:
    command = ["docker", "image", "ls", "--no-trunc", "--digests", "--format", "{{json .}}"]
elif mode == "inspect" and operands and all(one.startswith("sha256:") for one in operands):
    command = ["docker", "image", "inspect", *operands]
elif mode == "python" and len(operands) == 1 and Path(operands[0]).is_absolute():
    command = [operands[0], "-B", "-c", "import sys,json,importlib.metadata as m; print(json.dumps(dict(executable=sys.executable,version=sys.version,jsonschema=m.version('jsonschema'),distribution=str(m.distribution('jsonschema')._path))))"]
else:
    raise SystemExit("unselected readiness probe")
rows = json.loads(ledger.read_text())
spent = sum(row.get("elapsed", row["timeout"]) for row in rows)
probe_spent = sum(row.get("elapsed", row["timeout"]) for row in rows if row.get("readiness_claim") == 163241)
remaining, probe_remaining = 120 - spent, 20 - probe_spent
expected, margin = 2, 1
if min(remaining, probe_remaining) <= expected + margin:
    raise SystemExit("readiness child cannot fit expected plus margin in both ceilings")
timeout = min(10, remaining - margin, probe_remaining - margin)
row = dict(readiness_claim=163241, command=command, cap=120, readiness_cap=20,
           spent_before=spent, remaining_before=remaining, readiness_spent_before=probe_spent,
           readiness_remaining_before=probe_remaining, expected=expected, margin=margin,
           timeout=timeout, state="running")
rows.append(row)
log = root / f"readiness-163241-{len(rows)}.log"
row["log"] = log.name
ledger.write_text(json.dumps(rows, indent=2) + "\n")
start = time.monotonic()
try:
    with log.open("w") as output:
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT,
                                timeout=timeout, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    row.update(returncode=result.returncode, state="completed")
except subprocess.TimeoutExpired:
    row.update(returncode=124, state="timed-out")
except OSError as error:
    log.write_text(type(error).__name__ + ": " + str(error) + "\n")
    row.update(returncode=127, state="failed-to-start")
finally:
    row["elapsed"] = time.monotonic() - start
    ledger.write_text(json.dumps(rows, indent=2) + "\n")
print(log.read_text()[:10000])
print(json.dumps(dict(log=log.name, author_spent=sum(one["elapsed"] for one in rows),
    readiness_spent=sum(one["elapsed"] for one in rows if one.get("readiness_claim") == 163241))))
raise SystemExit(row["returncode"])
