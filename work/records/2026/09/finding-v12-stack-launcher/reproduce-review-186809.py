"""Review focused tests, fixed temporary custody and actual recipe dispatch."""
import hashlib,io,json,os,pathlib,subprocess,sys,tempfile,time
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[5];D=pathlib.Path(__file__).parent
sys.path[:0]=[str(ROOT/"v12/python"),str(ROOT/"v12/python/src")]
from tools import bootstrap,instance
candidates=json.loads((D/"EVIDENCE-186742.json").read_text())["candidates"]
for path,sha in candidates.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
started=time.monotonic()
command=[sys.executable,"-B","-m","unittest","-v","tests.tools.test_instance","tests.tools.test_environment","tests.tools.test_stack.TheInstalledMonitor"]
done=subprocess.run(command,cwd=ROOT/"v12/python",env=dict(os.environ,PYTHONPATH="src:.",PYTHONDONTWRITEBYTECODE="1"),text=True,capture_output=True,timeout=30)
assert done.returncode==0,done.stderr
scratch=pathlib.Path(tempfile.mkdtemp(prefix="w183883-review186809-"))
source=scratch/"source";(source/"_internal/rpds").mkdir(parents=True)
(source/"baton-v12-stack").write_text("launcher");(source/"_internal/rpds/rpds.so").write_text("native")
identity={"frozen":True,"schema_assets":{"agent-session-1.0":10,"worker-control-1.0":20},"native_rpds":str(source/"_internal/rpds/rpds.so"),"resources":str(source/"_internal")}
def admit(dest):
    with mock.patch.object(subprocess,"run",return_value=subprocess.CompletedProcess([],0,json.dumps(identity),"")):
        return bootstrap.admit(str(dest),str(source))
results={}
dest=scratch/"temporary-link";dest.mkdir();foreign=scratch/"foreign-document";foreign.write_text("foreign original bytes")
link=dest/"instance.json.new";link.symlink_to(foreign)
admitted=admit(dest)
selector=bootstrap.install(str(dest),str(source),{"authority_uuid":"a"*32},admitted=admitted,stream=io.StringIO())
assert foreign.read_text()=="foreign original bytes" and link.is_symlink()
assert not (dest/"instance.json").is_symlink() and instance.read(dest/"instance.json")==selector
assert not list(dest.glob(".instance-*"));results["temporary_symlink_preserved"]=True
dest=scratch/"temporary-hardlink";dest.mkdir();selector=dest/"instance.json";selector.write_text("existing selector must survive");os.link(selector,dest/"instance.json.new")
try:instance.create(selector,{"schema":instance.SCHEMA})
except instance.InstanceRefusal:pass
else:raise AssertionError("must refuse existing selector")
assert selector.read_text()=="existing selector must survive"
assert (dest/"instance.json.new").read_text()=="existing selector must survive"
assert not list(dest.glob(".instance-*"));results["temporary_hardlink_preserved"]=True
# Harmless executable fixture; real just recipes, helper, selector and manifest.
dest=scratch/"recipe-instance";places=instance.layout(str(dest));pathlib.Path(places["distro"]).mkdir(parents=True)
program=pathlib.Path(places["command"])
def script(label):return "#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps({\"fixture\": "+repr(label)+", \"argv\": sys.argv[1:]}))\n"
program.write_text(script("original"));program.chmod(0o700)
document=instance.emit(str(dest),authority_uuid="a"*32,identity={"frozen":True},runtime=instance.manifest(places["distro"]))
instance.create(places["instance"],document)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",XDG_RUNTIME_DIR=str(scratch))
env.pop("PYTHONPATH",None)
def recipe(verb):
    command=["just","--justfile",str(ROOT/"v12/justfile"),verb,places["instance"]]
    result=subprocess.run(command,cwd=scratch,env=env,text=True,capture_output=True,timeout=15)
    return {"command":command,"returncode":result.returncode,"stdout":result.stdout,"stderr":result.stderr}
results["actual_recipe_positive_controls"]={}
for verb in ("start","status","monitor","stop"):
    result=recipe(verb);assert result["returncode"]==0,result
    said=json.loads(result["stdout"]);assert said["fixture"]=="original" and said["argv"][:3]==[verb,"--instance",places["instance"]],said
    results["actual_recipe_positive_controls"][verb]=result
program.write_text(script("changed-runtime-ran"))
try:instance.verify(instance.read(places["instance"]))
except instance.InstanceRefusal as exc:refusal=str(exc)
else:raise AssertionError("tamper control should refuse")
result=recipe("status")
assert result["returncode"]==0 and json.loads(result["stdout"])["fixture"]=="changed-runtime-ran",result
results["changed_runtime_executed_before_verification"]={"direct_verify_refusal":refusal,"actual_recipe":result}
# A manifest mismatch in a non-executable bundle resource also slips the helper.
program.write_text(script("original"));resource=pathlib.Path(places["distro"])/"resource.dat";resource.write_text("new unbound bytes")
answer=io.StringIO();code=instance.main(["command",places["instance"]],stream=answer)
assert code==0 and answer.getvalue().strip()==places["command"]
results["helper_accepts_changed_bundle_resource"]={"code":code,"answer":answer.getvalue()}
out={"prior_attempt":{"scratch":"/tmp/w183883-review186809-gfw_1tmm","result":"121-test subprocess and custody controls passed; first actual just recipe could not create its temporary script under read-only /run/user/1000/just. No recipe launched. Harness now gives just an owned XDG_RUNTIME_DIR under allowed /tmp.","verification_seconds":"unknown; failed harness did not persist stopwatch"},"claim":186809,"candidate_hashes":candidates,"focused_tests":{"command":command,"returncode":done.returncode,"stdout":done.stdout,"stderr":done.stderr},"results":results,"verification_seconds":time.monotonic()-started,"retained_scratch":str(scratch),"scope":"121 focused unit tests; real scratch filesystem custody; real just recipe/helper dispatch to harmless printing executable fixture, not a frozen bundle. Identity subprocess mocked only for bootstrap custody control. No real stack/Authority/build/provider/engine/Job/Git or external-root mutation."}
(D/"REVIEW-EVIDENCE-186809.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({k:v for k,v in out.items() if k not in ("candidate_hashes","focused_tests")},indent=2))
print(done.stderr[-180:])
