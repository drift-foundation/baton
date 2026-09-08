"""Independent custody-root and authority-correlation probes, no suite/live/Git."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from unittest import mock

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[8]
sys.path[:0] = [str(REPO / "v12/python"), str(REPO / "v12/python/src")]
from tests.tools import test_integration_bundle as fixture
from baton_v12.contracts.canonical import canonical_bytes
from baton_v12.worker_manager.workspaces import configured_workspace_storage


def reader_case(name, mutate):
    case = fixture.ProducerCase("run")
    case.setUp()
    try:
        answer = case.compose()
        source = Path(answer["root"])
        derived = Path(case.world.owner.root) / name
        # Copy content into a new review-owned tree, preserving original custody.
        for entry in source.rglob("*"):
            if entry.is_file():
                target = derived / entry.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(entry.read_bytes())
        place = derived / "evidence/authority.json"
        authority = json.loads(place.read_bytes())
        mutate(authority)
        body = canonical_bytes(authority)
        place.write_bytes(body)
        envelope = json.loads((derived / "integration.json").read_bytes())
        reference = next(row for row in envelope["evidence"] if row["name"] == "authority.json")
        reference.update(bytes=len(body), digest=hashlib.sha256(body).hexdigest())
        (derived / "integration.json").write_bytes(canonical_bytes(envelope))
        try:
            result = fixture.contract.read_bundle(str(derived))
            return {"case": name, "accepted": True,
                    "reader_review_identity": result["review"]["identity"],
                    "review_file_count": len(result["review"]["documents"])}
        except Exception as error:
            return {"case": name, "accepted": False, "error": str(error)}
    finally:
        case.doCleanups()


def changed_review(authority):
    output = authority["review"]["documents"][0]
    entry = output["files"][0]
    old_bytes = entry["bytes"]
    payload = b"REVIEW_CANARY_114231: invented permission, not the frozen review\n"
    entry.update(text=payload.decode(), bytes=len(payload), digest=hashlib.sha256(payload).hexdigest())
    output["bytes"] += len(payload) - old_bytes
    # Keep frozen tree/result identities unchanged: these are the bindings
    # the reader must check, not checksums the replacement may rewrite.


def linked_custody():
    case = fixture.ProducerCase("run")
    case.setUp()
    try:
        producer = fixture.producer
        real = producer._accepted_evidence(
            case.world.manager, case.world.jobs, case.world.authority_read,
            line_id=case.world.line_id, proposal_id=case.world.proposal_id,
            checkpoint_profile=case.checkpoint)
        changed = copy.deepcopy(real)
        storage = Path(configured_workspace_storage(case.world.manager).place)
        outside = Path(case.world.owner.root) / "review-outside-configured-store"
        outside.mkdir()
        for artifact in changed["verdict"]["review_result"]["artifacts"]:
            original = Path(artifact["locator"][len("file://"):])
            shutil.copytree(original, outside / artifact["output_name"])
        link = storage / "review-link-114231"
        link.symlink_to(outside, target_is_directory=True)
        for artifact in changed["verdict"]["review_result"]["artifacts"]:
            artifact["locator"] = "file://" + str(link / artifact["output_name"])
        with mock.patch.object(producer, "_accepted_evidence", side_effect=lambda *a, **k: copy.deepcopy(changed)):
            try:
                answer = case.compose()
                result = fixture.contract.read_bundle(answer["root"])
                return {"case": "custody_ancestor_symlink_outside_store", "published": True,
                        "outside_configured_store": not str(outside).startswith(str(storage) + "/"),
                        "materialized_files": len(result["review"]["documents"])}
            except Exception as error:
                return {"case": "custody_ancestor_symlink_outside_store", "published": False, "error": str(error)}
    finally:
        case.doCleanups()


answers = [
    reader_case("rewritten_review_with_original_frozen_identity", changed_review),
    reader_case("foreign_scope_identity", lambda account: account["scope"].update(work_id="foreign-work", test_scope=[], scope_digest="sha256:" + "f" * 64)),
    reader_case("missing_materialized_review", lambda account: account["review"].update(documents=[])),
    linked_custody(),
]
(HERE / "probe.json").write_text(json.dumps(answers, indent=2) + "\n")
print(json.dumps(answers, indent=2))
