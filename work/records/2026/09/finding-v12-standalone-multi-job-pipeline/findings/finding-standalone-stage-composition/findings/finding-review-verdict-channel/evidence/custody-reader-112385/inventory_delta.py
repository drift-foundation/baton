"""Compare incoming inventory/source diagnostics with the exact assigned candidate.

Run from v12/python with PYTHONPATH=src:.; no source or inventory test is edited.
"""
import ast
import hashlib
import json
from pathlib import Path
from unittest import mock
from tests.manager import test_boundary_inventory as inventory

root = Path(__file__).resolve().parent
import types
current_inventory = inventory
before_inventory = types.ModuleType("tests.manager.before_inventory")
before_inventory.__package__ = "tests.manager"
before_inventory.__file__ = inventory.__file__
exec(compile((root / "before/v12/python/tests/manager/test_boundary_inventory.py").read_text(), inventory.__file__, "exec"), before_inventory.__dict__)
snapshot = inventory._sources()
before = tuple((path, ast.parse((root / "before/v12/python/src/baton_v12/worker_manager" / path.name).read_text())
                if path.name in ("review_cycles.py", "custody.py") else tree) for path, tree in snapshot)


def audit(source):
    for value in vars(inventory).values():
        if callable(getattr(value, "cache_clear", None)):
            value.cache_clear()
    with mock.patch.object(inventory, "_sources", lambda: source):
        owner = inventory.EveryReceivingEntryHasOneOwner()
        entries = inventory.receiving_entries()
        unowned = {entry for entry in entries if owner.owner_of(entry)[0] is None}
        owners = inventory.owning_validators()
        claimed = set()
        for entry in entries:
            places = [(entry[1], inventory._claims(entry))]
            if entry in inventory.DELEGATED:
                places.append(inventory.DELEGATED[entry])
            for site, stem in places:
                for label in inventory._owned_here(site, stem, covering=entry[0] != "injected"):
                    claimed.update((kind, label) for kind, found, _ in owners.get(site, ()) if found == label)
        orphans = {(site, kind, label) for site, found in owners.items() for kind, label, _ in found
                   if (kind, label) not in claimed and (site, kind, label) not in inventory.NOT_AN_ENTRY}
        untracked = inventory.columns_read() - {subject.split(".")[-1] for domain, _, subject in entries
                                               if domain == "adopted" and "." in subject}
        return {"unowned": unowned, "orphans": orphans, "untracked_columns": {(column,) for column in untracked}}


inventory = before_inventory
previous = audit(before)
inventory = current_inventory
current = audit(snapshot)
report = {kind: {"before_count": len(previous[kind]), "after_count": len(current[kind]),
                 "added": sorted(current[kind] - previous[kind]), "removed": sorted(previous[kind] - current[kind])}
          for kind in previous}
report["source_sha256"] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path, _ in snapshot if path.name in ("review_cycles.py", "custody.py")}
(root / "inventory-delta.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
