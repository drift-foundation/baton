"""Read-only operator/executor preflight. Does not create the selected root."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('/home/sl/baton-instances/serving-renewal-w333485-339444')
BASE = Path('/home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal')
AMEND = BASE / 'findings/finding-lease-policy-amendment/amendment-345734'
expected = '8a46facba604ad3c5e2c1c1b7d76eaf91b84ea1e2aad5e904f296c301a7c7394'
checks = {
    'uid_is_sl_1000': os.geteuid() == 1000,
    'root_absent_including_symlink': not os.path.lexists(ROOT),
    'parent_is_canonical_directory': ROOT.parent.is_dir() and ROOT.parent.resolve() == ROOT.parent,
    'parent_writable_and_searchable': os.access(ROOT.parent, os.W_OK | os.X_OK),
    'amendment_manifest_matches': hashlib.sha256((AMEND / 'AMENDMENT.json').read_bytes()).hexdigest() == expected,
}
if checks['amendment_manifest_matches']:
    result = subprocess.run([sys.executable, '-B', str(AMEND / 'prepare.py'), 'verify'], capture_output=True, text=True, timeout=30)
    checks['all_preparation_pins_match'] = result.returncode == 0
else:
    checks['all_preparation_pins_match'] = False
print(json.dumps({'schema': 'w345730-readonly-preflight/1', 'root': str(ROOT), 'checks': checks, 'writes_performed': False, 'launch_selected': False, 'note': 'Access is this invoking process only. A pass is not proof of another executor boundary or authorization to stage/start.'}, indent=2))
sys.exit(0 if all(checks.values()) else 1)
