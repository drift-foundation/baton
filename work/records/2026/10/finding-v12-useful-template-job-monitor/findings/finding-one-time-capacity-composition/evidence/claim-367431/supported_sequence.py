import io, json, os, pathlib, sys, tempfile

REPO = pathlib.Path("/home/sl/src/baton")
sys.path[:0] = [str(REPO / "v12/python/src"), str(REPO / "v12/python")]
D = (REPO / "work/records/2026/10/finding-v12-useful-template-job-monitor"
     / "findings/finding-one-time-capacity-composition")
sys.path.insert(0, str(D))
import capacity
from tools import bootstrap, instance, job_manager

out = {}
scratch = pathlib.Path(os.environ.get("BATON_V12_DISK_ROOT",
                                      "/var/tmp/baton-w257624"))
dest = str(pathlib.Path(tempfile.mkdtemp(prefix="w367232-seq-",
                                         dir=str(scratch))) / "instance")
distro = open("/tmp/distro.txt").read().strip()
out["destination"] = dest

PKT = (REPO / "work/records/2026/10/finding-v12-native-pilot-instance-packet"
       / "fresh5-361402/install-inputs.json")

# ---- STEP 1: MINT ONLY. `--inputs` alone, state_root naming the destination.
pilot = json.loads(PKT.read_text())
phase1 = dict(pilot)
phase1["state_root"] = dest
phase1["integration_target"] = os.path.join(dest, "repo", "target.git")
phase1["integration_workspace"] = os.path.join(dest, "repo", "workspace")
assert not phase1.get("workers") and not phase1.get("jobs")
# OUTSIDE THE DESTINATION. `fresh.py:mint` writes it at
# <destination>/install-inputs.json, and the destination-form install in step 4
# then refuses: "there is already an installer input document ... Nothing here
# replaces one". The mint form takes any path, so the staged input lives beside
# the destination and step 4 writes the destination's own slot itself.
pathlib.Path(dest).mkdir(parents=True, exist_ok=False)
p1 = pathlib.Path(dest).parent / "phase1-install-inputs.json"
p1.write_text(json.dumps(phase1, indent=1, sort_keys=True) + "\n")
said = io.StringIO()
code = bootstrap.main(["--inputs", str(p1)], stream=said)
out["step1_mint_exit"] = code
if code != 0:
    out["step1_said"] = said.getvalue().strip().splitlines()[-6:]
    print(json.dumps(out, indent=1))
    raise SystemExit(1)

# ---- STEP 2: readback
places = bootstrap.layout(dest)
minted = json.loads(
    pathlib.Path(places["identity"]).read_text())["authority_uuid"]
out["step2_minted_uuid"] = minted
out["step2_is_generated"] = minted != "0" * 31 + "a"
configured = json.loads(pathlib.Path(places["configuration"]).read_text())
out["step1_configured_no_workers"] = (configured.get("workers") or []) == []

# ---- STEP 3: compose around the readback
held = capacity.compose(minted, destination=dest, distro=distro)
out["step3"] = {"work": held["work_id"], "lanes": held["lanes"],
                "participants": held["participants"],
                "declared_base":
                    held["document"]["jobs"][0]["line_declared_base"]}

# ---- THE ONE TEST SUBSTITUTION IN THIS SEQUENCE, LABELLED.
# Each worker names a nominated source directory, and the installer proves it
# with an lstat: "the nominated source ... is not a directory this manager can
# see (FileNotFoundError)". The OPERATOR gets those directories by passing
# `--repository-source <checkout>`, which CLONES -- and cloning is outside this
# preparation's boundary. So for the inert proof they are created as empty
# directories and that is recorded as a substitution, not as an operational
# arrangement: a real install must select the repository source.
out["test_substitution"] = {
    "what": "the two nominated source directories are created empty",
    "why": "the installer lstats them; the operator obtains them with "
           "--repository-source, which clones, and cloning is outside this "
           "preparation's boundary",
    "not_operational": True}
for lane in capacity.LANES:
    pathlib.Path(os.path.join(instance.layout(dest)["repository"],
                              "source-" + lane["worker_id"])).mkdir(
        parents=True, exist_ok=True)

# ---- THE INSTALLED TASK DOCUMENT IS WRITTEN BEFORE THE INSTALL.
# The installer opens it: "the configured task document could not be opened
# (FileNotFoundError)". `fresh.py:install_and_configure` writes it at the same
# point, for the same reason -- the bytes are the composition's, and the
# manifest's human_contract already digests exactly these.
tp = pathlib.Path(held["installed_task"]["place"])
tp.parent.mkdir(parents=True, exist_ok=True)
tp.write_text(held["task_bytes"])
out["installed_task_written"] = {"place": str(tp),
                                 "bytes": len(held["task_bytes"].encode())}

# ---- STEP 4: ONE destination install carrying both lanes
p2 = pathlib.Path(dest) / "phase2-inputs.json"
p2.write_text(json.dumps(held["document"], indent=1, sort_keys=True) + "\n")
said2 = io.StringIO()
code2 = bootstrap.main(["--inputs", str(p2), "--destination", dest,
                        "--distro", distro, "--no-repositories"],
                       stream=said2)
out["step4_install_exit"] = code2
out["step4_said"] = said2.getvalue().strip().splitlines()[-6:]

if code2 == 0:
    from tools.creation_ports import DeploymentDerivation
    emitted = json.loads(pathlib.Path(
        instance.layout(dest)["deployment"]).read_text())
    out["step4_emitted_lanes"] = sorted(
        (w["role"], w["deployment"]["participant"]) for w in emitted["workers"])
    out["step4_all_minted"] = all(
        w["deployment"]["authority_uuid"] == minted for w in emitted["workers"])
    port = DeploymentDerivation(dest)
    derived = port.derived()
    out["step5_derived"] = {"work_id": derived["work_id"],
                            "profiles": sorted(derived["profiles"]),
                            "input_digest": derived["input_digest"]}
    places2 = instance.layout(dest)
    from baton_v12.worker_manager import ControlStore
    with ControlStore.open(places2["control_store"], incarnation="manager-1",
                           clock=lambda: "2026-09-02T00:00:00.000Z"):
        pass
    argv = ["--store", places2["job_store"], "--incarnation", "operator-1",
            "--authority-uuid", minted, "create",
            "--instance", dest, "--control", places2["control_store"],
            "--authority", places2["authority_store"],
            "--task", capacity.TASK_ID, "--template", capacity.TEMPLATE,
            "--source", "installed", "--statement", capacity.STATEMENT,
            "--provider-turn-seconds", str(capacity.PROVIDER_TURN_SECONDS),
            "--verification-command-seconds",
            str(capacity.VERIFICATION_COMMAND_SECONDS)]
    for one in capacity.ACCEPTANCE:
        argv += ["--acceptance", one]
    for one in capacity.WORK_SCOPE:
        argv += ["--work-scope", one]
    s3 = io.StringIO()
    try:
        c3 = job_manager.main(argv, stream=s3)
        out["step6_create_exit"] = c3
        if c3 == 0:
            a = json.loads(s3.getvalue())
            out["step6_create"] = {
                "job_id": a["job_id"], "work_id": a["work_id"],
                "template": a["template"]["version"],
                "servable": a["servable"],
                "acceptance_count": len(a["acceptance"]),
                "scope": a["scope"],
                "statement": a["task"]["statement"][:60] + "..."}
    except Exception as failure:
        out["step6_create_raised"] = "%s: %s" % (type(failure).__name__,
                                                 str(failure)[:500])
print(json.dumps(out, indent=1, default=str))
