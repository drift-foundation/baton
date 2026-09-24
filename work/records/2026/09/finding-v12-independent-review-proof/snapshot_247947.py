"""Build and verify W239533's own manager-source snapshot.

Owner 247663 item 4. The selections bound
`/home/sl/baton-runs/single-implementation-242687/manager-source`, which is
W239528's producer snapshot and PREDATES the `correction_policy` change owner
selection 247421 made -- so a run bound to it would have no boundary to
decline the correction round with, and `held_packet` would refuse the packet it
composed. This builds the successor that carries the change.

WHY NOT `../finding-v12-single-implementation-proof/snapshot_242687.py`. It
does support `--rebuild-into` and `--claim` for exactly this, and its
refusals -- never replace a tree, never replace a manifest, a successor states
its own claim -- are the ones this follows. But `manifest_for` writes the
manifest into ITS OWN dossier, and W239528 is a closed Work whose dossier is
read-only here. Writing a W239533 manifest into it would be this Job filing its
evidence in somebody else's record. So the rules are reused and the destination
is this dossier's.

WHAT IT NEVER DOES: remove, replace or write into an existing tree. The
producer's snapshot is verified UNCHANGED as part of every build, because the
whole point of a successor is that the predecessor survives it.
"""

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
SOURCE = CHECKOUT / "v12/python"
PACKAGES = ("src/baton_v12", "tools")

# THE PRODUCER'S SNAPSHOT. Verified unchanged on every build and never written
# to. Its manifest is W239528's `MANAGER-SOURCE-242687.json`, which is that
# dossier's evidence and is only READ here.
PRODUCER = pathlib.Path("/home/sl/baton-runs/single-implementation-242687"
                        "/manager-source")
PRODUCER_MANIFEST = (HERE.parent / "finding-v12-single-implementation-proof"
                     / "MANAGER-SOURCE-242687.json")

DEFAULT = pathlib.Path("/home/sl/baton-runs/independent-review-247947"
                       "/manager-source")

# The product change this successor exists to carry, and the digest owner
# selection 247421's record binds. A snapshot that did not contain it would be
# the predecessor under a new name.
CHANGED = "tools/stage_execution.py"
CHANGED_SHA256 = \
    "6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801"


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def tree(root):
    found = {}
    for base, dirs, names in os.walk(root):
        dirs[:] = [one for one in sorted(dirs) if one != "__pycache__"]
        for name in sorted(names):
            if name.endswith(".pyc"):
                continue
            whole = os.path.join(base, name)
            found[os.path.relpath(whole, root)] = sha(whole)
    return found


def manifest_for(snapshot):
    """One manifest per snapshot, named after it, in THIS dossier."""
    return HERE / ("MANAGER-SOURCE-" + pathlib.Path(snapshot).parent.name
                   + ".json")


def producer_unchanged():
    """The predecessor, proved byte-identical to its own recorded manifest.

    Read-only: this opens W239528's manifest and W239528's tree and compares
    them. A successor whose build could not say the predecessor survived would
    be asserting the one thing the whole arrangement exists to guarantee.
    """
    if not PRODUCER_MANIFEST.exists():
        raise SystemExit(f"the producer's manifest {PRODUCER_MANIFEST} is not "
                         f"readable; this is an operational finding, not a "
                         f"reason to build without it")
    recorded = json.loads(PRODUCER_MANIFEST.read_text(encoding="utf-8"))
    files = recorded.get("files") or recorded.get("tree") or {}
    if not files:
        raise SystemExit("the producer's manifest records no files")
    if not PRODUCER.is_dir():
        raise SystemExit(f"the producer's snapshot {PRODUCER} is gone")
    held = tree(PRODUCER)
    drifted = sorted(one for one in files if held.get(one) != files[one])
    missing = sorted(one for one in files if one not in held)
    return {"manifest": str(PRODUCER_MANIFEST), "path": str(PRODUCER),
            "file_count": len(files), "drifted": drifted,
            "missing": missing, "unchanged": not drifted and not missing}


