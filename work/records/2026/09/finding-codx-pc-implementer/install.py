import hashlib
import json
import os
import socket
from pathlib import Path

packet = Path(__file__).resolve().parent
base = Path('/home/sl/baton-v11.14aecfb')
side = base / 'codx-pc'
home = Path('/home/sl/.codex-pushcoin')
live = base / 'baton.json'
expected = json.loads((packet / 'base.json').read_text())['config_sha256']
if hashlib.sha256(live.read_bytes()).hexdigest() != expected:
    raise SystemExit('Refused: Baton config changed since preparation; refresh the packet.')
if side.exists() or side.is_symlink():
    raise SystemExit('Refused: codx-pc deployment already exists; inspect before retrying.')
for target in (home / 'rules/baton-codx-pc.rules',):
    if target.exists() or target.is_symlink():
        raise SystemExit(f'Refused: would replace existing {target}')
if not (home / 'auth.json').is_file():
    raise SystemExit('Refused: the selected Codex home has no auth.json.')
with socket.socket() as probe:
    try:
        probe.bind(('127.0.0.1', 4502))
    except OSError as exc:
        raise SystemExit(f'Refused: port 4502 unavailable: {exc}')
side.mkdir(mode=0o700)
(side / 'backup').mkdir(mode=0o700)
(side / 'backup/baton-generation11.json').write_bytes(live.read_bytes())
os.chmod(side / 'backup/baton-generation11.json', 0o600)
(home / 'rules').mkdir(mode=0o700, exist_ok=True)
for name, target in (
    ('infra.json', side / 'infra.json'),
    ('dispatcher.template.json', side / 'dispatcher.template.json'),
    ('baton-codx-pc.rules', home / 'rules/baton-codx-pc.rules'),
):
    with target.open('xb') as handle:
        handle.write((packet / name).read_bytes())
    os.chmod(target, 0o600)
if hashlib.sha256(live.read_bytes()).hexdigest() != expected:
    raise SystemExit('Refused: config drift during installation; live config untouched.')
replacement = side / 'baton-generation12.json'
replacement.write_bytes((packet / 'baton.json').read_bytes())
os.chmod(replacement, live.stat().st_mode & 0o777)
os.replace(replacement, live)
print('Prepared files installed; generation 12 must now be accepted with regen.')
