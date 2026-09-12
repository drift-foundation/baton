"""Supported read-only opener probe; no fallback, raw store access or repair."""
from datetime import datetime, timezone
from pathlib import Path
import json
import stat
import time
from baton_v12.integration import IntegrationStore
from baton_v12.worker_manager import ControlStore
from baton_v12.worker_manager.workspaces import WorkspaceGroup

HERE = Path(__file__).resolve().parent
RUN = Path('/home/sl/.local/state/baton/v12/w71879-run9')
started = time.monotonic()
answer = {'control_public_readonly_opener': hasattr(ControlStore, 'open_readonly'),
          'metadata': {}, 'coordinator': None, 'caller_minted_workspace_group': None}
for name in ('integration.sqlite3', 'integration.sqlite3-wal', 'integration.sqlite3-shm'):
    path = RUN / name
    try:
        one = path.stat()
        answer['metadata'][name] = {'mode': oct(stat.S_IMODE(one.st_mode)), 'uid': one.st_uid, 'gid': one.st_gid, 'bytes': one.st_size}
    except FileNotFoundError:
        answer['metadata'][name] = {'present': False}
try:
    with IntegrationStore.open_readonly(str(RUN / 'integration.sqlite3'), incarnation='w71879-run9', clock=lambda: datetime.now(timezone.utc).isoformat()):
        answer['coordinator'] = {'opened': True}
except Exception as failure:
    answer['coordinator'] = {'opened': False, 'type': type(failure).__name__, 'category': getattr(failure, 'category', None), 'code': getattr(failure, 'code', None), 'message': str(failure)}
try:
    WorkspaceGroup(1001)
except Exception as failure:
    answer['caller_minted_workspace_group'] = {'type': type(failure).__name__, 'category': getattr(failure, 'category', None), 'code': getattr(failure, 'code', None), 'message': str(failure)}
answer['seconds'] = time.monotonic() - started
(HERE / 'reader-findings.json').write_text(json.dumps(answer, indent=2) + '\n')
print(json.dumps(answer, indent=2))