def build(snapshot, claim):
    snapshot = pathlib.Path(snapshot)
    manifest_path = manifest_for(snapshot)
    if type(claim) is not int or claim <= 0:
        raise SystemExit(f"--claim is one positive sequence; this is {claim!r}")
    # NEVER REPLACE. Both the tree and its manifest, for the reason W239528's
    # builder records: a successor that destroys evidence somebody verified is
    # the mistake the snapshot exists to avoid.
    if snapshot.exists():
        raise SystemExit(f"{snapshot} already exists; this builder never "
                         f"removes or replaces a tree. Choose another "
                         f"destination.")
    if manifest_path.exists():
        raise SystemExit(f"{manifest_path} already exists; a manifest is a "
                         f"snapshot's evidence and is never overwritten.")

    held = producer_unchanged()
    if not held["unchanged"]:
        raise SystemExit(f"the producer's snapshot has drifted from its own "
                         f"manifest and this build refuses to proceed: "
                         f"{json.dumps(held, indent=2)}")

    snapshot.mkdir(parents=True)
    for one in PACKAGES:
        shutil.copytree(SOURCE / one, snapshot / pathlib.Path(one).name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    files = tree(snapshot)
    if files.get(CHANGED) != CHANGED_SHA256:
        raise SystemExit(
            f"this successor exists to carry the correction_policy change and "
            f"{CHANGED} in it is {files.get(CHANGED)!r}, not "
            f"{CHANGED_SHA256!r}. A snapshot without the change is the "
            f"predecessor under a new name.")
    record = {
        "schema": "baton.independent-review-manager-source/1",
        "work": "W239533", "created_by_claim": claim,
        "participant": "baton.claude",
        "path": str(snapshot), "packages": list(PACKAGES),
        "file_count": len(files), "files": files,
        "carries": {CHANGED: CHANGED_SHA256,
                    "why": "the correction_policy boundary owner selection "
                           "247421 added; see OWNER-PRODUCT-CHANGE-247423.md"},
        "predecessor": held,
        "recipe": ("copied from the checkout's v12/python at build time; "
                   "no tree was removed or replaced and the producer's "
                   "snapshot was verified unchanged first"),
    }
    manifest_path.write_text(json.dumps(record, indent=2, sort_keys=True)
                             + "\n", encoding="utf-8")
    return record


def verify(snapshot):
    snapshot = pathlib.Path(snapshot)
    manifest_path = manifest_for(snapshot)
    if not manifest_path.exists():
        raise SystemExit(f"{manifest_path} does not exist; build it first")
    recorded = json.loads(manifest_path.read_text(encoding="utf-8"))
    held = tree(snapshot)
    drifted = sorted(one for one in recorded["files"]
                     if held.get(one) != recorded["files"][one])
    missing = sorted(one for one in recorded["files"] if one not in held)
    extra = sorted(one for one in held if one not in recorded["files"])
    answer = {"verified": str(snapshot), "manifest": str(manifest_path),
              "file_count": recorded["file_count"], "drifted": drifted,
              "missing": missing, "extra": extra,
              "carries_the_change": held.get(CHANGED) == CHANGED_SHA256,
              "predecessor": producer_unchanged()}
    answer["holds"] = (not drifted and not missing and not extra
                       and answer["carries_the_change"]
                       and answer["predecessor"]["unchanged"])
    return answer


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="snapshot_247947",
        description="Build or verify W239533's manager-source snapshot.")
    parser.add_argument("--into", default=str(DEFAULT))
    parser.add_argument("--claim", type=int, default=None)
    parser.add_argument("--verify", action="store_true")
    taken = parser.parse_args(argv)
    if taken.verify:
        answer = verify(taken.into)
        print(json.dumps(answer, indent=2, sort_keys=True))
        return 0 if answer["holds"] else 1
    if taken.claim is None:
        raise SystemExit("a snapshot states the claim that created it: "
                         "pass --claim <seq>")
    record = build(taken.into, taken.claim)
    print(json.dumps({one: record[one] for one in
                      ("path", "file_count", "created_by_claim", "carries",
                       "predecessor")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
