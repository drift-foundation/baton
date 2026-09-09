import hashlib,json,time
from pathlib import Path
from tests.manager import test_boundary_inventory as b
start=time.monotonic()
e=Path(__file__).resolve().parent
path=Path(b.__file__)
base=path.read_bytes()
assert hashlib.sha256(base).hexdigest()=="bf6160f596ad917fdb4296963d2c272adf3f328b2e78e279dc1f1eb4da7bf00c"
(e/"base-120754.py").write_bytes(base)
entries=b.receiving_entries()
owner=b.EveryReceivingEntryHasOneOwner()
records=b.boundary_occurrences()
claims=b._boundary_claims(records,entries,b.DELEGATED)
_,residual=b._account_boundary_calls(records,claims,b.NOT_AN_ENTRY)
case=b.EveryProbeProvesItArrived()
case.setUp()
try:
    declared={p for p in case.review_cycle_probes() if p[0][1].startswith("review_cycles.py:")}
    expected={p for p in case.expected() if p[0][1].startswith("review_cycles.py:")}
finally:
    case.doCleanups()
module=sorted(e for e in entries if e[1].startswith("review_cycles.py:"))
report=dict(entries=module,owners=[(e,owner.owner_of(e)) for e in module],unowned=[e for e in module if owner.owner_of(e)[0] is None],orphan_calls=sorted({(r.site,r.kind,r.label) for r in residual if r.site.startswith("review_cycles.py:")}),expected=sorted(expected),declared=sorted(declared),missing=sorted(expected-declared),orphan_pairs=sorted(declared-expected),hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [path,Path("v12/python/src/baton_v12/worker_manager/review_cycles.py"),Path("v12/python/src/baton_v12/worker_manager/schema.py")]},seconds=time.monotonic()-start)
with (e/"census-120754.json").open("x") as f:json.dump(report,f,indent=2)
print(json.dumps({k:(len(v) if k in ("entries","owners","expected","declared") else v) for k,v in report.items()},indent=2))
