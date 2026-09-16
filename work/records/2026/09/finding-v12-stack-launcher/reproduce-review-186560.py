"""Independent selector tests and isolated bootstrap admission reproductions."""
import hashlib, io, json, os, pathlib, subprocess, sys, tempfile, time
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[5];D=pathlib.Path(__file__).parent
sys.path[:0]=[str(ROOT/"v12/python"),str(ROOT/"v12/python/src")]
from tools import bootstrap, instance
prior=json.loads((D/"REVIEW-EVIDENCE-186499.json").read_text())
author=json.loads((D/"EVIDENCE-186523.json").read_text())
candidates=dict(prior["candidate_hashes"],**author["candidates"])
for name,sha in candidates.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
assert hashlib.sha256((D/"EVIDENCE-186523.json").read_bytes()).hexdigest()=="30c55f3ed5f6c6a312622c8258ca0bc53efc5199c3c1545de1abda9bafca07a1"
started=time.monotonic()
done=subprocess.run([sys.executable,"-m","unittest","-v","tests.tools.test_instance"],cwd=ROOT/"v12/python",env=dict(os.environ,PYTHONPATH="src:.",PYTHONDONTWRITEBYTECODE="1"),capture_output=True,text=True,timeout=30)
assert done.returncode==0,done.stderr
scratch=pathlib.Path(tempfile.mkdtemp(prefix="w183883-review186560-"));source=scratch/"source-distro";(source/"_internal/rpds").mkdir(parents=True)
(source/"baton-v12-stack").write_text("runtime version 1")
(source/"_internal/rpds/__init__.py").write_text("native-wrapper")
identity={"frozen":True,"schema_assets":{"agent-session-1.0":48212,"worker-control-1.0":51419},"resources":str(source/"_internal"),"native_rpds":str(source/"_internal/rpds/__init__.py")}
def probe_identity(argv,**kw):return subprocess.CompletedProcess(argv,0,json.dumps(identity),"")
results={}
# Invalid resource shape now refuses before prepare and before destination creation.
inputs=scratch/"inputs.json";inputs.write_text(json.dumps({"authority_uuid":"a"*32}))
bad=scratch/"bad-identity"
with mock.patch.object(subprocess,"run",return_value=subprocess.CompletedProcess([],0,json.dumps({"frozen":False}),"")),mock.patch.object(bootstrap,"prepare") as prepared:
    rc=bootstrap.main(["--inputs",str(inputs),"--destination",str(bad),"--distro",str(source)],stream=io.StringIO())
    assert rc==2 and not prepared.called and not bad.exists()
    results["fixed_K3_identity_before_effects"]=True
# Layout containment is checked when reading a selector, not on bootstrap admission.
foreign=scratch/"other-state";foreign.mkdir();dest=scratch/"escaped";dest.mkdir();(dest/"state").symlink_to(foreign,target_is_directory=True)
with mock.patch.object(subprocess,"run",side_effect=probe_identity):
    bootstrap.install(str(dest),str(source),{"authority_uuid":"a"*32},stream=io.StringIO())
try:instance.read(dest/"instance.json")
except instance.InstanceRefusal as exc:refusal=str(exc)
else:raise AssertionError("selector should reveal escaped state")
results["remaining_bootstrap_containment"]={"install_returned_success":True,"selector_published":True,"later_selector_read_refusal":refusal}
# A dangling selector is existing custody even though Path.exists returns false.
dest=scratch/"dangling-selector";dest.mkdir();(dest/"instance.json").symlink_to(scratch/"missing-selector-target")
with mock.patch.object(subprocess,"run",side_effect=probe_identity):bootstrap.install(str(dest),str(source),{"authority_uuid":"a"*32},stream=io.StringIO())
assert not (dest/"instance.json").is_symlink()
results["remaining_dangling_selector_overwrite"]={"prior":"dangling symlink","after":"regular published selector"}
# Native location is accepted relative to an UNBOUND claimed resources path.
foreign_identity=dict(identity,resources="/",native_rpds="/usr/lib/python3/dist-packages/rpds/__init__.py")
with mock.patch.object(subprocess,"run",return_value=subprocess.CompletedProcess([],0,json.dumps(foreign_identity),"")):
    assert bootstrap._identity_of(source/"baton-v12-stack",instance.manifest(source))==foreign_identity
results["remaining_unbound_resource_root"]=foreign_identity
missing_native=dict(identity,native_rpds=str(source/"_internal/nonexistent-rpds.so"))
assert bootstrap._resources_of(missing_native,instance.manifest(source)) is None
results["remaining_unlisted_native_resource"]={"accepted_path":missing_native["native_rpds"],"exists":False}
# The first admission is discarded: a different candidate after prepare is accepted.
initial=instance.manifest(source)["digest"];order=[]
def changed_during_prepare(*args,**kw):
    order.append("prepare")
    (source/"baton-v12-stack").write_text("runtime version 2")
def identity_with_order(argv,**kw):
    order.append("identity:"+instance.manifest(source)["digest"])
    return probe_identity(argv,**kw)
dest=scratch/"changed-candidate"
with mock.patch.object(subprocess,"run",side_effect=identity_with_order),mock.patch.object(bootstrap,"prepare",side_effect=changed_during_prepare):
    rc=bootstrap.main(["--inputs",str(inputs),"--destination",str(dest),"--distro",str(source)],stream=io.StringIO())
assert rc==0
installed=json.loads((dest/"instance.json").read_text())["runtime"]["digest"]
assert installed!=initial
results["remaining_admitted_candidate_drift"]={"returncode":rc,"order":order,"first_admitted":initial,"installed":installed,"note":"prepare substituted to change source; no Authority mutation"}
seconds=time.monotonic()-started
out={"claim":186560,"candidate_hashes":candidates,"focused_tests":{"returncode":done.returncode,"stdout":done.stdout,"stderr":done.stderr},"results":results,"verification_seconds":seconds,"retained_scratch":str(scratch),"scope":"24 real selector unit tests plus isolated bootstrap helper calls; identity subprocess and prepare explicitly substituted. No actual bundle build, Authority, lifecycle, provider, engine, Job, external-root write or Git operation."}
(D/"REVIEW-EVIDENCE-186560.json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2))
