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

# ---- STEP 4: ONE destination install carrying both lanes
p2 = pathlib.Path(dest) / "phase2-inputs.json"
p2.write_text(json.dumps(held["document"], indent=1, sort_keys=True) + "\n")
said2 = io.StringIO()
code2 = bootstrap.main(["--inputs", str(p2), "--destination", dest,
                        "--distro", distro, "--no-repositories"],
                       stream=said2)
out["step4_install_exit"] = code2
out["step4_said"] = said2.getvalue().strip().splitlines()[-6:]
print(json.dumps(out, indent=1, default=str))
