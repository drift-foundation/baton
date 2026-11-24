"""Run each W385695 probe exactly as test_every_declared_probe_reaches_its_named_boundary does."""
import sys, traceback
from pathlib import Path
root = Path.cwd(); sys.path[:0] = [str(root), str(root / "src"), str(root.parent / "worker")]
from tests.manager import test_boundary_inventory as inv
case = inv.EveryProbeProvesItArrived("test_every_declared_probe_reaches_its_named_boundary")
case.setUp(); keys = sorted(case.w385695_probes()); case.doCleanups()
bad = 0
for entry, fragment in keys:
    try:
        case.setUp()
        full, probe = case.w385695_probes()[(entry, fragment)]
        assert fragment in full
        case.refusing(full, probe)
        print("ok ", entry[1], entry[2], "|", fragment)
    except BaseException as e:
        bad += 1; print("BAD", entry[1], entry[2], "|", fragment, "::", str(e)[:300])
    finally:
        case.doCleanups()
print("PROBES", len(keys), "BAD", bad)
