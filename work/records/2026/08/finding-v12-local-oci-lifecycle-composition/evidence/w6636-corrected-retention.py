"""W6636 review reproduction, re-run against the CORRECTION.

This is the reviewer's own `w6636-review-retention-noop.py` with the assertion
the required correction inverts, and nothing else. Their file is kept exactly
as produced.

Run from v12/python with:

    env PYTHONPATH=src:. python3 -B ../../work/records/2026/08/finding-v12-local-oci-lifecycle-composition/evidence/w6636-corrected-retention.py

WHY IT CANNOT BE RUN UNCHANGED, and the reason is not only the fix. Their file
builds an adapter with NO declared outputs and then asks it to discard
`attempt-1:proposal`. The correction refuses that, because an artifact this
assignment never declared is one of the three identities the review required be
refused rather than resolved -- so their script now raises where it asserted a
surviving artifact.

WHAT IS MEASURED IS UNCHANGED, and the review's argument is the one that
settles it: I recorded the no-op as an unspecified retention semantics, and it
is not unspecified. The manager's own settlement rule says `complete` means
nothing was kept, so reporting `complete` over surviving custody bytes is a
FALSE CLEAN ENDING. W6629 already decided the boundary.

Exit 0 means every one holds.
"""

import os
import tempfile

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager.oci import OciAdapter


ASSIGNMENT = {"work_ref": {"authority_uuid": "fe" * 16,
                           "work_id": "fefefefe-W1"},
              "participant": "baton.claude", "generation": 1}
DIGEST = "sha256:" + "5" * 64
IDENTITY = {"image_digest": "sha256:" + "0" * 64,
            "profile_digest": "sha256:" + "1" * 64,
            "policy_digest": "sha256:" + "2" * 64,
            "adapter_digest": "sha256:" + "3" * 64}


def declaration(name="proposal", path="out"):
    return {"name": name, "type": "directory-result", "path": path,
            "required": True,
            "constraints": {"max_bytes": 1 << 20, "max_entries": 100,
                            "allowed_media_types": ["text/plain"],
                            "link_policy": "forbid",
                            "validator_digest": None}}


def built(home, outputs):
    return OciAdapter(
        "docker", lambda _argv: {"status": 0, "stdout": "", "stderr": ""},
        identity=dict(IDENTITY),
        assignment_roots={"inputs": os.path.join(home, "inputs"),
                          "workspace": os.path.join(home, "workspace")},
        posture="execution", outputs=outputs,
        input_manifest_digest=DIGEST)


def custodied(adapter, home, names, attempt="attempt-1"):
    """Bytes in the adapter's own custody, as a collection would leave them."""
    made = []
    for name in names:
        place = os.path.join(adapter._custody(attempt), name)
        os.makedirs(place, exist_ok=True)
        with open(os.path.join(place, "a.txt"), "wb") as handle:
            handle.write(b"one")
        made.append(place)
    return made


def command(attempt="attempt-1", ids=("attempt-1:proposal",),
            disposition="discard-after-intake"):
    return {"assignment_ref": dict(ASSIGNMENT),
            "runtime_attempt_id": attempt,
            "artifact_ids": list(ids), "disposition": disposition,
            "retention_policy_digest": DIGEST,
            "operation": {"operation_id": "output.retain:1",
                          "signature_digest": DIGEST}}


def a_discard_actually_discards():
    with tempfile.TemporaryDirectory(prefix="w6636-retention-") as home:
        adapter = built(home, [declaration()])
        place, = custodied(adapter, home, ["proposal"])
        answer = adapter.retain(command())
        print("discard ->", answer, "| still exists:",
              os.path.exists(place))
        assert answer["discarded"] == ["proposal"]
        assert not os.path.exists(place), "the discarded artifact survived"
        return True


def keeping_dispositions_keep():
    for disposition in ("retain", "quarantine"):
        with tempfile.TemporaryDirectory(prefix="w6636-retention-") as home:
            adapter = built(home, [declaration()])
            place, = custodied(adapter, home, ["proposal"])
            answer = adapter.retain(command(disposition=disposition))
            assert answer["discarded"] == []
            assert os.path.isdir(place), disposition
    print("retain and quarantine keep the bytes")
    return True


