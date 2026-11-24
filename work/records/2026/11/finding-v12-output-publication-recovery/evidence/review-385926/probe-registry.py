import sys,json,unittest,subprocess,ast
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
from tests.manager import test_boundary_inventory as inv
out=Path(__file__).parent
prior=out.parent/'review-385919/registry-prior.log'
line=next(s for s in prior.read_text().splitlines() if s.startswith('ENTRIES '))
old=set(map(tuple,json.loads(line[8:])))
now={e for e in inv.receiving_entries() if e[1].split(':')[0] in ('review_cycles.py','workspaces.py')}
new=sorted(now-old); rows=[{'entry':e,'claims':inv.ownership_claims(e),'labels':inv.layer_labels(e)} for e in new]
assert len(new)==30,len(new)
assert all(sum(r['claims'])==1 for r in rows),rows
(out/'registry-owners.json').write_text(json.dumps(rows,indent=2)+'\n')
print('OWNERS',len(new),'all exactly one')
case=inv.EveryProbeProvesItArrived();case.setUp()
try: keys=list(case.w385695_probes())
finally:case.doCleanups()
for key in keys:
 case=inv.EveryProbeProvesItArrived();case.setUp()
 try:
  label,run=case.w385695_probes()[key];case.refusing(label,run);print('PROBE',key,'PASS')
 finally:case.doCleanups()
print('PROBES',len(keys),'all arrived')
# Read-only Git review of the claimed inherited rename, no mutation.
main=out.parents[6]
source=subprocess.check_output(['git','show','6079ad78345aa87b7148db302d48fb9b1867f940:v12/python/src/baton_v12/worker_manager/review_cycles.py'],cwd=main,text=True)
functions={n.name:n.lineno for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
assert '_freeze_checkpoint' in functions
print('BASE_RENAME',functions['freeze_checkpoint'],functions['_freeze_checkpoint'])
