"""The two harms of W6634's staging, driven against the code as it was.

Kept because a finding stated in prose is a claim, and this is the reproduction
that made it a fact. Run it against the pre-fix `sealing._staged` -- which
measured with `directory_manifest` and then reopened each path with a plain
`open` -- and both cases below succeed where they should refuse.
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, "/home/sl/src/baton/v12/python/src")
from baton_v12.worker_manager import workspaces  # noqa: E402

REOPENING = """
Under the pre-fix code this printed:

    measured entries: [('deep/a.txt', 11)]
    STAGED WITHOUT REFUSAL
    custody now holds: 'HOST FILE THE WORKER MUST NOT REACH\\n'

and the FIFO probe timed out at 12 seconds rather than returning.
"""


def reopening_copy(place, into, manifest):
    """W6634's staging, reduced to the two lines that mattered."""
    os.makedirs(into, exist_ok=True)
    for entry in manifest["entries"]:
        target = os.path.join(into, entry["path"])
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(os.path.join(place, entry["path"]), "rb") as reading:
            content = reading.read()
        with open(target, "wb") as writing:
            writing.write(content)


def escapes_the_tree():
    home = tempfile.mkdtemp(prefix="w26283-probe-")
    tree = os.path.join(home, "out")
    os.makedirs(os.path.join(tree, "deep"))
    with open(os.path.join(tree, "deep", "a.txt"), "w") as handle:
        handle.write("legitimate\n")
    before = workspaces.directory_manifest(tree)
    print("measured entries:",
          [(one["path"], one["bytes"]) for one in before["entries"]])
    os.rename(os.path.join(tree, "deep"), os.path.join(home, "deep-real"))
    os.makedirs(os.path.join(home, "elsewhere"))
    with open(os.path.join(home, "elsewhere", "a.txt"), "w") as handle:
        handle.write("HOST FILE THE WORKER MUST NOT REACH\n")
    os.symlink(os.path.join(home, "elsewhere"), os.path.join(tree, "deep"))
    held = os.path.join(home, "custody")
    reopening_copy(tree, held, before)
    with open(os.path.join(held, "deep", "a.txt")) as reading:
        print("custody now holds:", repr(reading.read()))
    print(">>> the manager read and copied a file from OUTSIDE the workspace")


BLOCKS = '''
import os, sys, tempfile
sys.path.insert(0, "/home/sl/src/baton/v12/python/src")
sys.path.insert(0, "/tmp")
from baton_v12.worker_manager import workspaces
home = tempfile.mkdtemp(prefix="w26283-fifo-")
tree = os.path.join(home, "out"); os.makedirs(tree)
open(os.path.join(tree, "a.txt"), "w").write("ok\\n")
before = workspaces.directory_manifest(tree)
os.unlink(os.path.join(tree, "a.txt"))
os.mkfifo(os.path.join(tree, "a.txt"))
print("staging over a FIFO...", flush=True)
open(os.path.join(tree, "a.txt"), "rb").read()
print("returned")
'''


def blocks_forever():
    found = subprocess.run([sys.executable, "-c", BLOCKS],
                           capture_output=True, timeout=None
                           if "--wait" in sys.argv else 12)
    print(found.stdout.decode(), end="")


if __name__ == "__main__":
    escapes_the_tree()
    try:
        blocks_forever()
        print(">>> returned; the FIFO did not block")
    except subprocess.TimeoutExpired:
        print(">>> TIMED OUT: one mkfifo stalls the copy indefinitely")
