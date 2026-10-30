import subprocess,os,time,pathlib,json
root=pathlib.Path('/tmp/baton-serving-envelope-347778')
code='''import json
from tests.manager import test_boundary_inventory as t
case=t.EveryReceivingEntryHasOneOwner()
print(json.dumps(sorted(entry for entry in t.receiving_entries() if case.owner_of(entry)[0] is None)))
'''
results={};durations={}
for name,source in [('base',root/'baseline/v12/python/src'),('candidate',root/'v12/python/src')]:
 start=time.monotonic();p=subprocess.run(['python3','-c',code],cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH=str(source)+':.'),capture_output=True,text=True,timeout=30);durations[name]=time.monotonic()-start
 if p.returncode: raise RuntimeError(p.stderr)
 results[name]=json.loads(p.stdout)
added=[x for x in results['candidate'] if x not in results['base']];removed=[x for x in results['base'] if x not in results['candidate']]
report={'seconds':durations,'counts':{k:len(v) for k,v in results.items()},'added':added,'removed':removed,'entries':results}
(root/'evidence/inventory-comparison-final.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='entries'},indent=2))
