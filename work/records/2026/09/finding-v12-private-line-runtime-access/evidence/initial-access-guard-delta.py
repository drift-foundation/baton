"""Read-only inventory comparison: checkpoint sources versus saved pre-edit bytes."""
import ast
import json
from pathlib import Path
import sys
from unittest import mock

repo = Path.cwd()
sys.path[:0] = [str(repo / "v12/python"), str(repo / "v12/python/src")]
from tests.manager import test_boundary_inventory as inventory

base = Path(__file__).parent / "initial-access-base"
sources = inventory._sources()


def clear():
    for value in vars(inventory).values():
        if hasattr(value, "cache_clear"):
            value.cache_clear()


def snapshot():
    case = inventory.EveryReceivingEntryHasOneOwner()
    entries = inventory.receiving_entries()
    unowned = {entry for entry in entries if case.owner_of(entry)[0] is None}
    owners = inventory.owning_validators()
    claimed = set()
    for entry in entries:
        places = [(entry[1], inventory._claims(entry))]
        if entry in inventory.DELEGATED:
            places.append(inventory.DELEGATED[entry])
        for site, stem in places:
            for label in inventory._owned_here(site, stem, covering=entry[0] != "injected"):
                claimed |= {(kind, label) for kind, found, _ in owners.get(site, ()) if found == label}
    orphans = {(site, kind, label) for site, found in owners.items() for kind, label, _ in found
               if (kind, label) not in claimed and (site, kind, label) not in inventory.NOT_AN_ENTRY}
    return {"unowned": unowned, "orphans": orphans}


current = snapshot()
baseline_sources = []
for source, tree in sources:
    saved = base / source.relative_to(repo)
    baseline_sources.append((source, ast.parse(saved.read_text(), str(source)) if saved.exists() else tree))
clear()
with mock.patch.object(inventory, "_sources", return_value=tuple(baseline_sources)):
    baseline = snapshot()
print(json.dumps({
    "method": "Only the three scoped production modules are substituted with saved pre-edit ASTs; all other current source and guard bytes stay fixed.",
    "baseline_counts": {key: len(value) for key, value in baseline.items()},
    "candidate_counts": {key: len(value) for key, value in current.items()},
    "added": {key: sorted(current[key] - baseline[key]) for key in current},
    "removed": {key: sorted(baseline[key] - current[key]) for key in current},
}, indent=2))
