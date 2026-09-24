"""This dossier's pins and its focused witness, measured rather than estimated.

`--pins` re-reads the artifacts ASSESSMENT-249338.md selected and prints what
it found beside what was pinned. It opens no deployed store, starts nothing and
writes nothing outside this dossier.
"""
import argparse
import hashlib
import io
import json
import os
import pathlib
import time
import unittest

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
SNAPSHOT = pathlib.Path(
    "/home/sl/baton-runs/independent-review-247947/manager-source")
RUNTIME = pathlib.Path(
    "/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro")
PINNED = {
    "manager_source_files": 106,
    "manager_source_manifest_sha256": "ab5e5b0befbb77f6e96a94e76d0d8b6e01935beb2e7f48090d0d3fc13fae1cd5",
    "stage_execution_sha256":
        "6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801",
    "runtime_executable_sha256":
        "04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a",
}
OWNED = ("two_jobs.py", "test_two_jobs.py", "align_template.py",
         "add_roundtrip.py", "apply_249551.py", "apply_249551_tests.py",
         "apply_249551_root.py", "two_job_supervisor.py",
         "ADOPTION-247941.md",
         "CONTINUITY-247941.md", "SELECTIONS-247941.json", "verify_247941.py")
MODULES = ("test_two_jobs",)


# WHERE THE DISPOSABLE FIXTURE ROOT MAY LIVE, and why it is not folklore.
#
# Review 2026-09-23T17:25:40Z ran the roundtrip cases with a fixture root the
# product refused: `held_configuration` calls any mutable state inside "the
# checkout" a policy denial, and the checkout it detects is derived from the
# SOURCE THAT IMPORTED IT. Bound to the pinned snapshot under
# `/home/sl/baton-runs/...`, that makes `/home/sl/baton-runs` the checkout --
# so a fixture root under it is refused even though it is nowhere near the
# repository.
#
# The guard is right and is not weakened here. What this names is the setup
# that satisfies it: a DISK-BACKED directory outside both the repository and
# the pinned source's own root.
FIXTURE_ROOT_VARIABLE = "BATON_V12_DISK_ROOT"
FIXTURE_ROOT = "/var/tmp/baton-w247941"


def fixture_root_setup():
    """The exact command that prepares a usable disposable root."""
    return (f"mkdir -p {FIXTURE_ROOT} && "
            f"{FIXTURE_ROOT_VARIABLE}={FIXTURE_ROOT}")


def held_fixture_root(place=None):
    """Why a given fixture root will or will not serve. READ ONLY."""
    import os
    place = place or os.environ.get(FIXTURE_ROOT_VARIABLE)
    if not place:
        return [f"{FIXTURE_ROOT_VARIABLE} is unset; the suite would choose a "
                f"root for itself and may choose one the product refuses. "
                f"Use: {fixture_root_setup()}"]
    held = []
    whole = os.path.realpath(place)
    for what, root in (("this repository", str(CHECKOUT)),
                       ("the pinned source's own root",
                        os.path.dirname(str(SNAPSHOT)))):
        root = os.path.realpath(root)
        if os.path.commonpath([whole, root]) == root:
            held.append(f"{whole} is inside {what} at {root}; "
                        f"`held_configuration` denies mutable state there. "
                        f"Use: {fixture_root_setup()}")
    return held


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def source_files(root):
    """Every SOURCE file in the snapshot, compiled caches excluded.

    W247941, claim 255973. The snapshot held 193 files where this pins 106,
    and the extra 87 are `__pycache__` byte-code written into it at
    2026-09-24T04:27 by a run that imported from it -- importing from a
    directory writes caches into that directory. No source file was touched:
    none has an mtime later than the pin, the 106 remaining are byte-identical
    to the working tree except the three this Work owns and has edited, and
    with the caches excluded the manifest below reproduces the pinned
    `ab5e5b0b…` EXACTLY.

    So the count and the digest are taken over source, which is what they were
    always meant to describe. Nothing was deleted from the snapshot to make
    this true -- removing files from preserved material is not this Work's to
    do, and a digest made true by tidying the evidence would not be a digest.

    THE BOUNDARY CHANGED AND SAYING "NOTHING IS WEAKENED" WAS TOO BROAD.
    Review 2026-09-24T10:35:28Z [R3], and it is right. What this attests is
    SOURCE IDENTITY: the same 106 files, still moving on a changed byte, a
    rename or a swap. What it no longer attests is every byte Python may
    EXECUTE from this directory, because the former all-file boundary covered
    the caches and this does not. `PYTHONDONTWRITEBYTECODE` and `-B` prevent
    WRITING byte-code; they do not prevent LOADING an existing `.pyc`, so a
    cache-contaminated import root could still execute bytes no source digest
    here describes.

    THAT IS AN OPEN ITEM AND NOT A CLOSED ONE. The new reviewable snapshot
    owes a clean or separately verified import-cache boundary, so unreviewed
    cached code cannot stand in for reviewed source, with its own focused
    verifier cases. This function is the source half of that proof and is
    deliberately not the whole of it.
    """
    return [place for place in root.rglob("*")
            if place.is_file() and "__pycache__" not in place.parts]


