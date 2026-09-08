"""Record candidate hashes, exact deltas, and reusable implementer evidence."""
import ast
import datetime
import difflib
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[8]
DOSSIER = HERE.parents[1]
BASE = DOSSIER.parents[1] / "evidence/review-114048/candidate"
author = json.loads((DOSSIER / "evidence/implementation-114090/audit.json").read_text())
audit = {"claim": 114231, "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "paths": {}}
for name, expected in author["delivered"].items():
    data = (REPO / name).read_bytes()
    target = HERE / "candidate" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    old = (BASE / name).read_text()
    new = data.decode()
    measured = hashlib.sha256(data).hexdigest()
    audit["paths"][name] = {"sha256": measured, "author_sha256": expected, "matches": measured == expected}
    (HERE / (Path(name).name + ".diff")).write_text("".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True))))
    if "/tests/" in name:
        def methods(text):
            return {(node.name, member.name): ast.get_source_segment(text, member)
                    for node in ast.parse(text).body if isinstance(node, ast.ClassDef)
                    for member in node.body if isinstance(member, ast.FunctionDef)}
        before, after = methods(old), methods(new)
        audit["test_delta"] = {"removed": [list(key) for key in before.keys() - after.keys()],
                               "changed": [list(key) for key in before if key in after and before[key] != after[key]],
                               "added_test_count": sum(key[1].startswith("test_") for key in after.keys() - before.keys())}
focused = (DOSSIER / "evidence/implementation-114090/focused.txt").read_bytes()
(HERE / "focused-author.txt").write_bytes(focused)
text = focused.decode()
audit["retained_focused"] = {"sha256": hashlib.sha256(focused).hexdigest(),
                              "summary": re.findall(r"^(?:Ran .*|FAILED .*|OK)$", text, re.M),
                              "failures": re.findall(r"^(?:FAIL|ERROR): .*", text, re.M)}
(HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps(audit, indent=2))
