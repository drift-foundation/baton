"""Targeted inventory harness: receiving entries at changed sites and their owners. Usage: inv.py dump FILE | check PREVFILE"""
import sys, json, time
from pathlib import Path
root = Path.cwd(); sys.path[:0] = [str(root), str(root / "src")]
from tests.manager import test_boundary_inventory as inv
mode = sys.argv[1]
start = time.monotonic()
try:
    entries = sorted(inv.receiving_entries())
except AssertionError as e:
    print("RECEIVING-ERROR", e); sys.exit(2)
mine = [e for e in entries if e[1].split(":")[0] in ("review_cycles.py", "workspaces.py", "provider_context.py")]
if mode == "dump":
    json.dump(mine, open(sys.argv[2], "w")); print(len(entries), len(mine), time.monotonic() - start); sys.exit(0)
prev = {tuple(e) for e in json.load(open(sys.argv[2]))}
new = [e for e in mine if e not in prev]
gone = [e for e in prev if e not in set(mine)]
print("NEW", len(new), "GONE", len(gone))
case = inv.EveryReceivingEntryHasOneOwner("owner_of")
bad = 0
for e in new:
    try:
        owner = case.owner_of(e); claims = inv.ownership_claims(e)
    except AssertionError as err:
        print("LABEL-ERROR", e, err); bad += 1; continue
    ok = owner[0] is not None and sum(claims) == 1
    bad += not ok
    print("ok " if ok else "BAD", e, owner[0], owner[1] if owner[0] else "", claims)
for e in gone: print("GONE", e)
print("ELAPSED", time.monotonic() - start, "BAD", bad)
