"""Reviewer evidence: output-custody limits do not bound source reads.

Exit 0 means both byte and entry ceilings stop the read itself. Exit 1 means
the current implementation performed source reads beyond a ceiling before it
refused. The fake ``os.read`` models a regular file growing after ``fstat``;
that race is worker-controlled, and a bounded reader must not depend on the
earlier size remaining true.
"""

import os
import pathlib
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

        def observed(place, relative, what):
            read.append(relative)
            return original(place, relative, what)

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


if __name__ == "__main__":
    bounded = byte_ceiling()
    counted = entry_ceiling()
    raise SystemExit(0 if bounded and counted else 1)
