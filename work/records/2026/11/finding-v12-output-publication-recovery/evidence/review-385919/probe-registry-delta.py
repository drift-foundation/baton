import sys,json,time
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.manager import test_boundary_inventory as inv
entries=sorted(e for e in inv.receiving_entries() if e[1].split(':')[0] in ('review_cycles.py','workspaces.py'))
print('ENTRIES',json.dumps(entries),flush=True)
try:
 owners=inv.owning_validators()
 print('OWNERS_BUILT',len(owners),flush=True)
except AssertionError as error:
 print('OWNERS_ERROR',str(error),flush=True);raise
