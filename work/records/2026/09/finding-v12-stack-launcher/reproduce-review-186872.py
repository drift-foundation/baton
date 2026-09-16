"""Independent verify-before-dispatch regression and focused suite."""
import hashlib,io,json,os,pathlib,subprocess,sys,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parents[5];D=pathlib.Path(__file__).parent
sys.path[:0]=[str(ROOT/"v12/python"),str(ROOT/"v12/python/src")]
from tools import instance
candidates=json.loads((D/"EVIDENCE-186838.json").read_text())["candidates"]
for path,sha in candidates.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
started=time.monotonic()
command=[sys.executable,"-B","-m","unittest","-v","tests.tools.test_instance","tests.tools.test_environment"]
done=subprocess.run(command,cwd=ROOT/"v12/python",env=dict(os.environ,PYTHONPATH="src:.",PYTHONDONTWRITEBYTECODE="1"),text=True,capture_output=True,timeout=30)
assert done.returncode==0,done.stderr
scratch=pathlib.Path(tempfile.mkdtemp(prefix="w183883-review186872-"))
dest=scratch/"instance";places=instance.layout(str(dest));pathlib.Path(places["distro"]).mkdir(parents=True)
program=pathlib.Path(places["command"])
program.write_text("#!/bin/sh\necho original-runtime\n");program.chmod(0o700)
document=instance.emit(str(dest),authority_uuid="a"*32,identity={"frozen":True},runtime=instance.manifest(places["distro"]))
instance.create(places["instance"],document)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",XDG_RUNTIME_DIR=str(scratch));env.pop("PYTHONPATH",None)
recipe=["just","--justfile",str(ROOT/"v12/justfile"),"status",places["instance"]]
def run():
    r=subprocess.run(recipe,cwd=scratch,env=env,text=True,capture_output=True,timeout=15)
    return {"command":recipe,"returncode":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
positive=run();assert positive["returncode"]==0 and "original-runtime" in positive["stdout"],positive
program.write_text("#!/bin/sh\necho changed-runtime-ran\n")
negative=run();assert negative["returncode"]!=0 and "changed-runtime-ran" not in negative["stdout"]+negative["stderr"],negative
assert "not the one this instance was prepared with" in negative["stderr"],negative
answer=io.StringIO();assert instance.main(["state",places["instance"]],stream=answer)==0
assert answer.getvalue().strip()==places["state"]
out={"claim":186872,"candidate_hashes":candidates,"focused_tests":{"command":command,"returncode":done.returncode,"stdout":done.stdout,"stderr":done.stderr},"results":{"unchanged_runtime_runs":positive,"changed_runtime_refused_before_execution":negative,"broken_instance_state_still_discoverable":True},"verification_seconds":time.monotonic()-started,"retained_scratch":str(scratch),"scope":"123 real focused tests and original actual recipe reproduction with harmless executable fixture. No frozen bundle, real stack, Authority, build, provider, engine, Job, external-root write or Git mutation."}
(D/"REVIEW-EVIDENCE-186872.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({k:v for k,v in out.items() if k not in ("candidate_hashes","focused_tests")},indent=2));print(done.stderr[-180:])
