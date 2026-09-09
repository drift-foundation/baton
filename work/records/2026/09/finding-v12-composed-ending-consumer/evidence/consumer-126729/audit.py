"""Bind unchanged consumer and accepted provider bytes at this handback."""
import hashlib
import json
from pathlib import Path
import stat

here = Path(__file__).resolve().parent
repo = next(parent for parent in here.parents if (parent / "v12/python/src").is_dir())
dossier = here.parent.parent
consumer = json.loads((dossier / "evidence/takeover-125537/final.json").read_text())["files"]
provider = json.loads((dossier / "findings/finding-integration-stage-observation/evidence/accepted-126698/manifest.json").read_text())
rows = []
for entry in consumer + [{**one, "path": "v12/python/" + one["path"], "mode": "0o" + one["mode"]} for one in provider]:
    path = repo / entry["path"]
    payload = path.read_bytes()
    row = {"path": entry["path"], "sha256": hashlib.sha256(payload).hexdigest(), "mode": oct(stat.S_IMODE(path.stat().st_mode))}
    assert not path.is_symlink()
    assert row["sha256"] == entry["sha256"], row
    assert row["mode"] == entry["mode"], row
    retained = here / "unchanged" / entry["path"]
    retained.parent.mkdir(parents=True, exist_ok=True)
    retained.write_bytes(payload)
    rows.append(row)
(here / "final.json").write_text(json.dumps({"all_eleven_accepted_paths_unchanged": True, "files": rows}, indent=2) + "\n")
print("All eleven consumer/provider files match their accepted or retained baseline bytes and modes.")
