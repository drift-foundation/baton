import subprocess,time,json,pathlib,os,sys
root=pathlib.Path('/tmp/baton-serving-envelope-347778'); logs=root/'evidence';logs.mkdir(exist_ok=True)
name=sys.argv[1];args=[sys.executable,'-m','unittest',*sys.argv[2:]]
start=time.monotonic()
try:
 result=subprocess.run(args,cwd=root/'v12/python',env=dict(os.environ,PYTHONPATH='src:.', BATON_V12_DISK_ROOT='/home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal/bootstrap-347778/disk-tests'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
 code=result.returncode;output=result.stdout.decode()
except subprocess.TimeoutExpired as e:
 code=124;output=(e.stdout or b'').decode()
record={'command':args,'seconds':time.monotonic()-start,'status':code}
(logs/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n');(logs/(name+'.log')).write_text(output)
print(json.dumps(record));print(output[-14000:])
