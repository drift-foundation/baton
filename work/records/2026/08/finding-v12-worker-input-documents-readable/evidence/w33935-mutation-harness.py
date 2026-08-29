"""W33935 — the corrected delivery, MEASURED BY REMOVAL.

Each mutation puts one half of the defect back into production source and
requires the case that claims to establish the correction to FAIL.  Two halves,
because the defect had two: the MODE was owner-only, and the mode was
REQUESTED at creation rather than established on the descriptor, so a
restrictive umask authored the owner-only file even once the constant was
right.  A suite that caught only the first would leave the second free to
return on a host with a different umask.

It rewrites source in place and restores it, printing the before/after digest
so the restoration is checked rather than asserted.  No Git history or index is
touched.

Run from `v12/python`: `PYTHONPATH=src python3 <this file>`.
"""

import hashlib
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path("/home/sl/src/baton")
WORKSPACES = REPO / "v12/python/src/baton_v12/worker_manager/workspaces.py"
SUITE = "tests.manager.test_input_delivery"

MUTATIONS = [
    ("the delivered mode is owner-only again",
     WORKSPACES,
     "READ_ONLY_FILE = 0o444",
     "READ_ONLY_FILE = 0o400",
     f"{SUITE}.DockerDelivery.test_the_worker_identity_reads_both_delivered_documents"),

    ("...and the daemon-free half sees it too",
     WORKSPACES,
     "READ_ONLY_FILE = 0o444",
     "READ_ONLY_FILE = 0o400",
     f"{SUITE}.TheModeIsEstablishedRatherThanRequested"),

    ("...and the two components stop agreeing",
     WORKSPACES,
     "READ_ONLY_FILE = 0o444",
     "READ_ONLY_FILE = 0o400",
     f"{SUITE}.DockerDelivery.test_the_launch_document_and_the_input_pair_agree_on_the_mode"),

    # CORRECTED.  Review [P0]: this changed a constant PRODUCTION CODE NEVER
    # READ and reran a bit-value assertion, so it measured no delivered
    # directory behaviour at all and the 6-of-6 result overclaimed one guard.
    # The constant is now applied, so these three mutations move the delivery.
    # RE-ANCHORED: the parent freeze now follows the root freeze, so the
    # two lines are adjacent and the old anchor no longer matches.
    ("the input root is never frozen at all",
     WORKSPACES,
     '''    os.chmod(root, READ_ONLY_DIR)''',
     '''    pass''',
     f"{SUITE}.TheInputRootIsFrozenAndNotOnlyItsFiles.test_the_frozen_root_denies_create_unlink_rename_and_replacement"),

    ("the root is frozen owner-only, so the worker cannot traverse it",
     WORKSPACES,
     "READ_ONLY_DIR = 0o555",
     "READ_ONLY_DIR = 0o500",
     f"{SUITE}.DockerDelivery.test_the_worker_identity_reads_both_delivered_documents"),

    ("the freeze runs BEFORE the second document is installed",
     WORKSPACES,
     '''        written.append(_write_read_only(place, canonical_bytes(owned), name))''',
     '''        written.append(_write_read_only(place, canonical_bytes(owned), name))
        os.chmod(root, READ_ONLY_DIR)''',
     f"{SUITE}.TheInputRootIsFrozenAndNotOnlyItsFiles"),

    # RE-TARGETED, and the first aim was wrong rather than the case.  It
    # removed the chmod in `_remove`'s SUBDIRECTORY branch, and that line is
    # not what thaws a frozen root holding files: the walk reaches the root
    # as `current` first and the files loop thaws it there.  Mutating a line
    # that protects nothing measures nothing, which is the same defect this
    # review found in the constant.
    # RE-ANCHORED AGAIN.  The thaw moved OUT of the files loop when the home
    # was frozen: a directory holding only directories never reached that
    # loop, so `rmdir` on its children was denied by its own mode.  The
    # mutation is the removal of the thaw wherever it now lives.
    ("cleanup cannot remove what it froze",
     WORKSPACES,
     '''        os.chmod(current, 0o700)
        for name in files:''',
     '''        for name in files:''',
     f"{SUITE}.TheRootsOwnENTRYIsFrozenToo.test_cleanup_reaches_exactly_one_frozen_home"),

    # ---------------------------------------------------------------------
    # Re-review [P0]: the parent boundary that owns the `inputs` ENTRY.
    # Measured by removing the freeze, not by moving a constant.
    # ---------------------------------------------------------------------
    ("the home is never frozen, so the root entry stays replaceable",
     WORKSPACES,
     '''    os.chmod(os.path.dirname(root.rstrip("/")), READ_ONLY_DIR)''',
     '''    pass''',
     f"{SUITE}.TheRootsOwnENTRYIsFrozenToo.test_the_root_entry_itself_cannot_be_renamed_or_replaced"),

    ("the home is frozen before its later siblings are provisioned",
     WORKSPACES,
     '''    for name in HOME_ENTRIES:''',
     '''    for name in ROOT_NAMES:''',
     f"{SUITE}.TheRootsOwnENTRYIsFrozenToo.test_what_the_frozen_home_still_permits"),

    ("the mode is REQUESTED at creation instead of established",
     WORKSPACES,
     '''        os.fsync(handle)
        os.fchmod(handle, READ_ONLY_FILE)''',
     '''        os.fsync(handle)''',
     f"{SUITE}.TheModeIsEstablishedRatherThanRequested.test_a_restrictive_umask_cannot_author_an_unreadable_document"),

    ("the write denial is dropped, so readable became writable",
     REPO / "v12/python/src/baton_v12/worker_manager/oci.py",
     '''    for source, target, writable in assigned:
        argv += ["--mount",
                 f"type=bind,source={source},target={target},"
                 f"readonly={'false' if writable else 'true'}"]''',
     '''    for source, target, writable in assigned:
        argv += ["--mount",
                 f"type=bind,source={source},target={target},"
                 f"readonly=false"]''',
     f"{SUITE}.DockerDelivery.test_neither_document_is_writable_and_neither_is_the_root"),
]


