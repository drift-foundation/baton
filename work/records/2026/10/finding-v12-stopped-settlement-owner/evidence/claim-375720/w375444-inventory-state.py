import runpy,json,sys
m=runpy.run_path(sys.argv[1], run_name="tests.manager.inventory_state"); entries=m['receiving_entries'](); owner=m['EveryReceivingEntryHasOneOwner'](); driver=m['EveryProbeProvesItArrived']()
try:
 driver.setUp(); probes=set(driver.all_probes()); expected=driver.expected()
finally: driver.doCleanups()
records=m['boundary_occurrences'](); _, residual=m['_account_boundary_calls'](records,m['_boundary_claims'](records,entries,m['DELEGATED']),m['NOT_AN_ENTRY'])
print(json.dumps({'unowned':sorted(e for e in entries if owner.owner_of(e)[0] is None),'orphans':sorted(set((r.site,r.kind,r.label) for r in residual)),'missing_probes':sorted(expected-probes),'extra_probes':sorted(probes-expected)},indent=2))
