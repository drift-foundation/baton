"""Receiving entries added by this correction (vs reviewed 58d452ff), each with its owner."""
import sys, json
from pathlib import Path
root = Path.cwd(); sys.path[:0] = [str(root), str(root / "src"), str(root.parent / "worker")]
from tests.manager import test_boundary_inventory as inv
entries = inv.receiving_entries()
mine = sorted(e for e in entries if "abandonment_declared" in e[1])
owner = inv.EveryReceivingEntryHasOneOwner()
for e in mine:
    try: got = owner.owner_of(e)
    except BaseException as x: got = ("ERR", str(x)[:200])
    kinds = (bool(inv.layer_labels(e)), e in inv.STATED_OWNERS, e in inv.DELEGATED)
    print(e, "owner", got, "labels/stated/delegated", kinds)
print("ENTRIES", len(mine))
