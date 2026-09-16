"""Reviewer-only isolated counterexamples; no scheduler/engine/provider execution."""
import copy, hashlib, io, json, os, pathlib, subprocess, sys, tempfile, time
from unittest import mock
ROOT = pathlib.Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
from tools import instance, stack, stack_command, bootstrap, stage_execution
D = pathlib.Path(__file__).parent
claimed = json.loads((D / "EVIDENCE-186381.json").read_text())
for name, digest in claimed["candidates"].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
started = time.monotonic()
root = pathlib.Path(tempfile.mkdtemp(prefix="w183883-review186439-"))
results = {}
def fixture(name, content):
    dest = root / name
    (dest / "distro").mkdir(parents=True)
    (dest / "distro/baton-v12-stack").write_text(content)
    doc = instance.emit(str(dest), authority_uuid="a" * 32,
                        identity={"frozen": True}, runtime=instance.manifest(dest / "distro"))
    instance.publish(dest / "instance.json", doc)
    return dest, doc
a, da = fixture("a", "runtime A")
b, db = fixture("b", "runtime B")
# Baseline and direct byte corruption are checked before the counterexamples.
instance.verify(instance.read(a / "instance.json"))
(a / "distro/baton-v12-stack").write_text("changed")
try: instance.verify(da)
except instance.InstanceRefusal: results["direct_runtime_change_refused"] = True
else: raise AssertionError("expected direct byte change refusal")
(a / "distro/baton-v12-stack").write_text("runtime A")
# A selector retained at A can route stop into B merely by changing state.
foreign = copy.deepcopy(da)
for key in ("state", "logs", "job_store", "control_store", "deployment"):
    foreign[key] = db[key]
instance.publish(a / "instance.json", foreign)
with mock.patch.object(stack, "stop", return_value=0) as stop:
    code = stack.main(["--instance", str(a / "instance.json"), "stop"], stream=io.StringIO(), environ={})
    assert code == 0
    assert stop.call_args.args[0] == pathlib.Path(db["state"])
    results["K1_cross_instance_stop_dispatch"] = {"selector": str(a / "instance.json"), "dispatched_state": str(stop.call_args.args[0]), "returncode": code, "note": "stop substituted; no process was signalled"}
instance.publish(a / "instance.json", da)
# B runtime validates, but start still generates commands from running A.
with mock.patch.object(stack_command, "frozen", return_value=True), mock.patch.object(stack_command, "executable", return_value=str(a / "distro/baton-v12-stack")):
    document, environ = stack.instance_settings(b / "instance.json", {})
    argv = stack.manager_argv(environ, "review")
    assert argv[0] == str(a / "distro/baton-v12-stack")
    assert document["command"] != argv[0]
    results["K2_other_runtime_dispatch"] = {"verified_runtime_digest": document["runtime"]["digest"], "a_digest": da["runtime"]["digest"], "selected_command": document["command"], "actual_child_command": argv[0]}
# External symlink contents change without changing manifest/verification.
external = root / "mutable-library"
external.write_text("version 1")
(a / "distro/library.so").symlink_to(external)
linked = instance.emit(str(a), authority_uuid="a" * 32, identity={"frozen": True}, runtime=instance.manifest(a / "distro"))
before = instance.manifest(a / "distro")
external.write_text("version 2")
after = instance.manifest(a / "distro")
assert before == after
instance.verify(linked)
results["K2_external_symlink_change_accepted"] = {"link": str(a / "distro/library.so"), "manifest_unchanged": True, "verify": "accepted after external target byte change"}
# Invalid resource identity with successful process status is accepted.
bad_identity = {"frozen": False, "schema_assets": "FileNotFoundError: absent", "native_rpds": "ImportError: absent"}
with mock.patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(bad_identity), "")):
    accepted = bootstrap._identity_of("/nonexecuted/review-command")
    assert accepted == bad_identity
    results["K3_invalid_identity_accepted"] = accepted
# main composes before install rejects a missing bundle.
inputs = root / "inputs.json"
inputs.write_text(json.dumps({"authority_uuid": "a" * 32}))
visited = []
with mock.patch.object(bootstrap, "prepare", side_effect=lambda *args, **kw: visited.append("prepare")):
    stream = io.StringIO()
    code = bootstrap.main(["--inputs", str(inputs), "--destination", str(root / "missing-runtime-instance"), "--distro", str(root / "absent-distro")], stream=stream)
assert code == 2 and visited == ["prepare"]
results["K3_prepare_before_install_preflight"] = {"order": ["prepare", "missing distro refusal"], "returncode": code, "output": stream.getvalue(), "note": "prepare substituted to record ordering; no Authority was opened"}
# A preexisting selector without distro is silently replaced by install.
preexisting = root / "preexisting-selector"
preexisting.mkdir(); prior = preexisting / "instance.json"; prior.write_text("old corrupt selector")
with mock.patch.object(bootstrap, "_identity_of", return_value=bad_identity):
    bootstrap.install(str(preexisting), str(b / "distro"), {"authority_uuid": "a" * 32}, stream=io.StringIO())
assert prior.read_text() != "old corrupt selector"
results["K3_existing_selector_overwritten"] = {"selector": str(prior), "identity": json.loads(prior.read_text())["identity"], "note": "direct install, identity probe substituted; real file replaced inside reviewer scratch"}
# Default PyInstaller onedir places resources in _internal, not bundle root.
with mock.patch.object(sys, "frozen", True, create=True), mock.patch.object(sys, "_MEIPASS", str(b / "distro/_internal"), create=True):
    boundary = stage_execution._checkout()
    stage_execution._outside(str(b / "distro/mutable-state"), boundary, "review state")
    results["K4_bundle_root_state_allowed"] = {"returned_code_boundary": boundary, "accepted_mutable_path": str(b / "distro/mutable-state")}
# Type validation should yield an operator refusal, currently raises TypeError.
typed = copy.deepcopy(db); typed["state"] = 17
try: instance.malformed(typed, b / "instance.json")
except TypeError as exc: results["K1_wrong_type_escapes"] = str(exc)
else: raise AssertionError("wrong type behavior changed")
seconds = time.monotonic() - started
out = {"claim": 186439, "candidate_hashes": claimed["candidates"], "results": results, "verification_seconds": seconds, "retained_scratch": str(root), "scope": "Isolated actual helper calls with explicit subprocess/control substitutes; no packaged build, Authority, provider, engine, Job or real stop/start. No external-root writes or Git operations."}
(D / "REVIEW-EVIDENCE-186439.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
