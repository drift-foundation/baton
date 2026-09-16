"""Read only named public evidence and candidate bytes; execute no fixture code."""
import ast
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parent
PUBLIC = "operator-result-2026-09-15T15-08-40Z/"
expected = {
    PUBLIC + "qualification.json": "7ac89dac9d7e1457b553b761d406187958866d5c7bbe373280834753ddf5ecfc",
    PUBLIC + "PROVENANCE.json": "27649d4ddfcfaba5b9f20e79e84a2011433bef4a8cc3899b048189b64d02f368",
    PUBLIC + "diagnostic.json": "2695e882e7192e724a6ad8124e8d15f8ebe268b02ce07dc813788b37ae7977ee",
    "evidence/qualification-manifest.json": "73fe32b941b2c82bc0f7bc87a4fa512854dfd64b17b4c8656752607f45dc0481",
    "OPERATOR-178579.md": "e504579fb99ec837d5522a0184906fda3ffb01a3830cbe5e1274af800b5ba323",
    "review-2026-09-15T14-51-59Z.md": "2995243fa8353018fc5ee89171146f40cf6e1a30db4c09a01044064873b1c022",
    "EVIDENCE-178875.json": "b2962d220f7c8eb166b8fe9aab2db7f9884fa144c8cb10453fd6d56e90e6e986",
}
manifest = json.loads((ROOT / "evidence/qualification-manifest.json").read_bytes())
for name, digest in manifest["files"].items():
    expected["evidence/" + name] = digest
    expected["candidate-178875/" + name] = digest
expected["candidate-178875/qualification-manifest.json"] = expected["evidence/qualification-manifest.json"]
inventory = {}
for relative in [*expected, PUBLIC + "diagnostic.py", "audit-179084.py"]:
    path = ROOT / relative
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("nonregular public evidence: " + relative)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    inventory[relative] = {"sha256": digest, "bytes": info.st_size, "mode": oct(stat.S_IMODE(info.st_mode)), "expected": expected.get(relative), "matches": digest == expected[relative] if relative in expected else None}
q = json.loads((ROOT / (PUBLIC + "qualification.json")).read_bytes())
p = json.loads((ROOT / (PUBLIC + "PROVENANCE.json")).read_bytes())
d = json.loads((ROOT / (PUBLIC + "diagnostic.json")).read_bytes())
arm = q["arms"][0]
events = q["events"]
constants = {}
for node in ast.parse((ROOT / "evidence/qualification_contract.py").read_text()).body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ("INITIAL", "CORRECTED"):
        constants[node.targets[0].id] = ast.literal_eval(node.value)
checks = {
    "all_expected_hashes_match": all(row["matches"] for row in inventory.values() if row["expected"] is not None),
    "provenance_binds_public_bytes": p["qualification_sha256"] == inventory[PUBLIC + "qualification.json"]["sha256"],
    "manifest_matches_both_exports": p["fixture_manifest_sha256"] == q["fixture_manifest_sha256"] == expected["evidence/qualification-manifest.json"],
    "diagnostic_repeats_same_terminal": d["terminal"] == arm["terminal"],
    "failed_first_artifact": q["outcome"] == "failed" and q["stage"] == "first-turn" and q["failure_code"] == d["failure_code"] == "initial-artifact",
    "one_observed_arm": len(q["arms"]) == 1 and arm["provider_started"] is True and arm["provider_exit"] == 0,
    "success_session_projection": arm["terminal"]["type"] == "result" and arm["terminal"]["subtype"] == "success" and arm["terminal"]["is_error"] == "false" and arm["terminal"]["session_matches"] is True and arm["terminal"]["session_id"] == q["session"],
    "model_not_established": arm["terminal"]["actual_model"] is None and arm["terminal"]["model_fields"] == [] and "modelUsage" in arm["terminal"]["members"] and "model" not in arm["terminal"]["members"],
    "selected_observed_runtime": q["image"] == manifest["image"] and arm["uid"] == 65532 and arm["groups"] == [1001, 65532] and arm["home_mode"] == "0o2770" and arm["cwd"] == "/output",
    "receipt_consumed_stopped": arm["shutdown"]["consumed"] is True and arm["shutdown"]["running"] is False and arm["shutdown"]["pid"] == 0,
    "events_exact_first_turn_sequence": [e["event"] for e in events] == ["container-create-intent", "container-created", "user-turn-intent", "shutdown-observed", "shutdown-receipt-consumed", "provider-start-observed"],
    "events_monotonic": all(a["monotonic_ns"] <= b["monotonic_ns"] for a, b in zip(events, events[1:])),
    "cleanup_receipt_confirmed": q["cleanup_confirmed"] is True and len(q["cleanup"]) == 3 and all(r["confirmed"] is True for r in q["cleanup"]),
    "diagnostic_outer_whitespace_only": d["workspace"]["entries"] == 1 and d["workspace"]["unexpected_entries"] == 0 and d["solution"]["regular_file"] is True and d["solution"]["exact_match"] is False and d["solution"]["matches_after_crlf_normalization"] is False and d["solution"]["matches_ignoring_outer_whitespace"] is True,
}
report = {"work": "W177936", "claim": 179084, "method": "static public evidence/hash comparisons only; no imports or fixture/diagnostic execution; no private roots read", "inventory": inventory, "checks": checks, "all_checks_match": all(checks.values()), "artifact_lengths": {"expected_initial": len(constants["INITIAL"]), "diagnostic_actual": d["solution"]["size"]}, "operator_elapsed_seconds": q["elapsed_seconds"], "new_runtime_verification_seconds": 0, "limitations": ["Provenance is the retained operator/fixture report, not a signed execution attestation.", "No current Docker/resource inspection or independent private artifact comparison performed.", "Original provider JSON unavailable; the anonymous projection cannot identify the modelUsage mismatch subtype."]}
with (ROOT / "review-evidence-179084.json").open("x") as stream:
    json.dump(report, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps({"all_checks_match": report["all_checks_match"], "checks": len(checks), "inventoried_files": len(inventory), "expected_initial_bytes": len(constants["INITIAL"]), "diagnostic_actual_bytes": d["solution"]["size"]}))
