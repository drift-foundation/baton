import io, json, os, pathlib, sys, tempfile
REPO = pathlib.Path("/home/sl/src/baton")
sys.path[:0] = [str(REPO/"v12/python/src"), str(REPO/"v12/python")]
PKT = REPO/"work/records/2026/10/finding-v12-native-pilot-instance-packet/fresh5-361402"
F3  = REPO/"work/records/2026/10/finding-v12-native-pilot-instance-packet/fresh3-358443"
sys.path[:0] = [str(F3), str(PKT),
                str(REPO/"work/records/2026/10/finding-v12-native-pilot-instance-packet/post-install-357462")]
out = {}
try:
    import fresh
    out["fresh_imported"] = True
    out["fresh_JOB"] = getattr(fresh, "JOB", None)
    out["has_compose"] = hasattr(fresh, "_compose")
except Exception as e:
    out["fresh_import_error"] = "%s: %s" % (type(e).__name__, e)
    print(json.dumps(out, indent=1)); raise SystemExit(1)
root = tempfile.mkdtemp(prefix="w366962-inert-", dir="/var/tmp")
dest = os.path.join(root, "disposable")
try:
    from tools import bootstrap, instance
    doc = json.loads((PKT/"install-inputs.json").read_text())
    doc.pop("state_root", None)
    doc["integration_target"] = os.path.join(dest, "repo", "target.git")
    doc["integration_workspace"] = os.path.join(dest, "repo", "workspace")
    inputs = os.path.join(root, "phase1.json")
    pathlib.Path(inputs).write_text(json.dumps(doc, indent=1, sort_keys=True))
    said = io.StringIO()
    code = bootstrap.main(["--inputs", inputs, "--destination", dest,
                           "--no-repositories"], stream=said)
    out["phase1_exit"] = code
    out["phase1_said"] = said.getvalue().strip().splitlines()[-6:]
    if code == 0:
        places = instance.layout(dest)
        held = json.loads(pathlib.Path(places["identity"]).read_text())
        out["minted_uuid"] = held.get("authority_uuid")
except Exception as e:
    out["phase1_error"] = "%s: %s" % (type(e).__name__, str(e)[:500])
out["disposable_root"] = root
print(json.dumps(out, indent=1))
