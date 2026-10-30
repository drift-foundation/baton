import json, sys
sys.path[:0] = ['src', '.']
from baton_v12.worker_manager import ControlStore, attempts
from tools.authoring_enforcement import utc
root = sys.argv[1]
with ControlStore.open(root + '/control.sqlite3', incarnation='w384870-c7-read', clock=utc) as control:
    rows = attempts._attempts(control, "WHERE 1=1 ORDER BY runtime_attempt_id")
    for row in rows:
        print('ROW', {k: row[k] for k in ('runtime_attempt_id', 'execution_runtime', 'cleanup', 'runtime_id', 'workspace_device', 'workspace_inode') if k in row.keys()})
        op = attempts._start_operation_id(row)
        print('START', op)
        rec = control.operation_record(op)
        print('START RECORD', json.dumps(rec, default=str)[:1500])
        cancel = attempts._cancel_operation_id(row)
        print('CANCEL RECORD', json.dumps(control.operation_record(cancel), default=str)[:600])
