"""Reviewer reproduction: a listed regular file can still become a FIFO.

The custody pass checks a directory entry and then opens its name.  The open
must be nonblocking because the worker-owned name can change in that interval;
checking ``fstat`` after a blocking FIFO open is too late.

The parent bounds the child so this evidence never hangs its caller.  Exit 0
means the open returned and the special file was refused.  Exit 1 means the
current implementation blocked before it could apply that refusal.
"""

import os
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "v12" / "python" / "src"))


def child(place):
    from baton_v12.contracts import ContractRefusal
    from baton_v12.worker_manager import workspaces

    original = workspaces._walk

    def replace_after_listing(real, what):
        parent = os.open(real, os.O_RDONLY | os.O_DIRECTORY)
        try:
            # This is the interval after a directory entry was accepted as a
            # regular file and before _read_exactly opens that entry.
            os.unlink(os.path.join(real, "answer"))
            os.mkfifo(os.path.join(real, "answer"))
            yield (parent, "answer"), "answer"
        finally:
            os.close(parent)

    workspaces._walk = replace_after_listing
    try:
        try:
            workspaces.copied_manifest(place, place + "-custody")
        except ContractRefusal as error:
            print(f"returned with {error.category}/{error.code}: {error}")
            return 0
        print("UNEXPECTED: copied a replacement FIFO")
        return 2
    finally:
        workspaces._walk = original


def parent():
    with tempfile.TemporaryDirectory(prefix="w26283-review-fifo-") as home:
        place = os.path.join(home, "worker-output")
        os.mkdir(place)
        with open(os.path.join(place, "answer"), "wb") as writing:
            writing.write(b"regular when listed\n")
        try:
            found = subprocess.run(
                [sys.executable, __file__, "--child", place],
                capture_output=True, text=True, timeout=3)
        except subprocess.TimeoutExpired:
            print("BLOCKED: the post-listing FIFO replacement hung os.open")
            return 1
        print(found.stdout, end="")
        print(found.stderr, end="", file=sys.stderr)
        return found.returncode


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        raise SystemExit(child(sys.argv[2]))
    raise SystemExit(parent())
