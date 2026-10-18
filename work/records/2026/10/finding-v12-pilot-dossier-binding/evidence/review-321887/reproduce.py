import contextlib, hashlib, io, json, os, sys, tempfile
from pathlib import Path
from tools import dossier_command as command
from baton_v12.authority import Authority
from baton_v12.authority.schema import SCHEMA_VERSION

def run(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = command.main(args)
    return {"code": code, "output": json.loads(out.getvalue()) if out.getvalue() else None, "error": err.getvalue()}

with tempfile.TemporaryDirectory(prefix="w321887-") as tmp:
    root = Path(tmp); report = {}
    stores = {}
    for name in command.STORES:
        file = root/name; file.write_bytes(b"disposable member")
        stores[name] = str(file)
    instance = root/"instance.json"; instance.write_text(json.dumps(stores))
    report["missing_provenance_and_artifacts"] = run(["recovery-manifest", "--instance", str(instance)])
    one = root/"only-member"; one.write_bytes(b"one file")
    manifest = {"schema": "baton.v12.instance-recovery-set/1", "schema_version_expected": SCHEMA_VERSION, "members": {"authority_store": {"path": str(one), "digest": "sha256:"+hashlib.sha256(one.read_bytes()).hexdigest(), "sidecars": []}}}
    path = root/"set.json"; path.write_text(json.dumps(manifest))
    report["one_member_recovery"] = run(["recovery-check", "--manifest", str(path), "--root", str(root), "--flat"])
    uuid = "0123456789abcdef0123456789abcdef"; work = uuid[:8]+"-W1"; store = root/"authority.sqlite3"
    with Authority.create(str(store), authority_uuid=uuid) as authority:
        authority.create_work(work, "impl", operation_id="create")
        authority.bind_dossier(work,"example-12345678",operation_id="bind")
    inside = root/"repo"; inside.mkdir(); outside = root/"outside"; outside.write_text("disposable outside bytes")
    (inside/"escape").symlink_to(outside)
    base = ["--authority-store", str(store), "--authority-uuid",uuid,"--work",work,"--root",str(inside)]
    report["symlink_cite"] = run(["cite",*base,"--reference","escape","--operation-id","cite"])
    report["symlink_verify"] = run(["verify",*base])
    assert all(value["code"] == 0 for value in report.values())
    print(json.dumps(report,indent=2))