def manifest_digest(root):
    """ONE digest over every source file in the snapshot, paths included.

    Review 2026-09-23T17:12:02Z R5: counting 106 files says nothing about
    their CONTENT, and the count is the one property a drifted snapshot is
    most likely to keep. This hashes the sorted (relative path, file digest)
    pairs, so a changed byte, a renamed file or a swapped pair all move it.
    """
    reading = hashlib.sha256()
    for one in sorted(source_files(root)):
        reading.update(str(one.relative_to(root)).encode("utf-8"))
        reading.update(b"\0")
        reading.update(sha(one).encode("ascii"))
        reading.update(b"\n")
    return reading.hexdigest()


def pins():
    """What the selected artifacts hash to NOW, beside what was pinned."""
    held = {"pinned": dict(PINNED), "found": {}}
    if SNAPSHOT.is_dir():
        held["found"]["manager_source_files"] = len(source_files(SNAPSHOT))
        place = SNAPSHOT / "tools" / "stage_execution.py"
        held["found"]["stage_execution_sha256"] = (
            sha(place) if place.is_file() else None)
        held["found"]["manager_source_manifest_sha256"] = manifest_digest(
            SNAPSHOT)
    else:                                                    # pragma: no cover
        held["found"]["manager_source"] = f"absent at {SNAPSHOT}"
    executable = RUNTIME / "baton-v12-stack"
    held["found"]["runtime_executable_sha256"] = (
        sha(executable) if executable.is_file() else f"absent at {executable}")
    held["checkout_stage_execution_sha256"] = sha(
        CHECKOUT / "v12/python/tools/stage_execution.py")
    held["fixture_root"] = held_fixture_root()
    held["agree"] = all(held["found"].get(name) == value
                        for name, value in PINNED.items())
    return held


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pins", action="store_true")
    parser.add_argument("--claim", type=int, default=249364)
    # THE RECEIPT IS NUMBERED BY THE CALLER. It was hardcoded to 17, so a
    # later run silently overwrote the receipt an earlier claim had cited
    # as its evidence.
    parser.add_argument("--receipt", type=int, default=17)
    chosen = parser.parse_args(argv)
    if chosen.pins:
        held = pins()
        print(json.dumps(held, indent=2, sort_keys=True))
        # IT FAILS CLOSED. The first version printed a disagreement and exited
        # 0, so an operator following step 1 of the packet would have seen a
        # drifted artifact and a success status in the same breath.
        return 0 if held["agree"] else 1
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(
        [loader.loadTestsFromName(one) for one in MODULES])
    stream = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    elapsed = time.perf_counter() - started
    log = f"verification-{chosen.receipt}.log"
    (HERE / log).write_text(stream.getvalue(), encoding="utf-8")
    receipt = {
        "schema": "baton.v12-adoption-gate-verification/1",
        "work": "W247941", "claim": chosen.claim,
        "participant": "baton.claude",
        "modules": list(MODULES),
        "checks": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "measured_seconds": elapsed,
        "python": os.sys.version.split()[0],
        "owned": {name: sha(HERE / name) for name in OWNED},
        "pins": pins(),
        "log": log,
        "note": "the two-Job arrangement held by the product's own validator "
                "and driven through W130224's accepted two-Job fixture on "
                "disposable stores. No container, image, engine, live "
                "provider, network, credential, deployed store or deployment "
                "change.",
    }
    (HERE / f"verification-{chosen.receipt}.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({one: receipt[one] for one in
                      ("checks", "failures", "errors", "measured_seconds")},
                     indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
