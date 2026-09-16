"""Independent fifty-test verification and selector temporary-file custody."""
import hashlib, io, json, os, pathlib, subprocess, sys, tempfile, time
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[5]
D=pathlib.Path(__file__).parent
sys.path[:0]=[str(ROOT/"v12/python"),str(ROOT/"v12/python/src")]
from tools import bootstrap, instance
candidates=json.loads((D/"EVIDENCE-186672.json").read_text())["candidates"]
for path,sha in candidates.items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
started=time.monotonic()
done=subprocess.run([sys.executable,"-B","-m","unittest","-v","tests.tools.test_instance"],cwd=ROOT/"v12/python",env=dict(os.environ,PYTHONPATH="src:.",PYTHONDONTWRITEBYTECODE="1"),text=True,capture_output=True,timeout=30)
assert done.returncode==0,done.stderr
scratch=pathlib.Path(tempfile.mkdtemp(prefix="w183883-review186721-"))
source=scratch/"source"
(source/"_internal/rpds").mkdir(parents=True)
(source/"baton-v12-stack").write_text("launcher")
(source/"_internal/rpds/rpds.so").write_text("native")
identity={"frozen":True,"schema_assets":{"agent-session-1.0":10,"worker-control-1.0":20},"native_rpds":str(source/"_internal/rpds/rpds.so"),"resources":str(source/"_internal")}
def admit(dest):
    with mock.patch.object(subprocess,"run",return_value=subprocess.CompletedProcess([],0,json.dumps(identity),"")):
        return bootstrap.admit(str(dest),str(source))
def install(dest,admitted):
    return bootstrap.install(str(dest),str(source),{"authority_uuid":"a"*32},admitted=admitted,stream=io.StringIO())
results={}
# Previously reported late selector is now preserved.
dest=scratch/"late-selector";admitted=admit(dest);dest.mkdir()
(dest/"instance.json").write_text("foreign selector")
try:install(dest,admitted)
except bootstrap.BootstrapRefusal as exc:
    assert "already an instance selector" in str(exc)
else:raise AssertionError("late selector should refuse")
assert (dest/"instance.json").read_text()=="foreign selector"
assert not (dest/"distro").exists()
results["late_selector_preserved"]=True
# Previously reported late state link is now refused.
dest=scratch/"late-state";admitted=admit(dest);dest.mkdir()
foreign=scratch/"foreign-state";foreign.mkdir();(dest/"state").symlink_to(foreign)
try:install(dest,admitted)
except bootstrap.BootstrapRefusal as exc:assert "carries a link" in str(exc)
else:raise AssertionError("late state link should refuse")
assert not (dest/"instance.json").exists() and list(foreign.iterdir())==[]
results["late_state_link_preserved"]=True
# Existing temporary symlink, present BEFORE actual admission, is followed.
dest=scratch/"temporary-link";dest.mkdir()
foreign=scratch/"foreign-document";foreign.write_text("foreign original bytes")
(dest/"instance.json.new").symlink_to(foreign)
admitted=admit(dest)
install(dest,admitted)
assert foreign.read_text()!="foreign original bytes"
results["preexisting_temporary_symlink"]={"install_returned_success":True,"foreign_original":"foreign original bytes","foreign_now_schema":json.loads(foreign.read_text())["schema"],"temporary_removed":not os.path.lexists(dest/"instance.json.new"),"selector_is_symlink":(dest/"instance.json").is_symlink()}
# create itself damages an EXISTING selector via a hardlinked temporary,
# even though its final no-clobber link correctly refuses the selector name.
dest=scratch/"temporary-hardlink";dest.mkdir();selector=dest/"instance.json"
selector.write_text("existing selector must survive")
os.link(selector,dest/"instance.json.new")
try:instance.create(selector,{"schema":instance.SCHEMA})
except instance.InstanceRefusal as exc:refusal=str(exc)
else:raise AssertionError("existing selector should refuse")
assert selector.read_text()!="existing selector must survive"
results["preexisting_temporary_hardlink"]={"refusal":refusal,"selector_original":"existing selector must survive","selector_now":selector.read_text()}
# Ordinary successful install remains valid.
dest=scratch/"unchanged";admitted=admit(dest);held=install(dest,admitted)
assert instance.read(dest/"instance.json")==held
results["unchanged_install_reads_back"]=True
out={"claim":186721,"candidate_hashes":candidates,"focused_tests":{"returncode":done.returncode,"stdout":done.stdout,"stderr":done.stderr},"results":results,"verification_seconds":time.monotonic()-started,"retained_scratch":str(scratch),"scope":"50 unit tests plus real filesystem admit/install/create/read controls. Only runtime identity subprocess substituted. No Authority/process control/build/provider/engine/Job/Git mutation or external-root writes."}
(D/"REVIEW-EVIDENCE-186721.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({k:v for k,v in out.items() if k not in ("focused_tests","candidate_hashes")},indent=2))
print(done.stderr[-170:])
