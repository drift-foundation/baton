"""Re-run review112989's three reproductions against the second correction.

Each block performs the reviewer's own seam and records what the boundary now
answers. Nothing opens the Baton ledger; nothing writes to retained evidence.
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


# -- probe 1: the root alias, the trailing dot and the linked ancestor -------

case = fixtures.ReadBackCase()
case.setUp()
try:
    envelope = case.build()
    side = envelope["paths"][0]["candidate"]
    alias = Path(case.root) / "alias"
    alias.symlink_to(case.place, target_is_directory=True)
    held = {
        "direct_root_link": refused(contract.read_bundle, str(alias)),
        "root_link_with_dot": refused(contract.read_bundle, str(alias) + "/."),
        "blob_root_with_dot": refused(contract.bundle_blob,
                                      str(alias) + "/.", side),
        "valid_root_still_reads":
            contract.read_bundle(case.place)["envelope"] == envelope}
    report["probes"]["root_traversal"] = held
finally:
    case.doCleanups()

case = fixtures.ReadBackCase()
case.setUp()
try:
    import shutil

    envelope = case.build()
    parent = Path(case.root) / "parent"
    parent.mkdir()
    shutil.move(case.place, str(parent / "bundle"))
    linked = Path(case.root) / "linked-parent"
    linked.symlink_to(parent, target_is_directory=True)
    report["probes"]["ancestor_link"] = {
        "through_link": refused(contract.read_bundle,
                                str(linked / "bundle")),
        "by_its_own_name":
            contract.read_bundle(str(parent / "bundle"))["envelope"]
            == envelope}
finally:
    case.doCleanups()


class Harness(fixtures.ProducerCase):
    def runTest(self):
        pass


def world():
    case = Harness()
    case.setUp()
    return case


# -- probe 2: one shared blob under a scaled unique-content bound -----------

case = world()
try:
    paths = ["src/one.py", "src/two.py"]
    shared = b"12345"
    real = producer._accepted_evidence(
        case.world.manager, case.world.jobs, case.world.authority_read,
        line_id=case.world.line_id, proposal_id=case.world.proposal_id,
        checkpoint_profile=case.checkpoint)
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
    case.objects.tree(fixtures.BASE_TREE, {})
    case.objects.tree(case.world.owner.observed["tree"],
                      {one: ("100644", shared) for one in paths})
    with mock.patch.object(producer, "_accepted_evidence",
                           side_effect=lambda *a, **k: copy.deepcopy(projection)), \
            mock.patch.object(producer, "MAX_BLOB_BYTES", 8), \
            mock.patch.object(contract, "MAX_BLOB_BYTES", 8):
        answer = case.compose()
        taken = contract.read_bundle(answer["root"])
    reads = [argv for argv in case.objects.calls
             if argv[2:4] == ["cat-file", "blob"]]
    report["probes"]["shared_blob_budget"] = {
        "scaled_limit": 8,
        "unique_bytes": answer["blob_bytes"],
        "side_references": 2,
        "producer_published": True,
        "content_reads": len(reads),
        "reader_accepts": len(taken["envelope"]["paths"]) == 2}
finally:
    case.doCleanups()

# -- probe 3: the transient swap, restored before any later check -----------

case = world()
try:
    import shutil

    line = Path(case.line["line_path"])
    before = line.stat()
    observed = {}

    def transient():
        parked = Path(str(line) + "-parked")
        line.rename(parked)
        line.mkdir()
        observed["substitute"] = (line.stat().st_dev, line.stat().st_ino)
        line.rename(str(line) + "-substitute")
        parked.rename(line)

    case.objects.on_first = transient
    answer = case.compose()
    after = line.stat()
    contract.read_bundle(answer["root"])
    report["probes"]["transient_source_swap"] = {
        "substitute_identity": observed.get("substitute"),
        "line_identity": [before.st_dev, before.st_ino],
        "same_identity_before_after": os.path.samestat(before, after),
        "every_read_bound_to_the_line": all(
            one == (before.st_dev, before.st_ino)
            for one in case.objects.directories),
        "reads": len(case.objects.directories),
        "no_command_named_the_pathname": all(
            "-C" not in argv and str(line) not in argv
            for argv in case.objects.calls),
        "published": True}
finally:
    case.doCleanups()

print(json.dumps(report, indent=2))
