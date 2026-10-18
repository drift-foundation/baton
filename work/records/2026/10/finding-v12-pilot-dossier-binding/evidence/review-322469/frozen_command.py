import importlib.util,subprocess,os,io,json,time,hashlib
from pathlib import Path
from contextlib import redirect_stdout
p=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("driver",p/"correction-322441/packaged_command.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
binary="/tmp/w321688-review322469-26ea58rx/out/distro/baton-v12-stack"
def command(*operands,cwd):
 env=dict(os.environ);env.pop("PYTHONPATH",None)
 r=subprocess.run([binary,*operands],cwd=cwd,env=env,capture_output=True,text=True,timeout=30)
 return r.returncode,r.stdout,r.stderr
m.command=command
out=io.StringIO();start=time.monotonic()
with redirect_stdout(out):code=m.main()
j=json.loads(out.getvalue());j.update(boundary="new frozen binary; PYTHONPATH removed; disposable real-instance fixtures",frozen_bundle_built=True,entry_script=None,binary=binary,binary_sha256=hashlib.sha256(Path(binary).read_bytes()).hexdigest(),seconds=time.monotonic()-start);j.pop("why_not",None)
assert code==0
for row in j["results"]:
 expected=0 if row["what"] in ("recovery-manifest on the live instance","complete unchanged restore","selector relocated to the restored root") else 2
 assert row["exit"]==expected,row
print(json.dumps(j,indent=2))
