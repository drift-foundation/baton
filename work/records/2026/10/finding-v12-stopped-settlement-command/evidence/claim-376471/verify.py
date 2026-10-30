import unittest,time,json,pathlib,sys
out=pathlib.Path('work/records/2026/10/finding-v12-stopped-settlement-command/evidence/claim-376471')
names=sys.argv[2:];start=time.monotonic()
with (out/(sys.argv[1]+'.log')).open('w') as stream:
 r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
d={'seconds':time.monotonic()-start,'names':names,'tests':r.testsRun,'failures':[(str(t),s) for t,s in r.failures],'errors':[(str(t),s) for t,s in r.errors],'skipped':r.skipped};(out/(sys.argv[1]+'.json')).write_text(json.dumps(d,indent=2)+'\n');print({k:len(v) if k in ('failures','errors') else v for k,v in d.items()})
