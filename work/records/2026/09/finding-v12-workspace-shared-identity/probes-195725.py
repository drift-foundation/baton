"""The two corrections of review 2026-09-17T15-42-06Z, as a failing/passing pair.

Claim 195725. No engine, provider, installed store or network: this opens
files under a fresh temporary directory and nothing else. Run from
`v12/python` with `PYTHONPATH=src:.`. Recorded outputs BEFORE and AFTER the
correction are in `EVIDENCE-195725.json`.

P1 `file_to_symlink`: the reviewer's interleaving, replacing a
fingerprinted regular file with a symlink while its sibling is opened.
P2 `integrity_access_error`: a real `0000` entry, whose refusal has to name
the operation and the entry rather than only `errno 13`.
`control` and `stable_symlink` are the positive halves -- an unchanged tree
and a symlink that stays put both still pass.
"""
import json, os, tempfile, time
from pathlib import Path
from unittest import mock

from baton_v12.worker_manager import workspaces as w

started = time.monotonic()
scratch = Path(tempfile.mkdtemp(prefix="w194457-probe195725-"))
out = {"scratch": str(scratch), "engine": "none; local filesystem only"}


def replacement(case):
    base = scratch / case
    base.mkdir()
    line = base / "checkout"
    line.mkdir(mode=0o700)
    for name in ("one", "two"):
        (line / name).write_text("original")
    outside = base / "outside"
    outside.write_text("outside sentinel")
    pin = (line.stat().st_dev, line.stat().st_ino)
    identity = w.identity_for(w.WorkspaceGroup(os.getgid(), w._MINT))
    original_open = os.open
    opened, fired = [], []

    def interleave(path, *args, **kwargs):
        descriptor = original_open(path, *args, **kwargs)
        if kwargs.get("dir_fd") is not None and path in ("one", "two"):
            opened.append(path)
            if len(opened) == 2 and case != "control":
                first = line / opened[0]
                first.unlink()
                first.symlink_to(outside)
                fired.append(str(first))
        return descriptor

    try:
        with mock.patch.object(w.os, "open", side_effect=interleave):
            w.prove_line_integrity(str(line), pin, identity)
            w.establish_line_access(str(line), pin, identity)
        outcome = {"returned": True}
    except Exception as failure:
        outcome = {"returned": False, "error": type(failure).__name__,
                   "message": str(failure)}
    return {**outcome, "interleaving": fired,
            "root_mode": oct(line.stat().st_mode & 0o7777),
            "outside_unchanged": outside.read_text() == "outside sentinel"}


out["file_to_symlink"] = replacement("file-to-symlink")
out["control"] = replacement("control")

# A STABLE symlink must still be accepted -- nothing here asks for symlinks to
# be refused, only for a type transition between the passes to be caught.
stable = scratch / "stable-symlink"
stable.mkdir()
line = stable / "checkout"
line.mkdir(mode=0o700)
(line / "one").write_text("original")
(line / "link").symlink_to(stable / "elsewhere")
identity = w.identity_for(w.WorkspaceGroup(os.getgid(), w._MINT))
try:
    out["stable_symlink"] = {
        "returned": True,
        "result": w.prove_line_integrity(
            str(line), (line.stat().st_dev, line.stat().st_ino), identity)}
except Exception as failure:
    out["stable_symlink"] = {"returned": False, "error": type(failure).__name__,
                             "message": str(failure)}

# P2: a real mode-0000 entry
line = scratch / "unreadable-checkout"
line.mkdir(mode=0o700)
blocked = line / "blocked-entry"
blocked.write_text("retained")
blocked.chmod(0)
try:
    try:
        w.prove_line_integrity(str(line),
                               (line.stat().st_dev, line.stat().st_ino), identity)
        out["integrity_access_error"] = {"returned": True}
    except Exception as failure:
        out["integrity_access_error"] = {
            "returned": False, "error": type(failure).__name__,
            "message": str(failure),
            "root_mode": oct(line.stat().st_mode & 0o7777),
            "names_failed_path": "blocked-entry" in str(failure),
            "names_errno": "EACCES" in str(failure)}
finally:
    blocked.chmod(0o600)

out["seconds"] = time.monotonic() - started
print(json.dumps(out, indent=2))
