"""Read retained JSON and proposed command text only; never execute disposal."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex

HERE = Path(__file__).resolve().parent
ROOT = Path.cwd()
baseline = json.loads((ROOT / "work/records/2026/09/finding-v12-unresolved-suite-checks/evidence/docker.json").read_text())
candidate = json.loads((HERE / "current-containers.json").read_text())
live = json.loads((HERE / "review-116180-live.json").read_text())
rows = [json.loads(line) for line in live["operations"][0]["output"].splitlines()]
by_id = lambda items: {one["id"]:one for one in items}
old, proposed, current = map(by_id, (baseline["containers"], candidate["containers"], rows))
assert len(old) == len(proposed) == len(current) == 32
assert set(old) == set(proposed) == set(current)
assert all(current[key] == proposed[key] for key in current)
common = {"id", "name", "created", "state", "started", "finished", "exit_code", "image_id"}
assert all(all(old[key][field] == current[key][field] for field in common) for key in current)
commands = [shlex.split(line) for line in (HERE / "proposed-removal-commands.txt").read_text().splitlines() if line.strip() and not line.startswith("#")]
assert len(commands) == 33
assert all(len(cmd) == 3 and cmd[:2] == ["docker", "rm"] and re.fullmatch("[0-9a-f]{64}", cmd[2]) for cmd in commands[:32])
assert len({cmd[2] for cmd in commands[:32]}) == 32
assert {cmd[2] for cmd in commands[:32]} == set(current)
assert commands[-1] == ["docker", "image", "rm", "baton-w6633-test:7dc2c25ca26c"]
listed = [line.split() for op in live["operations"][2:] for line in op["output"].splitlines()]
assert len(listed) == 32 and {line[0] for line in listed} == set(current)
assert all(line[2] == "exited" for line in listed)
image = "sha256:db9f397171153338ce068b46a7c9ab48c79b80d9f1ad1db4c149541a5eb8199b"
tags = {"baton-w6633-test:7dc2c25ca26c", "baton-w81857-exchange:1", "baton-w81857-exchange:2"}
images = live["operations"][1]["output"].splitlines()
assert len(images) == 3
for line in images:
    identity, aliases = line.split(" ", 1)
    assert json.loads(identity) == image and set(json.loads(aliases)) == tags
facts = {
    "audited_at":datetime.now(timezone.utc).isoformat(),
    "container_count":len(current),
    "same_baseline_ids_and_common_metadata":True,
    "same_candidate_all_selected_metadata":True,
    "same_listing_ids":True,
    "states":dict(Counter(row["state"] for row in rows)),
    "exit_codes":dict(Counter(row["exit_code"] for row in rows)),
    "work_groups":dict(Counter(row["work_id"] or "unlabelled" for row in rows)),
    "unique_exact_container_commands":32,
    "exact_tag_commands":1,
    "shared_image":image,
    "all_three_aliases_directly_verified":True,
    "hashes":{str(path.relative_to(HERE.parent)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (HERE.parent / "DISPOSITION.md", HERE / "proposed-removal-commands.txt", HERE / "current-containers.json", HERE / "inspection-command.txt", HERE / "review-116180-live.json")},
    "disposal_executed":False,
    "manager_lifecycle_observed":False,
}
(HERE / "review-116180-audit.json").write_text(json.dumps(facts, indent=2, sort_keys=True)+"\n")
print(json.dumps(facts, indent=2, sort_keys=True))
