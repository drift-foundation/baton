"""Account standalone managed-tool probes; never launches Docker itself."""
import json
from pathlib import Path
import sys
root = Path(__file__).resolve().parent
path = root / "verification-162766.json"
rows = json.loads(path.read_text())
if sys.argv[1] == "prepare":
    spent = sum(row.get("elapsed", row["timeout"]) for row in rows)
    probes = sum(row.get("elapsed", row["timeout"]) for row in rows if "readiness_claim" in row)
    remaining, probe_remaining = 120 - spent, 20 - probes
    expected, margin = 2, 1
    if min(remaining, probe_remaining) <= expected + margin:
        raise SystemExit("probe cannot fit both remaining allowances")
    command = ["docker", "version"] if sys.argv[2] == "version" else ["docker", "image", "inspect", "sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8"]
    rows.append(dict(readiness_claim=164329, command=command, boundary="standalone managed exec tool",
        cap=120, readiness_cap=20, spent_before=spent, remaining_before=remaining,
        readiness_spent_before=probes, readiness_remaining_before=probe_remaining,
        expected=expected, margin=margin, timeout=min(10, remaining-margin, probe_remaining-margin), state="running"))
else:
    assert rows[-1]["state"] == "running" and rows[-1]["readiness_claim"] == 164329
    result = json.loads((root / sys.argv[2]).read_text())
    rows[-1].update(elapsed=result["elapsed"], state=result["state"], returncode=result["returncode"], log=sys.argv[2])
path.write_text(json.dumps(rows, indent=2) + "\n")
print(json.dumps(dict(rows=len(rows), current=rows[-1], author_spent=sum(row.get("elapsed", row["timeout"]) for row in rows))))
