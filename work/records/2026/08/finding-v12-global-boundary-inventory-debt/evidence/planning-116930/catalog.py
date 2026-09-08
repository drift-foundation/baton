from pathlib import Path
import collections, hashlib, json, sys, time
ROOT=Path.cwd()
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/"v12/python"),str(ROOT/"v12/python/src")]
from tests.manager import test_boundary_inventory as b
start=time.monotonic()
live=ROOT/"v12/python/tests/manager/test_boundary_inventory.py"
assert hashlib.sha256(live.read_bytes()).hexdigest()=="3973301e09e27a4cb724969c158a0441a629037718d755dae1ada594a2a24b5c"
case=b.EveryProbeProvesItArrived()
case.setUp()
try:
    expected=case.expected()
    declared=set(case.all_probes())
finally:
    case.doCleanups()
missing=sorted(expected-declared)
orphan=sorted(declared-expected)
facts={"candidate_sha256":hashlib.sha256(live.read_bytes()).hexdigest(),"expected_count":len(expected),"declared_count":len(declared),"missing_probes":missing,"orphan_probes":orphan,"missing_by_module":dict(sorted(collections.Counter(entry[1].split(":")[0] for entry,label in missing).items())),"orphan_by_module":dict(sorted(collections.Counter(entry[1].split(":")[0] for entry,label in orphan).items())),"elapsed_seconds":time.monotonic()-start,"probe_execution":False,"runtime_hashes":{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((ROOT/"v12/python/src/baton_v12/worker_manager").glob("*.py"))}}
(HERE/"catalog.json").write_text(json.dumps(facts,indent=2,sort_keys=True)+"\n")
print(json.dumps({key:value for key,value in facts.items() if key not in ("missing_probes","orphan_probes","runtime_hashes")},indent=2))
