"""Probe accounting restricted to the changed owners: owned-never-probed and probed-never-owned."""
import sys, json, time
from pathlib import Path
root = Path.cwd(); sys.path[:0] = [str(root), str(root / "src"), str(root.parent / "worker")]
from tests.manager import test_boundary_inventory as inv
case = inv.EveryProbeProvesItArrived("test_every_owned_entry_has_exactly_one_probe")
case.setUp()
try:
    declared = set(case.all_probes()); wanted = case.expected()
    files = ("review_cycles.py", "workspaces.py", "provider_context.py")
    un = sorted(x for x in inv._unprobed(wanted, declared) if x[0][1].split(":")[0] in files)
    ow = sorted(x for x in inv._unowned_probes(wanted, declared) if x[0][1].split(":")[0] in files)
finally:
    case.doCleanups()
out = {"unprobed": [[list(e), l] for e, l in un], "unowned": [[list(e), l] for e, l in ow]}
if sys.argv[1] == "all":
    for key in ("unprobed", "unowned"):
        print(key, len(out[key]))
        for x in out[key]: print("  ", key, x)
elif sys.argv[1] == "dump":
    json.dump(out, open(sys.argv[2], "w")); print(len(un), len(ow))
else:
    prev = json.load(open(sys.argv[2]))
    for key in ("unprobed", "unowned"):
        before = {json.dumps(x) for x in prev[key]}
        new = [x for x in out[key] if json.dumps(x) not in before]
        print(key, "total", len(out[key]), "new", len(new))
        for x in new: print("  NEW", key, x)
