"""Measure W26283's output-custody guards by removing them.

A guard nothing observes is not established. Each mutation below breaks ONE
rule the custody provider promises; the suites must fail.

`__pycache__` is dropped per write: these rewrites land inside one filesystem
timestamp tick and CPython's mtime+size invalidation misses that.
"""

import pathlib
import shutil
import subprocess
import sys

HOME = pathlib.Path("/home/sl/src/baton/v12/python")
SRC = HOME / "src" / "baton_v12" / "worker_manager"
# THE REAL-ENGINE SUITE IS IN THE MEASUREMENT TOO. A mutation caught only by
# fixtures is a rule established against material this repository wrote for
# itself; the acceptance asks for a real worker's output, so the removal is
# measured against one.
MODULES = ["tests.manager.test_sealing", "tests.manager.test_workspaces",
           "tests.manager.test_output_custody_engine"]

MUTATIONS = [
    # -- the defect this Work exists to fix -----------------------------------
    ("staging reopens each measured path, as W6634 did", "sealing.py",
     "    written = workspaces.copied_manifest(",
     "    written = _reopening_copy("),

    ("the copy follows a link at the destination", "workspaces.py",
     "                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | "
     "os.O_NOFOLLOW,",
     "                         os.O_WRONLY | os.O_CREAT | os.O_TRUNC,"),

    # Review [P1]: the interval between a directory entry being ACCEPTED as a
    # regular file and its name being OPENED. Without the flag the open blocks
    # on a FIFO and the descriptor-level refusal below it is unreachable. The
    # regression bounds itself with an alarm, which is what keeps this
    # mutation measurable instead of hanging the run.
    ("a post-listing pipe blocks the source open", "workspaces.py",
     "        descriptor = os.open(name,\n"
     "                             os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,\n"
     "                             dir_fd=parent)",
     "        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW,\n"
     "                             dir_fd=parent)"),

    ("the destination is written even if an entry is already there",
     "workspaces.py",
     "os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,",
     "os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW,"),

    # -- the ceilings ---------------------------------------------------------
    ("a declared entry ceiling is not enforced", "workspaces.py",
     "    if max_entries is not None and taken + 1 > max_entries:",
     "    if False:"),

    ("a declared byte ceiling is not enforced", "workspaces.py",
     "    if max_bytes is not None and total + added > max_bytes:",
     "    if False:"),

    ("a declared ceiling refuses as policy rather than integrity",
     "workspaces.py",
     '        _refuse(f"{what} carries more than the {max_entries} files '
     'its "\n                f"declaration allows", code="limit")',
     '        _denied(f"{what} carries more than the {max_entries} files "\n'
     '                f"its declaration allows")'),

    ("the global policy ceiling is gone", "workspaces.py",
     "    if taken + 1 > MAX_ENTRIES:",
     "    if False:"),

    # -- re-review [P1]: the ORDER, and the bound on the read ------------------
    # A guard after an unbounded operation does not bound that operation. Both
    # of these leave the ceiling in place and only put it back where it was --
    # after the work it exists to refuse -- so a suite that catches them is one
    # that observes the ORDER rather than just the answer.
    ("the entry ceiling is checked after the crossing file has been read",
     "workspaces.py",
     "        _entry_ceilings(what, len(entries), max_entries)\n"
     "        content = _read_exactly(place, relative, what,\n"
     "                                allowance=_byte_allowance(total, "
     "max_bytes))",
     "        content = _read_exactly(place, relative, what,\n"
     "                                allowance=_byte_allowance(total, "
     "max_bytes))\n"
     "        _entry_ceilings(what, len(entries), max_entries)"),

    ("the measuring pass reads before it counts", "workspaces.py",
     "        _entry_ceilings(what, len(entries), None)\n"
     "        content = _read_exactly(place, relative, what,\n"
     "                                allowance=_byte_allowance(total, None))",
     "        content = _read_exactly(place, relative, what,\n"
     "                                allowance=_byte_allowance(total, None))\n"
     "        _entry_ceilings(what, len(entries), None)"),

    ("the descriptor read ignores the allowance it was given",
     "workspaces.py",
     "    remaining = allowance + 1",
     "    remaining = 1 << 62"),

    # -- the caller's content rule --------------------------------------------
    ("the caller's rule runs AFTER the write", "workspaces.py",
     "        if admits is not None:\n            admits(relative, content)\n"
     "        target = os.path.join(into, relative)",
     "        target = os.path.join(into, relative)"),

    ("live-secret bytes are not scanned at all", "sealing.py",
     "        admits=lambda relative, content: check_no_durable_secret(",
     "        admits=lambda relative, content: (lambda *a, **k: None)("),

    # -- custody's own integrity ----------------------------------------------
    ("an interrupted attempt's partial tree is kept", "sealing.py",
     "    _cleared(into)\n    limits = declared[\"constraints\"]",
     "    limits = declared[\"constraints\"]"),

    ("custody is not frozen read-only", "sealing.py",
     "    _frozen(into)\n    # THE WRITE VERIFIED",
     "    # THE WRITE VERIFIED"),

    ("the write is not verified against what was copied", "sealing.py",
     '    if confirmed["tree_digest"] != written["tree_digest"]:',
     "    if False:"),
]

