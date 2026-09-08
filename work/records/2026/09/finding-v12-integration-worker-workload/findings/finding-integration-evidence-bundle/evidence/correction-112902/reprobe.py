"""Re-run review112857's three reproductions against the corrected sources.

Each block performs the reviewer's own seam and asserts the boundary now
refuses. Nothing here opens the Baton ledger and nothing writes to the
reviewer's retained evidence.
"""
import copy
import json
import os
import sys
from pathlib import Path
from unittest import mock

REPO = Path("/home/sl/src/baton")
sys.path[:0] = [str(REPO / "v12/python"), str(REPO / "v12/python/src")]
from tests.tools import test_integration_bundle as fixtures     # noqa: E402
from baton_v12.contracts import ContractRefusal, digest         # noqa: E402

producer, contract = fixtures.producer, fixtures.contract
report = {"probes": {}}


def refused(action, *operands, **named):
    try:
        action(*operands, **named)
    except (ContractRefusal, contract.BundleRefusal) as caught:
        return f"{type(caught).__name__}: {caught}"
    return None


# -- probe 1: symlinked ancestors -------------------------------------------

case = fixtures.ReadBackCase()
case.setUp()
try:
    envelope = case.build()
    held = {}
    original = Path(case.place) / "evidence"
    outside = Path(case.root) / "outside-evidence"
    original.rename(outside)
    original.symlink_to(outside, target_is_directory=True)
    held["evidence_directory"] = refused(contract.read_bundle, case.place)

    blobs = Path(case.place) / "blobs"
    outside_blobs = Path(case.root) / "outside-blobs"
    blobs.rename(outside_blobs)
    blobs.symlink_to(outside_blobs, target_is_directory=True)
    held["blob_directory"] = refused(contract.bundle_blob, case.place,
                                     envelope["paths"][0]["candidate"])

    linked = Path(case.root) / "linked-root"
    linked.symlink_to(case.place, target_is_directory=True)
    held["root_link"] = refused(contract.read_bundle, str(linked))
    report["probes"]["intermediate_links"] = held
finally:
    case.doCleanups()

# -- probes 2 and 3: the real admitted world --------------------------------


class Harness(fixtures.ProducerCase):
    def runTest(self):
        pass


def world():
    case = Harness()
    case.setUp()
    return case


# The line directory is replaced at the first extraction query.
case = world()
try:
    import shutil

    def replace():
        place = case.line["line_path"]
        shutil.move(place, place + "-moved")
        os.mkdir(place)

    before = os.stat(case.line["line_path"])
    case.objects.on_first = replace
    answer = refused(case.compose)
    after = os.stat(case.line["line_path"])
    report["probes"]["line_replaced_during_extraction"] = {
        "initial_identity": [before.st_dev, before.st_ino],
        "replacement_identity": [after.st_dev, after.st_ino],
        "refusal": answer,
        "destination_exists": os.path.exists(case.destination),
        "staging_exists": os.path.exists(case.destination + ".incomplete")}
finally:
    case.doCleanups()

# 252 two-sided edits: the exact bundle that used to publish 513 files.
case = world()
try:
    real = producer._accepted_evidence(
        case.world.manager, case.world.jobs, case.world.authority_read,
        line_id=case.world.line_id, proposal_id=case.world.proposal_id,
        checkpoint_profile=case.checkpoint)
    paths = sorted(f"src/{index:04d}.py" for index in range(252))
    held_digest = digest(paths)
    evidence = dict(real["checkpoint"]["evidence"], paths=paths,
                    path_set_digest=held_digest)
    projection = {
        "account": dict(real["account"], path_set_digest=held_digest),
        "line": real["line"],
        "checkpoint": dict(real["checkpoint"], evidence=evidence),
        "documents": dict(
            real["documents"],
            **{"checkpoint.json": dict(real["documents"]["checkpoint.json"],
                                       evidence=evidence,
                                       path_set_digest=held_digest)})}
    case.objects.tree(fixtures.BASE_TREE,
                      {one: ("100644", f"base {one}\n".encode())
                       for one in paths})
    case.objects.tree(case.world.owner.observed["tree"],
                      {one: ("100644", f"head {one}\n".encode())
                       for one in paths})
    with mock.patch.object(producer, "_accepted_evidence",
                           side_effect=lambda *a, **k: copy.deepcopy(projection)):
        answer = refused(case.compose)
    report["probes"]["manifest_limit"] = {
        "paths": 252,
        "would_be_files": producer.FIXED_FILES + 2 * 252,
        "max_paths": producer.MAX_PATHS,
        "max_bundle_files": producer.MAX_BUNDLE_FILES,
        "refusal": answer,
        "destination_exists": os.path.exists(case.destination),
        "staging_exists": os.path.exists(case.destination + ".incomplete")}
finally:
    case.doCleanups()

# And the exact maximum still publishes and measures.
case = world()
try:
    real = producer._accepted_evidence(
        case.world.manager, case.world.jobs, case.world.authority_read,
        line_id=case.world.line_id, proposal_id=case.world.proposal_id,
        checkpoint_profile=case.checkpoint)
    paths = sorted(f"src/{index:04d}.py" for index in range(producer.MAX_PATHS))
    held_digest = digest(paths)
    evidence = dict(real["checkpoint"]["evidence"], paths=paths,
                    path_set_digest=held_digest)
    projection = {
        "account": dict(real["account"], path_set_digest=held_digest),
        "line": real["line"],
        "checkpoint": dict(real["checkpoint"], evidence=evidence),
        "documents": dict(
            real["documents"],
            **{"checkpoint.json": dict(real["documents"]["checkpoint.json"],
                                       evidence=evidence,
                                       path_set_digest=held_digest)})}
    case.objects.tree(fixtures.BASE_TREE,
                      {one: ("100644", f"base {one}\n".encode())
                       for one in paths})
    case.objects.tree(case.world.owner.observed["tree"],
                      {one: ("100644", f"head {one}\n".encode())
                       for one in paths})
    with mock.patch.object(producer, "_accepted_evidence",
                           side_effect=lambda *a, **k: copy.deepcopy(projection)):
        answer = case.compose()
    taken = contract.read_bundle(answer["root"])
    report["probes"]["exact_maximum"] = {
        "paths": producer.MAX_PATHS,
        "manifest_files": len(answer["manifest"]),
        "digest_matches": answer["bundle_digest"] == digest(answer["manifest"]),
        "consumer_accepted": len(taken["envelope"]["paths"]) == producer.MAX_PATHS}
finally:
    case.doCleanups()

print(json.dumps(report, indent=2))
