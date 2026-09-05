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

from baton_v12.worker_manager.source_boundary import (MEMORY_FILESYSTEMS,
                                                      filesystem_of)

VARIABLE = "BATON_V12_DISK_ROOT"

DISTRIBUTION = pathlib.Path(__file__).resolve().parents[2]


def candidates():
    """Where a disk-backed root might be, in the order they are tried.

    THE DISTRIBUTION ITSELF IS ON THE LIST because a checkout is the one
    directory a test run is guaranteed to have and is almost always on real
    storage -- and because it is the same filesystem the run's own artifacts
    are already on, so a run that can write its results can write this.
    """
    named = os.environ.get(VARIABLE)
    return ([named] if named else []) + [tempfile.gettempdir(),
                                         str(DISTRIBUTION), "/var/tmp"]


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
    place = tempfile.mkdtemp(prefix="v12-w71917-", dir=disk_backed_root())
    case.addCleanup(_forcibly_remove, place)
    return place


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
