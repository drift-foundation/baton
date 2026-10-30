import io, json, os, pathlib, sys, tempfile
REPO = pathlib.Path("/home/sl/src/baton")
sys.path[:0] = [str(REPO/"v12/python/src"), str(REPO/"v12/python")]
D = REPO/"work/records/2026/10/finding-v12-useful-template-job-monitor/findings/finding-one-time-capacity-composition"
sys.path.insert(0, str(D))
import capacity
from tools import bootstrap, instance, job_manager

out = {}
scratch = pathlib.Path(os.environ.get("BATON_V12_DISK_ROOT","/var/tmp/baton-w257624"))
dest = pathlib.Path(tempfile.mkdtemp(prefix="w367232-dest-", dir=str(scratch)))/"instance"
distro = pathlib.Path(open("/tmp/distro.txt").read().strip())
out["owned_destination"] = str(dest)
out["distro"] = str(distro)

# ---- PHASE 1: mint, with no workers and no jobs
pilot = json.loads((REPO/"work/records/2026/10/finding-v12-native-pilot-instance-packet/fresh5-361402/install-inputs.json").read_text())
phase1 = dict(pilot)
phase1.pop("state_root", None)
places = instance.layout(str(dest))
phase1["integration_target"] = os.path.join(places["repository"], "target.git")
phase1["integration_workspace"] = os.path.join(places["repository"], "workspace")
p1 = dest.parent/"phase1.json"; p1.parent.mkdir(parents=True, exist_ok=True)
p1.write_text(json.dumps(phase1, indent=1, sort_keys=True))
said = io.StringIO()
code = bootstrap.main(["--inputs", str(p1), "--destination", str(dest),
                       "--distro", str(distro), "--no-repositories"], stream=said)
out["phase1_exit"] = code
if code != 0:
    out["phase1_said"] = said.getvalue().strip().splitlines()[-5:]
    print(json.dumps(out, indent=1)); raise SystemExit(1)
minted = json.loads(pathlib.Path(places["identity"]).read_text())["authority_uuid"]
out["minted_authority_uuid"] = minted
out["minted_is_not_the_fixture_constant"] = minted != "0"*31+"a"

# ---- COMPOSE around the minted identity
try:
    held = capacity.compose(minted, destination=str(dest), distro=str(distro))
except capacity.Refused as r:
    out["compose_refused"] = str(r); print(json.dumps(out, indent=1)); raise SystemExit(1)
out["composed"] = {"work_id": held["work_id"], "lanes": held["lanes"],
                   "participants": held["participants"],
                   "document_digest": held["document_digest"],
                   "declared_base": held["document"]["jobs"][0]["line_declared_base"],
                   "every_worker_uuid": sorted({w["deployment"]["authority_uuid"] for w in held["document"]["workers"]})}

# ---- PHASE 2: install the composed capacity
p2 = dest.parent/"phase2.json"
p2.write_text(json.dumps(held["document"], indent=1, sort_keys=True))
said2 = io.StringIO()
# PHASE 2 WITHOUT --distro: the runtime is already installed, and the
# installer refuses to replace one in place. This is the configure-only form.
code2 = bootstrap.main(["--inputs", str(p2), "--destination", str(dest),
                        "--no-repositories"], stream=said2)
out["phase2_exit"] = code2
out["phase2_said"] = said2.getvalue().strip().splitlines()[-6:]
if code2 == 0:
    from tools.creation_ports import DeploymentDerivation
    emitted = json.loads(pathlib.Path(places["deployment"]).read_text())
    out["emitted_lanes"] = sorted((w["role"], w["deployment"]["participant"])
                                  for w in emitted["workers"])
    out["emitted_all_minted"] = all(
        w["deployment"]["authority_uuid"] == minted for w in emitted["workers"])
    port = DeploymentDerivation(str(dest))
    d = port.derived()
    out["derived"] = {"work_id": d["work_id"], "profiles": sorted(d["profiles"]),
                      "input_digest": d["input_digest"][:24]}
    argv = ["--store", places["job_store"], "--incarnation", "operator-1",
            "--authority-uuid", minted, "create",
            "--instance", str(dest), "--control", places["control_store"],
            "--authority", places["authority_store"],
            "--task", capacity.TASK_ID, "--template", capacity.TEMPLATE,
            "--source", "installed",
            "--statement", capacity.STATEMENT,
            "--provider-turn-seconds", str(capacity.PROVIDER_TURN_SECONDS),
            "--verification-command-seconds",
            str(capacity.VERIFICATION_COMMAND_SECONDS)]
    for one in capacity.ACCEPTANCE: argv += ["--acceptance", one]
    for one in capacity.WORK_SCOPE: argv += ["--work-scope", one]
    s3 = io.StringIO()
    try:
        c3 = job_manager.main(argv, stream=s3)
        out["create_exit"] = c3
        if c3 == 0:
            a = json.loads(s3.getvalue())
            out["create"] = {"job_id": a["job_id"], "work_id": a["work_id"],
                             "template": a["template"]["version"],
                             "servable": a["servable"],
                             "acceptance_count": len(a["acceptance"]),
                             "scope": a["scope"]}
    except Exception as e:
        out["create_raised"] = "%s: %s" % (type(e).__name__, str(e)[:400])
print(json.dumps(out, indent=1, default=str))