# The reopening copy the fix replaced, restored verbatim so the first mutation
# reproduces W6634's behaviour rather than merely disabling something.
REOPENING = '''

def _reopening_copy(place, into, *, max_entries=None, max_bytes=None,
                    admits=None):
    """W6634's staging, restored for the mutation harness only."""
    import os as _os
    from . import workspaces as _w
    manifest = _w.directory_manifest(place)
    _os.makedirs(into, exist_ok=True)
    for entry in manifest["entries"]:
        source = _os.path.join(place, entry["path"])
        target = _os.path.join(into, entry["path"])
        _os.makedirs(_os.path.dirname(target), exist_ok=True)
        with open(source, "rb") as reading:
            content = reading.read()
        if admits is not None:
            admits(entry["path"], content)
        with open(target, "wb") as writing:
            writing.write(content)
    return _w.directory_manifest(into)
'''


def run():
    return subprocess.run(
        [sys.executable, "-B", "-m", "unittest", *MODULES],
        cwd=HOME, capture_output=True, timeout=900,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin", "HOME": "/home/sl"})


def drop_cache():
    for cache in HOME.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def main():
    drop_cache()
    base = run()
    print(f"BASELINE  {'OK' if base.returncode == 0 else 'FAILING'}\n")
    if base.returncode != 0:
        print(base.stderr.decode()[-3000:])
        return 1
    unestablished = []
    for name, where, before, after in MUTATIONS:
        place = SRC / where
        original = place.read_text()
        if original.count(before) != 1:
            print(f"[ANCHOR] {name}: {original.count(before)}x in {where}")
            unestablished.append(f"{name} (anchor)")
            continue
        body = original.replace(before, after)
        if "_reopening_copy(" in after:
            body += REOPENING
        place.write_text(body)
        drop_cache()
        try:
            found = run()
        finally:
            place.write_text(original)
            drop_cache()
        if found.returncode == 0:
            print(f"[UNSEEN] {name}")
            unestablished.append(name)
        else:
            tail = found.stderr.decode()
            failed = sorted({line.split(" ")[1] for line in tail.splitlines()
                             if line.startswith(("FAIL: ", "ERROR: "))})
            print(f"[caught] {name}\n         {', '.join(failed) or '?'}")
    print()
    if unestablished:
        print(f"{len(unestablished)} UNESTABLISHED:")
        for one in unestablished:
            print(f"  - {one}")
        return 1
    print(f"all {len(MUTATIONS)} mutations caught")
    return 0


if __name__ == "__main__":
    sys.exit(main())
