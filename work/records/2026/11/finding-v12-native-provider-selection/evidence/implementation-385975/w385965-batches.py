import json,subprocess,concurrent.futures,pathlib,sys
p=pathlib.Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/implementation-385975')
batches=json.loads((p/'finite-batches.json').read_text())
for off in range(0,len(batches),2):
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  fs=[pool.submit(subprocess.run,['python3','/tmp/w385965-finite.py',n,s,'180'],capture_output=True,text=True) for n,s in batches[off:off+2]]
  results=[f.result() for f in fs]
 for (n,s),r in zip(batches[off:off+2],results): print(n,r.returncode,r.stdout.strip(),r.stderr.strip(),flush=True)
 if any(r.returncode for r in results): sys.exit(1)
