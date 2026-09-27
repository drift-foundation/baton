#!/usr/bin/env python3
"""Owner-run exact reviewer-role proposal. Does not accept configuration or restart agents."""
import argparse
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path

config = Path('/home/sl/baton-v11.14aecfb/baton.json')
addition_path = Path(__file__).with_name('ROLE-ADDITION.txt')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true', help='Owner only: replace the deployment config; does not accept it')
args = parser.parse_args()
raw = config.read_bytes()
addition_bytes = addition_path.read_bytes()
if hashlib.sha256(raw).hexdigest() != 'ccfcb1ac55487a11ece571e54aa689c812057f00f1d4a43dbe9129548bd9f31b':
    raise SystemExit('Refused: configuration changed; prepare a fresh proposal.')
if hashlib.sha256(addition_bytes).hexdigest() != '1f95a082c05af0a0f75c1e507dea6a779f3219f6562979c84beb12efd959ceba':
    raise SystemExit('Refused: reviewed role addition changed.')
doc = json.loads(raw)
assert doc['generation'] == 12
doc['generation'] = 13
doc['teams']['baton']['roles']['rview']['instructions'] += ' ' + addition_bytes.decode().strip()
if not args.apply:
    print(json.dumps({'generation': {'before': 12, 'after': 13}, 'teams.baton.roles.rview.instructions': {'before': json.loads(raw)['teams']['baton']['roles']['rview']['instructions'], 'after': doc['teams']['baton']['roles']['rview']['instructions']}}, indent=2))
    raise SystemExit(0)
mode = stat.S_IMODE(config.stat().st_mode)
fd, temporary = tempfile.mkstemp(prefix='.reviewer-role-', dir=config.parent)
try:
    with os.fdopen(fd, 'w') as stream:
        os.fchmod(stream.fileno(), mode)
        stream.write(json.dumps(doc, indent=2, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    if config.read_bytes() != raw:
        raise SystemExit('Refused: configuration changed during preparation.')
    os.replace(temporary, config)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
print('Prepared generation 13: reviewer instructions only. Run the documented owner regen command next.')