def digest(place):
    return hashlib.sha256(place.read_bytes()).hexdigest()[:16]


def run(target):
    finished = subprocess.run(
        [sys.executable, "-m", "unittest", target],
        capture_output=True, timeout=1800,
        env={**os.environ, "PYTHONPATH": "src"},
        cwd=str(REPO / "v12/python"))
    return finished.returncode, (finished.stdout + finished.stderr).decode(
        "utf-8", "replace")


def main():
    print("W33935 — THE CORRECTED DELIVERY, MEASURED BY REMOVAL")
    print("=" * 74)
    print()

    code, output = run(SUITE)
    print(f"BASELINE  {'OK' if code == 0 else 'FAILED'}")
    if code != 0:
        print(output[-2500:])
        return 1
    print()

    caught, uncaught = [], []
    for title, place, old, new, target in MUTATIONS:
        original = place.read_text()
        if old not in original:
            print(f"[ANCHOR] {title}")
            print(f"         the anchor is no longer in {place.name}; this "
                  f"mutation measured NOTHING")
            uncaught.append((title, "stale anchor"))
            continue
        before = digest(place)
        place.write_text(original.replace(old, new, 1))
        try:
            code, output = run(target)
        finally:
            place.write_text(original)
        after = digest(place)
        assert before == after, f"{place} was not restored"
        if code != 0:
            print(f"[caught] {title}")
            print(f"         {target.split('.')[-1]}")
            caught.append(title)
        else:
            print(f"[NOT CAUGHT] {title}")
            print(f"             {target} still passes")
            uncaught.append((title, target))
        print()

    print("=" * 74)
    print(f"caught {len(caught)} of {len(MUTATIONS)}")
    if uncaught:
        print("NOT CAUGHT — each of these is a rule nothing here measures:")
        for title, why in uncaught:
            print(f"  {title} ({why})")
    return 0 if not uncaught else 1


if __name__ == "__main__":
    raise SystemExit(main())
