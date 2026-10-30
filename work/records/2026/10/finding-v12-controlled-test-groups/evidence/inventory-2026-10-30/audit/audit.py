"""Debt audit: the same computation as test_every_owned_entry_has_exactly_one_probe."""
import sys, collections
sys.path[:0] = ['src', '.']
from tests.manager import test_boundary_inventory as inv
case = inv.EveryOwnedEntryHasAProbe if hasattr(inv, 'EveryOwnedEntryHasAProbe') else None
# find the class holding all_probes/expected
for name in dir(inv):
    obj = getattr(inv, name)
    if isinstance(obj, type) and hasattr(obj, 'all_probes') and hasattr(obj, 'expected'):
        case = obj
probe_case = case('test_every_owned_entry_has_exactly_one_probe')
probe_case.setUp()
try:
    declared = set(probe_case.all_probes())
finally:
    probe_case.doCleanups()
wanted = probe_case.expected()
unprobed = sorted(inv._unprobed(wanted, declared))
unowned_probes = sorted(inv._unowned_probes(wanted, declared))
entries = inv.receiving_entries()
unowned = sorted(e for e in entries if not inv.layer_labels(e) and e not in inv.STATED_OWNERS and e not in inv.DELEGATED)
print('wanted', len(wanted), 'declared', len(declared), 'entries', len(entries))
print('owned-never-probed', len(unprobed)); [print('  ', u) for u in unprobed]
print('probed-never-owned', len(unowned_probes)); [print('  ', u) for u in unowned_probes]
print('unowned entries', len(unowned))
by_site = collections.Counter(e[1] for e in unowned)
for site, n in by_site.most_common(25): print('  ', n, site)
print('=== entries at _one_by_attempt / writer_for_attempt / review_for_attempt')
for e in sorted(entries):
    if any(s in e[1] for s in ('_one_by_attempt', 'writer_for_attempt', 'review_for_attempt')): print('  ', e, sorted(inv.layer_labels(e)))
own = inv.owning_validators()
for site in ('review_cycles.py:writer_for_attempt', 'review_cycles.py:review_for_attempt', 'review_cycles.py:_one_by_attempt'):
    print('=== owners recorded at', site)
    for found in sorted(own.get(site, ())): print('  ', found)
