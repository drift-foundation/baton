"""Prepare the successor manager-source snapshot, and manifest it.

Review 2026-09-22T23:53:34Z R1: `OPERATOR-FAILURE-242687.md` bound
`/home/sl/baton-runs/managed-correction-236087/manager-source`, which is a
snapshot taken under W236087 and therefore holds the PRE-CORRECTION
`review_driver.py` and `stage_execution.py`. The documented command would have
imported the uncorrected code and reproduced the stall it exists to disprove.

THE OLD SNAPSHOT IS PRESERVED AND NOT TOUCHED. Overwriting it would destroy the
bytes W236087's own packet is bound to, and the reviewer says so explicitly:
"overwriting the preserved old source is not the remedy". This writes a SECOND
snapshot beside it.

THE LAYOUT IS FLAT, like the one it succeeds: `baton_v12/` and `tools/` at the
root, so one `PYTHONPATH` entry is enough. The checkout nests them differently
(`v12/python/src/baton_v12`, `v12/python/tools`), which is exactly why a
snapshot exists at all.

IT COPIES AND VERIFIES; IT INSTALLS NOTHING. No store is opened, no container
starts, no deployment is changed, and the two accepted product digests are
checked against the snapshot after the copy rather than assumed from the copy
having happened.
"""
import hashlib
import json
import os
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
PYTHON = CHECKOUT / "v12" / "python"
ORIGINAL = pathlib.Path(
    "/home/sl/baton-runs/single-implementation-242687/manager-source")
SNAPSHOT = ORIGINAL
PRESERVED = pathlib.Path(
    "/home/sl/baton-runs/managed-correction-236087/manager-source")

# (source in the checkout, name in the flat snapshot)
PACKAGES = (("src/baton_v12", "baton_v12"), ("tools", "tools"))

# THE TWO FILES THIS SNAPSHOT EXISTS FOR, and the bytes independent review
# accepted. Checked against the snapshot AFTER the copy: a copy that ran is not
# a copy that landed.
ACCEPTED = {
    "baton_v12/job_manager/review_driver.py":
        "9a8a4a8193ff7b1c709c184dee3ba43a1b1e16e60891dcf31277279d2c220ae4",
    "tools/stage_execution.py":
        "ebc9be29d2bd23cf129afe33943f5336832df2ef24256c724708004220032896",
}
# And what the PRESERVED snapshot holds for the same two, which is why a second
# snapshot was needed.
SUPERSEDED = {
    "baton_v12/job_manager/review_driver.py":
        "b5b22535ef105f786aa74f61ff894614a1e91bb8e2739f1051151fb893ebe10c",
    "tools/stage_execution.py":
        "33c780916a115890767bb79cc3a2dcedc6ec588fb1da08e95490cd7897cd6e81",
}


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
    """One manifest per snapshot, named after it.

    REVIEW 2026-09-23T00:50:59Z R2. `--rebuild-into` used to change only the
    destination tree and still write the FIXED `MANAGER-SOURCE-242687.json`,
    so building a successor replaced the accepted predecessor's manifest --
    with a new path, new bytes and the old claim metadata -- and the default
    `--verify` then checked the old tree against the new manifest. A
    successor that destroys its predecessor's evidence is the same mistake
    the snapshot itself was created to avoid.

    So the manifest follows the snapshot. The original keeps its historical
    name; anything else is `MANAGER-SOURCE-<directory name>.json`.
    """
    if pathlib.Path(snapshot) == ORIGINAL:
        return HERE / "MANAGER-SOURCE-242687.json"
    return HERE / ("MANAGER-SOURCE-" + pathlib.Path(snapshot).parent.name
                   + ".json")


# THE CLAIM THAT CREATED THE ORIGINAL. It is history and is never rewritten;
# this exists so the default build replays its own provenance exactly while any
# SUCCESSOR has to state its own.
ORIGINAL_CLAIM = 242906


