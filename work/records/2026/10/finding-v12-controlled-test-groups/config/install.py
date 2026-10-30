"""W384870 — install the generation-15 candidate over the live baton.json.

Refuses on drift; backs up the accepted generation 14 beside the live config.
It does not accept anything: `regen` as baton.slaw is the acceptance.
"""
import hashlib, json, os
from pathlib import Path
packet = Path(__file__).resolve().parent
base = json.loads((packet / "base.json").read_text())
live = Path(base["live"])
if hashlib.sha256(live.read_bytes()).hexdigest() != base["config_sha256"]:
    raise SystemExit("Refused: live baton.json changed since preparation; refresh the packet.")
candidate = (packet / "baton-generation15.json").read_bytes()
if hashlib.sha256(candidate).hexdigest() != base["candidate_sha256"]:
    raise SystemExit("Refused: candidate bytes differ from the prepared digest.")
backup = live.parent / "backup"
backup.mkdir(mode=0o700, exist_ok=True)
saved = backup / "baton-generation14.json"
if saved.exists():
    raise SystemExit(f"Refused: {saved} already exists; inspect before retrying.")
saved.write_bytes(live.read_bytes()); os.chmod(saved, 0o600)
staged = live.parent / "baton-generation15.json"
staged.write_bytes(candidate); os.chmod(staged, live.stat().st_mode & 0o777)
os.replace(staged, live)
print("generation 15 candidate installed at", live, "; accept it with regen as baton.slaw.")
