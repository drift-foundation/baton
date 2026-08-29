"""W26283 re-review [P1], after the correction: the ceilings bound the work.

This is the reviewer's own `w26283-review-read-bounds.py`, re-run against the
corrected implementation, with ONE change that the required correction forced
and this file exists to name.

WHY THE REVIEWER'S SCRIPT CANNOT RUN UNMODIFIED. The correction the review
asked for was to "give the descriptor reader the smaller remaining
global/declared byte allowance", so `_read_exactly` now takes that allowance
as a required keyword. The reviewer's entry probe interposes on
`_read_exactly` with a three-parameter wrapper, and a wrapper with the old
signature raises `TypeError` at the first call rather than reporting anything
about the bound. Its BYTE probe is unaffected and still passes as written --
`byte ceiling 8: source returned 9 bytes across 9 reads before refusal`.

The reviewer's file is kept exactly as it was produced; this one is the same
two probes with `**rest` on that wrapper, plus a third the review's harm
description asks for and the original could not express: a file the worker
never stops appending to, which an unbounded reader never finishes reading at
all.

Exit 0 means every ceiling bounded the operation it governs.
"""

import os
import pathlib
import signal
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "v12" / "python" / "src"))

from baton_v12.contracts import ContractRefusal  # noqa: E402
from baton_v12.worker_manager import workspaces  # noqa: E402


def byte_ceiling():
    """A size observed below the ceiling can grow while the fd is open."""
    with tempfile.TemporaryDirectory(prefix="w26283-byte-bound-") as home:
        with open(os.path.join(home, "answer"), "wb") as writing:
            writing.write(b"x")
        original_read = workspaces.os.read
        original_limit = workspaces.MAX_BYTES
        calls = 0

        def growing(_descriptor, _amount):
            nonlocal calls
            calls += 1
            return b"x" if calls <= 64 else b""

        workspaces.os.read = growing
        workspaces.MAX_BYTES = 8
        try:
            try:
                workspaces.directory_manifest(home)
            except ContractRefusal:
                pass
        finally:
            workspaces.os.read = original_read
            workspaces.MAX_BYTES = original_limit
        # A bounded implementation needs at most ceiling+1 bytes to refuse.
        print(f"byte ceiling 8: source returned {min(calls, 64)} bytes "
              f"across {calls} reads before refusal")
        return calls <= 9


def entry_ceiling():
    """The file crossing an entry ceiling must not be read first."""
    with tempfile.TemporaryDirectory(prefix="w26283-entry-bound-") as home:
        source = os.path.join(home, "source")
        custody = os.path.join(home, "custody")
        os.mkdir(source)
        for name in ("a", "b"):
            with open(os.path.join(source, name), "wb") as writing:
                writing.write(name.encode("ascii"))
        original = workspaces._read_exactly
        read = []

        # `**rest` IS THE ONE CHANGE from the reviewer's script: the required
        # correction gave this function its allowance operand.
        def observed(place, relative, what, **rest):
            read.append(relative)
            return original(place, relative, what, **rest)

        workspaces._read_exactly = observed
        try:
            try:
                workspaces.copied_manifest(source, custody, max_entries=1)
            except ContractRefusal:
                pass
        finally:
            workspaces._read_exactly = original
        print(f"entry ceiling 1: source files read before refusal: {read}")
        return read == ["a"]


def never_stops_growing():
    """The harm the review named: a refusal that is never REACHED.

    A finite file makes an unbounded read merely wasteful. A worker that keeps
    appending makes it non-terminating, so this probe bounds itself and treats
    the alarm as the failure it is.
    """
    with tempfile.TemporaryDirectory(prefix="w26283-growth-") as home:
        source = os.path.join(home, "source")
        custody = os.path.join(home, "custody")
        os.mkdir(source)
        answer = os.path.join(source, "answer")
        with open(answer, "wb") as writing:
            writing.write(b"x")
        module = workspaces.os
        counted = []

        def grow():
            with open(answer, "ab") as appending:
                appending.write(b"x" * 64)

        class Growing:

            def __getattr__(self, name):
                return getattr(module, name)

            def fstat(self, descriptor):
                stated = module.fstat(descriptor)
                grow()
                return stated

            def read(self, descriptor, amount):
                piece = module.read(descriptor, amount)
                counted.append(len(piece))
                grow()
                return piece

        def ring(_number, _frame):
            raise TimeoutError("the read never reached the ceiling")

        original_limit = workspaces.MAX_BYTES
        workspaces.os = Growing()
        workspaces.MAX_BYTES = 8
        previous = signal.signal(signal.SIGALRM, ring)
        signal.alarm(5)
        answered = None
        try:
            workspaces.copied_manifest(source, custody)
        except ContractRefusal as refusal:
            answered = f"{refusal.category}/{refusal.code}"
        except TimeoutError:
            answered = "NEVER REACHED"
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous)
            workspaces.os = module
            workspaces.MAX_BYTES = original_limit
        print(f"endless growth, ceiling 8: {sum(counted)} bytes read, "
              f"refused as {answered}")
        return answered == "policy/denied" and sum(counted) <= 9


if __name__ == "__main__":
    bounded = byte_ceiling()
    counted = entry_ceiling()
    terminating = never_stops_growing()
    raise SystemExit(0 if bounded and counted and terminating else 1)
