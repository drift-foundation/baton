"""Isolated K1-K4 follow-up; no real lifecycle or Authority execution."""
import copy, hashlib, io, json, pathlib, subprocess, sys, tempfile, time
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[5]
sys.path[:0]=[str(ROOT/"v12/python"),str(ROOT/"v12/python/src")]
from tools import bootstrap, instance, stack, stack_command, stage_execution
D=pathlib.Path(__file__).parent
current=json.loads((D/"EVIDENCE-186468.json").read_text())
previous=json.loads((D/"EVIDENCE-186381.json").read_text())
candidates=dict(previous["candidates"],**current["candidates"])
for path,sha in candidates.items(): assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
assert hashlib.sha256((D/"EVIDENCE-186468.json").read_bytes()).hexdigest()=="43dc6e5a942ff9bb6e87fa98f58f1867eed37330bc85f4403c046b01144bd629"
started=time.monotonic();scratch=pathlib.Path(tempfile.mkdtemp(prefix="w183883-review186499-"));results={}
def fixture(name):
    root=scratch/name;(root/"distro").mkdir(parents=True)
    (root/"distro/baton-v12-stack").write_text(name)
    doc=instance.emit(str(root),authority_uuid="a"*32,identity={"frozen":True},runtime=instance.manifest(root/"distro"))
    instance.publish(root/"instance.json",doc);return root,doc
a,da=fixture("a");b,db=fixture("b")
def refusal(label,operation,kind):
    try:operation()
    except kind as exc:results[label]=str(exc)
    else:raise AssertionError(label+" was not refused")
changed=copy.deepcopy(da);changed["state"]=db["state"];instance.publish(a/"instance.json",changed)
refusal("fixed_K1_direct_foreign_path",lambda:instance.read(a/"instance.json"),instance.InstanceRefusal)
instance.publish(a/"instance.json",da)
with mock.patch.object(stack_command,"frozen",return_value=True),mock.patch.object(stack_command,"executable",return_value=str(a/"distro/baton-v12-stack")):
    refusal("fixed_K2_foreign_frozen_executable",lambda:instance.verify(db),instance.InstanceRefusal)
    instance.verify(da);results["own_frozen_executable_positive"]=True
external=scratch/"external";external.write_text("library")
links=scratch/"linked-runtime";links.mkdir();(links/"lib").symlink_to(external)
refusal("fixed_K2_external_child_link",lambda:instance.manifest(links),instance.InstanceRefusal)
# K1: the layout-derived path itself resolves outside A, so equality does not protect it.
(b/"state").mkdir();(a/"state").symlink_to(b/"state",target_is_directory=True)
with mock.patch.object(stack,"stop",return_value=0) as stop:
    rc=stack.main(["--instance",str(a/"instance.json"),"stop"],stream=io.StringIO(),environ={})
    dispatched=stop.call_args.args[0]
    assert rc==0 and dispatched.resolve()==b/"state"
    results["remaining_K1_symlink_cross_control"]={"selected":str(a/"instance.json"),"state_argument":str(dispatched),"resolved_state":str(dispatched.resolve()),"returncode":rc,"note":"stop substituted; no signals sent"}
# K2: checking entries does not reject a symlink at the runtime ROOT.
root_link=scratch/"distro-root-link";root_link.symlink_to(b/"distro",target_is_directory=True)
assert instance.manifest(root_link)==instance.manifest(b/"distro")
results["remaining_K2_symlink_runtime_root"]={"accepted_root":str(root_link),"external_target":str(b/"distro")}
wrong=copy.deepcopy(da);wrong["state"]=17
refusal("remaining_K1_wrong_type",lambda:instance.malformed(wrong,a/"instance.json"),TypeError)
inputs=scratch/"inputs.json";inputs.write_text(json.dumps({"authority_uuid":"a"*32}))
with mock.patch.object(bootstrap,"prepare") as prepare:
    rc=bootstrap.main(["--inputs",str(inputs),"--destination",str(scratch/"no-distro-dest"),"--distro",str(scratch/"absent")],stream=io.StringIO())
    assert rc==2 and not prepare.called
    results["fixed_K3_missing_distro_preflight"]=True
existing=scratch/"existing-selector";existing.mkdir();(existing/"instance.json").write_text("corrupt")
refusal("fixed_K3_existing_selector_preserved",lambda:bootstrap.install(str(existing),str(b/"distro"),{"authority_uuid":"a"*32},stream=io.StringIO()),bootstrap.BootstrapRefusal)
assert (existing/"instance.json").read_text()=="corrupt"
bad={"frozen":False,"schema_assets":"missing","native_rpds":"missing"}
with mock.patch.object(subprocess,"run",return_value=subprocess.CompletedProcess([],0,json.dumps(bad),"")):
    refusal("fixed_K3_obvious_bad_identity",lambda:bootstrap._identity_of("/never-executed"),bootstrap.BootstrapRefusal)
# But identity executes after prepare, directories and copy; refusal leaves artifacts.
dest=scratch/"bad-identity-dest";order=[]
with mock.patch.object(bootstrap,"prepare",side_effect=lambda *args,**kw:order.append("prepare")),mock.patch.object(subprocess,"run",side_effect=lambda *args,**kw:order.append("identity") or subprocess.CompletedProcess([],0,json.dumps(bad),"")):
    stream=io.StringIO();rc=bootstrap.main(["--inputs",str(inputs),"--destination",str(dest),"--distro",str(b/"distro")],stream=stream)
assert rc==2 and order==["prepare","identity"] and (dest/"distro/baton-v12-stack").exists()
results["remaining_K3_late_identity_refusal"]={"order":order,"returncode":rc,"copied_runtime_exists":True,"output":stream.getvalue(),"note":"prepare and identity subprocess substituted; real install directories/copy left in scratch"}
for label,said in [("empty",{"frozen":True,"schema_assets":{},"native_rpds":""}),("foreign",{"frozen":True,"schema_assets":{"unrelated":1},"native_rpds":"/usr/lib/python3/dist-packages/rpds/__init__.py"})]:
    with mock.patch.object(subprocess,"run",return_value=subprocess.CompletedProcess([],0,json.dumps(said),"")):
        assert bootstrap._identity_of("/never-executed")==said
        results["remaining_K3_identity_"+label+"_accepted"]=said
# Selected onedir boundary now rejects the entire runtime and allows instance sibling.
with mock.patch.object(sys,"frozen",True,create=True),mock.patch.object(sys,"_MEIPASS",str(b/"distro/_internal"),create=True):
    here=stage_execution._checkout();assert here==str(b/"distro")
    from baton_v12.contracts import ContractRefusal
    refusal("fixed_K4_distro_root_state_refused",lambda:stage_execution._outside(str(b/"distro/mutable-state"),here,"review state"),ContractRefusal)
    stage_execution._outside(str(b/"db"),here,"review state")
    results["fixed_K4_instance_sibling_allowed"]=True
seconds=time.monotonic()-started
out={"claim":186499,"candidate_hashes":candidates,"results":results,"verification_seconds":seconds,"retained_scratch":str(scratch),"scope":"Real isolated helper calls/file writes in scratch; explicit process-control, prepare, subprocess and frozen-mode substitutes. No Authority, actual lifecycle, bundle rebuild, external write, provider, engine, Job or Git mutation."}
(D/"REVIEW-EVIDENCE-186499.json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2))
