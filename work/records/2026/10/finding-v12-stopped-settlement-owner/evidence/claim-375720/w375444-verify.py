import unittest,time,json,pathlib,sys
out=pathlib.Path('work/records/2026/10/finding-v12-stopped-settlement-owner/evidence/claim-375720')
names=(['tests.manager.test_boundary_inventory'] if sys.argv[1]=='inventory' else ['tests.manager.test_stopped_settlement','tests.manager.test_store','tests.manager.test_maintenance','tests.manager.test_workspaces','tests.manager.test_attempts.CancellationFencesBeforeItStops'])
t=time.monotonic()
with (out/(sys.argv[1]+'.log')).open('w') as stream:
 r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
d={'seconds':time.monotonic()-t,'names':names,'tests':r.testsRun,'failures':[(str(x),s) for x,s in r.failures],'errors':[(str(x),s) for x,s in r.errors],'skipped':r.skipped}
(out/(sys.argv[1]+'.json')).write_text(json.dumps(d,indent=2)+'\n')
print({k:v if k not in ('failures','errors') else len(v) for k,v in d.items()})
