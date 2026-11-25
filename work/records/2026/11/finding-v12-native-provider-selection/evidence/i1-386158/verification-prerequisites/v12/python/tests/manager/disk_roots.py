"""A DISK-BACKED temporary root, for the suites whose subject needs one.

W71917. `source_boundary.compose_source_boundary` refuses a workspace on a
memory filesystem, because the five uses the ruling names -- checkout, build
cache, test artifacts, output and logs -- must not rely on scratch. That rule
is about a real deployment and it is also a rule the tests have to satisfy: on
a host whose `/tmp` is a tmpfs, `tempfile.mkdtemp()` answers a directory the
boundary correctly refuses, and every case that needed a workspace would fail
for the environment rather than for the code.

SO THE ROOT IS CHOSEN AND THE CHOICE IS STATED, in the shape
`input_roots.deployment_workspace_group` already uses for the same class of
problem: an explicit environment operand first, then named candidates tried in
order, and a REFUSAL rather than a silent fallback when none of them works.

WHY NOT SKIP. A suite that skipped itself on a tmpfs `/tmp` would report green
on a host where the boundary was never exercised, and this Work's whole subject
is a delivery that must not be able to look correct without being correct. A
run that cannot find real storage is told so, by name, with the variable that
fixes it.

NOTHING HERE ASSERTS ANYTHING. It answers a directory that goes away with the
case, exactly as `input_roots.storage_under` does.
"""

import os
import pathlib
import shutil
import tempfile

from tests.git_isolation import FixtureIsolationRefusal, require_fixture_root

from baton_v12.worker_manager.source_boundary import (MEMORY_FILESYSTEMS,
                                                      filesystem_of)

VARIABLE = "BATON_V12_DISK_ROOT"

DISTRIBUTION = pathlib.Path(__file__).resolve().parents[2]


def candidates():
    """Explicit selection, system temporary root, then /var/tmp; never checkout."""
    named = os.environ.get(VARIABLE)
    return ([named] if named else []) + [tempfile.gettempdir(), "/var/tmp"]


def disk_backed_root():
    """The first candidate that is real storage this process can write.

    AN EXPLICIT VARIABLE IS NEVER SILENTLY PASSED OVER. If a run names one and
    it is memory-backed or unwritable, that is a run whose operator believed
    something false about where its workspaces were going, and it is told
    rather than quietly given the next candidate.
    """
    named = os.environ.get(VARIABLE)
    tried = []
    for place in candidates():
        try:
            require_fixture_root(place)
        except FixtureIsolationRefusal as failure:
            tried.append(f"{place} (enclosing Git repository)")
            if place == named:
                raise AssertionError(str(failure)) from failure
            continue
        try:
            kind = filesystem_of(place)
        except Exception as failure:                     # noqa: BLE001
            tried.append(f"{place} ({type(failure).__name__})")
            if place == named:
                raise AssertionError(
                    f"{VARIABLE} is {named!r} and this build cannot say what "
                    f"filesystem it is on: {failure}") from failure
            continue
        if kind in MEMORY_FILESYSTEMS:
            tried.append(f"{place} ({kind})")
            if place == named:
                raise AssertionError(
                    f"{VARIABLE} is {named!r}, which is on a {kind} "
                    f"filesystem; W71917 refuses a workspace on memory, so a "
                    f"run pointed at one would prove the refusal rather than "
                    f"the delivery")
            continue
        if not os.path.isdir(place) or not os.access(place, os.W_OK):
            tried.append(f"{place} (not writable)")
            if place == named:
                raise AssertionError(
                    f"{VARIABLE} is {named!r}, which is not a directory this "
                    f"process can write")
            continue
        return place
    raise AssertionError(
        f"no disk-backed directory was found for a W71917 workspace; tried "
        f"{', '.join(tried)}. Set {VARIABLE} to a directory on real storage. "
        f"A workspace on a memory filesystem is refused by "
        f"`source_boundary.check_disk_backed`, so a run without one would "
        f"report this Work's refusal as its result.")


def disk_backed_under(case):
    """One disk-backed temporary directory, removed with the case.

    FORCIBLY, for `input_roots._forcibly_remove`'s reason: what is composed
    under here includes deliberately read-only input roots, and a fixture that
    could not take its own delivery away again would leave the next run's
    storage populated.
    """
    # CANONICAL, for `input_roots.storage_under`'s reason: a `/proc/self/fd`
    # alias is not a spelling the product's refusals or a child process can
    # use, and this directory is the fixture's own.
    place = os.path.realpath(
        tempfile.mkdtemp(prefix="v12-w71917-", dir=disk_backed_root()))
    case.addCleanup(_forcibly_remove, place)
    return place


def remove_owned_root(place):
    """Remove one FIXTURE-OWNED root whole, however the product froze what is under it.

    W384870 (five-groups-20261118): nine fixtures left 262 roots under `/var/tmp` in one
    run because the product makes delivered launch, attempt, publication and sealed trees
    read-only ON PURPOSE (0555 directories, 0444 files, even 0-mode roots) and
    `shutil.rmtree(..., ignore_errors=True)` then fails SILENTLY on every one of them.
    Owner access is restored on each real directory first -- the root is this fixture's
    own, made by `mkdtemp`, so that is not a custody violation -- and the removal is then
    NOT allowed to fail quietly: a fixture that cannot take its own root away reports it.

    LINKS ARE NOT FOLLOWED. A symlink inside the root is removed as a link; whatever it
    points at is somebody else's and keeps its bytes and its modes. The root itself must
    be a real directory for the same reason.
    """
    if os.path.islink(place) or not os.path.isdir(place):
        raise AssertionError(f"{place} is not a fixture-owned directory")

    def restore(path):
        os.chmod(path, 0o700)
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    restore(entry.path)

    restore(place)
    shutil.rmtree(place)


def _forcibly_remove(place):
    for current, _directories, files in os.walk(place):
        try:
            os.chmod(current, 0o700)
        except OSError:
            continue
        for name in files:
            try:
                os.chmod(os.path.join(current, name), 0o600)
            except OSError:
                pass
    shutil.rmtree(place, ignore_errors=True)
