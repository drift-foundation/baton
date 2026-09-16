"""Independent admission regressions and destination-change checks."""
import hashlib,io,json,os,pathlib,subprocess,sys,tempfile,time
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[5];D=pathlib.Path(__file__).parent
sys.path[:0]=[str(ROOT/"v12/python"),str(ROOT/"v12/python/src")]
from tools import bootstrap,instance
prior=json.loads((D/"REVIEW-EVIDENCE-186560.json").read_text());author=json.loads((D/"EVIDENCE-186583.json").read_text())
candidates=dict(prior["candidate_hashes"],**author["candidates"])
for path,sha in candidates.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
started=time.monotonic()
done=subprocess.run([sys.executable,"-m","unittest","-v","tests.tools.test_instance"],cwd=ROOT/"v12/python",env=dict(os.environ,PYTHONPATH="src:.",PYTHONDONTWRITEBYTECODE="1"),text=True,capture_output=True,timeout=30)
assert done.returncode==0,done.stderr
scratch=pathlib.Path(tempfile.mkdtemp(prefix="w183883-review186639-"));source=scratch/"source";(source/"_internal/rpds").mkdir(parents=True)
(source/"baton-v12-stack").write_text("launcher");(source/"_internal/rpds/rpds.so").write_text("native")
identity={"frozen":True,"schema_assets":{"agent-session-1.0":10,"worker-control-1.0":20},"native_rpds":str(source/"_internal/rpds/rpds.so"),"resources":str(source/"_internal")}
def admit(dest):
    with mock.patch.object(subprocess,"run",return_value=subprocess.CompletedProcess([],0,json.dumps(identity),"")):
        return bootstrap.admit(str(dest),str(source))
results={}
# Actual admission first, then another writer creates selector before install.
dest=scratch/"late-selector";admitted=admit(dest);dest.mkdir();selector=dest/"instance.json";selector.write_text("another writer owns this selector")
bootstrap.install(str(dest),str(source),{"authority_uuid":"a"*32},admitted=admitted,stream=io.StringIO())
assert selector.read_text()!="another writer owns this selector"
results["post_admission_selector_overwritten"]={"selector":str(selector),"original":"another writer owns this selector","now_schema":json.loads(selector.read_text())["schema"]}
# Actual admission first, then the destination gains a foreign state link.
dest=scratch/"late-state-link";admitted=admit(dest);dest.mkdir();foreign=scratch/"foreign-state";foreign.mkdir();(dest/"state").symlink_to(foreign,target_is_directory=True)
bootstrap.install(str(dest),str(source),{"authority_uuid":"a"*32},admitted=admitted,stream=io.StringIO())
try:instance.read(dest/"instance.json")
except instance.InstanceRefusal as exc:refusal=str(exc)
else:raise AssertionError("expected read-time containment refusal")
results["post_admission_foreign_state_accepted"]={"install":"returned success","published_selector":str(dest/"instance.json"),"read_refusal":refusal}
# Positive drift refusal still holds before a copy is attempted.
dest=scratch/"source-drift";admitted=admit(dest);(source/"baton-v12-stack").write_text("changed")
try:bootstrap.install(str(dest),str(source),{"authority_uuid":"a"*32},admitted=admitted,stream=io.StringIO())
except bootstrap.BootstrapRefusal as exc:assert "changed after" in str(exc)
else:raise AssertionError("expected source drift refusal")
assert not dest.exists();results["source_drift_refused_without_destination"]=True
seconds=time.monotonic()-started
out={"claim":186639,"candidate_hashes":candidates,"focused_tests":{"returncode":done.returncode,"stdout":done.stdout,"stderr":done.stderr},"results":results,"verification_seconds":seconds,"retained_scratch":str(scratch),"scope":"40 real unit tests and actual admit/install/read scratch operations, with only runtime identity subprocess substituted. No Authority, scheduler, process control, packaged build, provider, engine, Job, external-root write or Git operation."}
(D/"REVIEW-EVIDENCE-186639.json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2))
