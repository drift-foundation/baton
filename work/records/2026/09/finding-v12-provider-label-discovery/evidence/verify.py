"""W116523 bounded accepted controls and original6–8 census; budget30s total."""
from pathlib import Path
import ast
import collections
import hashlib
import json
import os
import sys
import time
import unittest

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
from tests.manager import test_boundary_inventory as b
os.chdir(ROOT / "v12/python")
os.environ["PYTHONPATH"] = str(ROOT / "v12/python/src")
start = time.monotonic()
names = [
    "AdoptedHelperOriginsAreContextual",
    "DeclaredMountOriginsStayWithTheirElements",
    "TheDiscoveryProjectionsAreBoundedAndImmutable",
    "EveryReceivingEntryHasOneOwner.test_every_boundary_call_belongs_to_an_entry_or_is_declared",
    "EveryReceivingEntryHasOneOwner.test_every_receiving_entry_has_an_owning_validator",
    "EveryReceivingEntryHasOneOwner.test_the_universe_sees_every_persisted_column_that_is_read",
]
with (HERE / "verification.txt").open("w") as stream:
    stream.write("Exact command: python3 " + str(Path(__file__).relative_to(ROOT)) + "\n")
    stream.write("Initial focused14=0.439s and broader+census8.617s retained separately. Final focused15 follows contextual member correction. Total budget30s.\n")
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names, b))
entries = b.receiving_entries()
owners = b.owning_validators()
case = b.EveryReceivingEntryHasOneOwner()
unowned = sorted(entry for entry in entries if case.owner_of(entry)[0] is None)
claimed = set()
for entry in entries:
    places = [(entry[1], b._claims(entry))]
    if entry in b.DELEGATED:
        places.append(b.DELEGATED[entry])
    for site, stem in places:
        for label in b._owned_here(site, stem, covering=entry[0] != "injected"):
            claimed.update((kind,label) for kind,found,_ in owners.get(site,()) if found==label)
orphans = sorted({(site,kind,label) for site,found in owners.items() for kind,label,_ in found
                  if (kind,label) not in claimed and (site,kind,label) not in b.NOT_AN_ENTRY})
facts = {"elapsed_seconds":time.monotonic()-start,"tests_run":result.testsRun,
         "failures":[test.id() for test,_ in result.failures],"errors":[test.id() for test,_ in result.errors],
         "entry_count":len(entries),"unowned":unowned,"orphans":orphans,
         "unowned_by_module":dict(sorted(collections.Counter(site.split(":")[0] for _,site,_ in unowned).items())),
         "orphan_by_module":dict(sorted(collections.Counter(site.split(":")[0] for site,_,_ in orphans).items())),
         "provider_owners":{site:sorted(found) for site,found in owners.items() if site.startswith("intake.py:") and any("teardown ending" in label for _,label,_ in found)},
         "provider_entries":sorted(entry for entry in entries if ".credentials" in entry[2] or ".launch" in entry[2]),
         "candidate_sha256":hashlib.sha256((ROOT / "v12/python/tests/manager/test_boundary_inventory.py").read_bytes()).hexdigest()}
(HERE / "census.json").write_text(json.dumps(facts,indent=2,sort_keys=True)+"\n")
print(json.dumps({key:value for key,value in facts.items() if key not in ("unowned","orphans","provider_owners","provider_entries")},indent=2))
sys.exit(1 if result.failures or result.errors else 0)