def only_the_named_artifact_goes():
    with tempfile.TemporaryDirectory(prefix="w6636-retention-") as home:
        adapter = built(home, [declaration(),
                               declaration("evidence", "second")])
        kept, = custodied(adapter, home, ["evidence"])
        gone, = custodied(adapter, home, ["proposal"])
        adapter.retain(command())
        print("subset ->", "proposal gone:", not os.path.exists(gone),
              "| evidence kept:", os.path.isdir(kept))
        assert not os.path.exists(gone)
        assert os.path.isdir(kept)
        return True


def an_exact_retry_is_idempotent():
    with tempfile.TemporaryDirectory(prefix="w6636-retention-") as home:
        adapter = built(home, [declaration()])
        place, = custodied(adapter, home, ["proposal"])
        adapter.retain(command())
        again = adapter.retain(command())
        print("retry ->", again)
        assert again["discarded"] == ["proposal"]
        assert not os.path.exists(place)
        return True


def an_unowned_identity_is_refused_rather_than_resolved():
    """THE ONE THAT MATTERS. The tree is derived from `attempt:name`, so a
    caller cannot name a path, reach another attempt's material, or discard
    something this assignment never declared."""
    refusals = {}
    for invented in ("attempt-2:proposal", "attempt-1:invented", "proposal",
                     "../../etc", "attempt-1:../secret"):
        with tempfile.TemporaryDirectory(prefix="w6636-retention-") as home:
            adapter = built(home, [declaration()])
            place, = custodied(adapter, home, ["proposal"])
            try:
                adapter.retain(command(ids=[invented]))
            except ContractRefusal as refusal:
                refusals[invented] = refusal.message[:48]
            else:
                raise AssertionError(f"{invented} was resolved")
            assert os.path.isdir(place), invented
    print("refused, and nothing touched:")
    for one, why in refusals.items():
        print("   ", one, "->", why)
    return True


def an_unknown_disposition_never_reaches_the_filesystem():
    """Re-review [P1]: everything that was not a KEEP fell through to the
    discard, so a typo removed the material and reported success. An adapter
    boundary that owns a destructive command may not make unknown mean
    delete."""
    seen = {}
    for invented in ("not-a-retention-disposition", "discard", "keep",
                     "Retain"):
        with tempfile.TemporaryDirectory(prefix="w6636-retention-") as home:
            adapter = built(home, [declaration()])
            place, = custodied(adapter, home, ["proposal"])
            try:
                adapter.retain(command(disposition=invented))
            except ContractRefusal as refusal:
                seen[invented] = refusal.message[:44]
            else:
                raise AssertionError(f"{invented} was enacted")
            assert os.path.isdir(place), invented
    print("unknown dispositions refused, custody untouched:")
    for one, why in seen.items():
        print("   ", one, "->", why)
    return True


def a_keep_over_absent_custody_refuses():
    """Re-review [P0]: the keep branch returned WITHOUT LOOKING, so custody
    that vanished between intake and retention was journalled as kept -- and
    cleanup then derived `retained`, whose whole meaning is that the material
    is still there.

    ONE FRESH TREE PER DISPOSITION. A loop over one fixture would have removed
    the tree on the first pass and then checked the second against custody
    that was already gone and no longer collected -- measured, in the focused
    suite, where exactly that made the second half vacuous.
    """
    for disposition in ("retain", "quarantine"):
        with tempfile.TemporaryDirectory(prefix="w6636-retention-") as home:
            adapter = built(home, [declaration()])
            place, = custodied(adapter, home, ["proposal"])
            os.remove(os.path.join(place, "a.txt"))
            os.rmdir(place)
            try:
                adapter.retain(command(disposition=disposition))
            except ContractRefusal as refusal:
                print(f"{disposition} over absent custody ->",
                      refusal.message[:60])
            else:
                raise AssertionError(
                    f"{disposition} was journalled over absent material")
    return True


if __name__ == "__main__":
    ok = [a_discard_actually_discards(),
          keeping_dispositions_keep(),
          only_the_named_artifact_goes(),
          an_exact_retry_is_idempotent(),
          an_unowned_identity_is_refused_rather_than_resolved(),
          an_unknown_disposition_never_reaches_the_filesystem(),
          a_keep_over_absent_custody_refuses()]
    print("OK" if all(ok) else "UNSAFE")
    raise SystemExit(0 if all(ok) else 1)