def main(snapshot=None, claim=None):
    # IT REFUSES AN EXISTING DESTINATION RATHER THAN REPLACING IT. Review
    # 2026-09-23T00:06:24Z recorded this as a builder finding: the first
    # version deleted its destination before copying, so re-running it would
    # have destroyed the very snapshot independent review had just verified
    # and bound -- and a reviewer had to tell an operator "do NOT rerun this".
    # A builder whose safety depends on nobody running it twice is not safe.
    #
    # `--rebuild-into <path>` is the way to make another one, and it refuses
    # the same way. Nothing here ever removes a tree.
    snapshot = ORIGINAL if snapshot is None else pathlib.Path(snapshot)
    manifest_path = manifest_for(snapshot)
    # TRUTHFUL CREATION PROVENANCE. Review 2026-09-23T01:02:06Z R2: the CLI
    # called this with the original's claim for every build, so a successor
    # created under a different assignment still recorded 242906. A manifest
    # naming the wrong episode is worse than one naming none: it reads as
    # evidence somebody produced under review that nobody did.
    #
    # THE ORIGINAL REPLAYS ITS OWN; a successor must state its own.
    if claim is None:
        if snapshot != ORIGINAL:
            raise SystemExit(
                "a successor snapshot must state the claim that created it: "
                "pass --claim <seq>. The original's claim is its own history "
                "and is never borrowed.")
        claim = ORIGINAL_CLAIM
    if type(claim) is not int or claim <= 0:
        raise SystemExit(f"--claim is one positive sequence; this is {claim!r}")
    if snapshot.exists():
        raise SystemExit(
            f"{snapshot} already exists and this program never replaces a "
            f"snapshot: an existing one may be bound by a reviewed packet. "
            f"Verify it with `--verify`, or build a new one somewhere else "
            f"with `--rebuild-into <path>`.")
    # AND NEITHER IS ITS MANIFEST REPLACED. R2: this is the evidence a
    # reviewer bound, and a successor that overwrote it would leave nothing
    # to compare against.
    if manifest_path.exists():
        raise SystemExit(
            f"{manifest_path} already exists and this program never replaces "
            f"a manifest: it is the evidence an earlier snapshot was accepted "
            f"on. Choose a `--rebuild-into` directory whose name is not "
            f"already manifested.")
    snapshot.mkdir(parents=True)
    for source, name in PACKAGES:
        shutil.copytree(PYTHON / source, snapshot / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    held = tree(snapshot)
    for name, expected in sorted(ACCEPTED.items()):
        found = held.get(name)
        if found != expected:
            raise SystemExit(
                f"the snapshot's {name} is {found!r} and independent review "
                f"accepted {expected!r}; the snapshot does not carry the "
                f"corrected bytes and must not be bound")
    # AND THE OLD ONE IS STILL THE OLD ONE. A successor that quietly became
    # the predecessor would destroy the evidence this correction rests on.
    for name, expected in sorted(SUPERSEDED.items()):
        found = sha(PRESERVED / name)
        if found != expected:
            raise SystemExit(
                f"the PRESERVED snapshot's {name} is {found!r} rather than "
                f"{expected!r}; it must not have been written to")

    manifest = {
        "schema": "baton.single-implementation-manager-source/1",
        "work": "W239528", "claim": claim, "participant": "baton.claude",
        "created_by_claim": claim,
        # THE RECIPE is this program and its accepted operands; the CREATION
        # is the episode that ran it. Distinguishing them is what R2 asks for:
        # a successor shares the recipe and does not share the authorship.
        "recipe": {"program": pathlib.Path(__file__).name,
                   "original_claim": ORIGINAL_CLAIM,
                   "original_path": str(ORIGINAL)},
        "path": str(snapshot),
        "packages": ["baton_v12", "tools"],
        "layout": "flat -- one PYTHONPATH entry is the whole import path",
        "file_count": len(held),
        "files": held,
        "accepted_product_bytes": ACCEPTED,
        "supersedes": {
            "path": str(PRESERVED),
            "why": ("that snapshot was taken under W236087 and holds the "
                    "PRE-CORRECTION bytes below; review 2026-09-22T23:53:34Z "
                    "R1 found the failure command bound it"),
            "files": SUPERSEDED,
            "preserved": True,
        },
        "built_from": str(PYTHON),
        "not_done": ("no store opened, no container started, no deployment "
                     "changed, no image rebuilt -- these are host-side "
                     "modules and the worker image is unaffected"),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(json.dumps({"path": str(snapshot), "manifest": str(manifest_path),
                      "file_count": len(held), "accepted": ACCEPTED},
                     indent=2, sort_keys=True))
    return 0


def verify(snapshot=None):
    """Re-check ONE snapshot against ITS OWN manifest and the accepted bytes.

    R2: the pair travels together. Verifying a tree against another tree's
    manifest is how a replaced manifest went unnoticed.
    """
    snapshot = ORIGINAL if snapshot is None else pathlib.Path(snapshot)
    manifest_path = manifest_for(snapshot)
    if not manifest_path.exists():
        raise SystemExit(f"{snapshot} has no manifest at {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["path"] != str(snapshot):
        raise SystemExit(f"{manifest_path} manifests {manifest['path']!r}, "
                         f"not {str(snapshot)!r}")
    held = tree(snapshot)
    if held != manifest["files"]:
        raise SystemExit("the snapshot no longer matches its manifest")
    for name, expected in sorted(ACCEPTED.items()):
        if held.get(name) != expected:
            raise SystemExit(f"the snapshot's {name} is not the accepted byte")
    for name, expected in sorted(SUPERSEDED.items()):
        if sha(PRESERVED / name) != expected:
            raise SystemExit(f"the preserved snapshot's {name} moved")
    print(json.dumps({"verified": str(snapshot),
                      "manifest": str(manifest_path),
                      "file_count": len(held)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    import sys

    chosen, claim = None, None
    if "--rebuild-into" in sys.argv:
        chosen = sys.argv[sys.argv.index("--rebuild-into") + 1]
    if "--claim" in sys.argv:
        held = sys.argv[sys.argv.index("--claim") + 1]
        if not held.isdigit():
            raise SystemExit(f"--claim is one positive sequence; "
                             f"this is {held!r}")
        claim = int(held)
    if "--verify" in sys.argv:
        raise SystemExit(verify(chosen))
    raise SystemExit(main(chosen, claim))
