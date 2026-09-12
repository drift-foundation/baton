"""Supported existing-store diagnostic; no serving, repair, or private store reads."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
sys.dont_write_bytecode = True
REPO = next(p for p in Path(__file__).resolve().parents if (p / 'v12/python/src/baton_v12').is_dir())
sys.path.insert(0, str(REPO / 'v12/python/src'))
from baton_v12.worker_manager.store import ControlStore
from baton_v12.worker_manager.workspaces import configured_workspace_group
from baton_v12.integration import IntegrationStore, reconciliation
ROOT = Path('/home/sl/.local/state/baton/v12/w71879-run9')
clock = lambda: datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
started = time.monotonic()
answer = {'scope': 'supported read-only owners; SQLite-owned WAL/SHM only'}
for name, cls in (('control', ControlStore), ('integration', IntegrationStore)):
    try:
        with cls.open_readonly(str(ROOT / (name + '.sqlite3')), incarnation='w71879-run9', clock=clock) as owner:
            if name == 'control':
                with owner.snapshot():
                    group = configured_workspace_group(owner)
                    answer[name] = {'state': 'read', 'configured_gid': group.gid}
            else:
                result = reconciliation.result_of(owner, 'result-86e13c1fe716246a07ea5ecd03f061713ca1e6a14ed73be4cddfead00e978ded')
                answer[name] = {k: result[k] for k in ('result_id', 'state', 'job_id', 'policy_generation')}
    except Exception as error:
        answer[name] = {'state': 'refused', 'type': type(error).__name__, 'category': getattr(error, 'category', None), 'code': getattr(error, 'code', None), 'message': str(error)}
answer['seconds'] = time.monotonic() - started
print(json.dumps(answer, indent=2))
