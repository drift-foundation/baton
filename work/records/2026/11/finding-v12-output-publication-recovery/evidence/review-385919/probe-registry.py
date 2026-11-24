import sys,json,time,ast
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.manager import test_boundary_inventory as inv
start=time.monotonic()
entries=[('adopted','review_cycles.py:freeze_unreleased_recovered_checkpoint','replay'),('adopted','workspaces.py:_retained_line_home','line_writers.writer_id')]
for entry in entries:
 print('ENTRY',entry,flush=True)
 print('OWNERS',json.dumps({'entry':entry,'present':entry in inv.receiving_entries(),'claims':inv.ownership_claims(entry),'labels':inv.layer_labels(entry),'stated':inv.STATED_OWNERS.get(entry),'delegated':entry in inv.DELEGATED},default=str),flush=True)
print('ELAPSED',time.monotonic()-start)
