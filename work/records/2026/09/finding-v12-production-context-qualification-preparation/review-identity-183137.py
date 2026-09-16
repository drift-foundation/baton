"""Bounded offline identity review. Never reserve or inspect live roots."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import time
from unittest import mock

R = Path(__file__).resolve().parent
E = R / "evidence"
sys.path.insert(0, str(E))
import qualification_contract as c
spec = importlib.util.spec_from_file_location("identity_review_fixture", E / "qualification-fixture.py")
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
e = json.loads((R / "EVIDENCE-183114.json").read_text())
started = time.monotonic()
checks = []
for row in e["files"]:
    for p, digest in ((R / row["path"], row["candidate_sha256"]), (R / row["retained_copy"], row["candidate_sha256"]), (R / "candidate-182906" / Path(row["path"]).name, row["base_sha256"])):
        checks.append({"path": str(p.relative_to(R)), "sha256": sha(p), "matches": sha(p) == digest})
    assert oct(stat.S_IMODE((R / row["path"]).stat().st_mode)) == row["mode"]
assert all(x["matches"] for x in checks)
current = (E / "qualification-fixture.py").read_text()
base = (R / "candidate-182906/qualification-fixture.py").read_text()
assert ast.dump(ast.parse(current.replace('IDENTITY = "183114"', 'IDENTITY = "180078"'))) == ast.dump(ast.parse(base))
manifest = json.loads((E / "qualification-manifest.json").read_text())
old = json.loads((R / "candidate-182906/qualification-manifest.json").read_text())
changed = sorted(k for k in manifest.keys() | old.keys() if manifest.get(k) != old.get(k))
assert set(changed) == {"claim", "consumed_identity", "consumed_identities", "credential_copy_root", "export_root", "files", "private_root", "run_identity"}
packet = (R / "OPERATOR-178579.md").read_text()
tokens = re.findall(r"--approved-manifest ([0-9a-f]{64})", packet)
assert tokens == [e["manifest_sha256"]] * 2
outcomes = []
with mock.patch.object(f, "engine", side_effect=AssertionError("engine forbidden")), mock.patch.object(f, "credential", side_effect=AssertionError("credential forbidden")):
    assert f.audit(e["manifest_sha256"]) == e["manifest_sha256"]
    for prior in ("178579", "180078"):
        for field in ("run_identity", "private_root", "credential_copy_root", "export_root"):
            with tempfile.TemporaryDirectory(prefix="baton-review-183137-") as tmp:
                altered = dict(manifest)
                altered[field] = altered[field].replace("183114", prior)
                path = Path(tmp) / "manifest.json"
                path.write_text(json.dumps(altered))
                with mock.patch.object(f, "MANIFEST", path):
                    try:
                        f.audit()
                    except c.Refusal as error:
                        assert c.failure_code(error) == "manifest-constants"
                        outcomes.append({"consumed_identity": prior, "field": field, "refusal": c.failure_code(error)})
                    else:
                        raise AssertionError("consumed identity mismatch accepted")
    for digest in (e["accepted_base"]["manifest"], "0" * 64):
        try:
            f.audit(digest)
        except c.Refusal as error:
            assert c.failure_code(error) == "manifest-digest"
            outcomes.append({"digest": digest, "refusal": c.failure_code(error)})
        else:
            raise AssertionError("wrong digest accepted")
assert len(outcomes) == 10
assert all(sha(R / row["path"]) == row["candidate_sha256"] for row in e["files"])
record = {"claim": 183137, "candidate_manifest": e["manifest_sha256"], "checks": checks, "current_modes_match": 7, "changed_manifest_keys": changed, "fixture_ast_equal_except_identity": True, "operator_digest_occurrences_match": 2, "outcomes": outcomes, "seconds": time.monotonic() - started, "python": sys.version, "source_unchanged": True, "scope": "offline; no live-root reads/reservation; no engine, credential or model; no children; helper temporary roots cleaned"}
with (R / "review-identity-183137.json").open("x") as out:
    json.dump(record, out, indent=2)
    out.write(chr(10))
print(json.dumps({"checks": len(checks), "negative_audits": len(outcomes), "seconds": record["seconds"]}))
