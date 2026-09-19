"""Disposable local-tree descriptor baseline; no stores, engine or provider.

The soft limit is lowered only in each child process. Both reviewed functions
are exercised over 1100 plain manager-owned files, never the installed attempt.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

def probe(name, root):
    from baton_v12.worker_manager import workspaces
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (min(1024, soft), hard))
    opened = set()
    metrics = {"peak_open_descriptors_from_os_open": 0, "successful_opens": 0,
               "first_open_errno": None, "limit": min(1024, soft)}
    original_open, original_close = os.open, os.close
    def measured_open(*args, **kwargs):
        try:
            fd = original_open(*args, **kwargs)
        except OSError as exc:
            metrics["first_open_errno"] = exc.errno
            raise
        opened.add(fd)
        metrics["successful_opens"] += 1
        metrics["peak_open_descriptors_from_os_open"] = max(
            metrics["peak_open_descriptors_from_os_open"], len(opened))
        return fd
    def measured_close(fd):
        result = original_close(fd)
        opened.discard(fd)
        return result
    pin = os.stat(root)
    started = time.monotonic()
    os.open, os.close = measured_open, measured_close
    try:
        if name == "provision":
            gid = next(g for g in sorted(set(os.getgroups()) | {os.getgid()}) if g > 0)
            workspaces._provision_line_access(root, (pin.st_dev, pin.st_ino), gid)
        else:
            workspaces._prove_line_consumable(root, (pin.st_dev, pin.st_ino))
        metrics["outcome"] = "returned"
    except Exception as exc:
        metrics["outcome"] = type(exc).__name__
        metrics["message"] = str(exc)
    finally:
        os.open, os.close = original_open, original_close
    metrics["remaining_tracked_descriptors"] = len(opened)
    metrics["seconds"] = time.monotonic() - started
    print(json.dumps(metrics))

if len(sys.argv) > 1:
    probe(sys.argv[1], sys.argv[2])
else:
    started = time.monotonic()
    root = Path(tempfile.mkdtemp(prefix="w194457-review194488-"))
    for i in range(1100):
        (root / str(i)).write_bytes(b"fixture\n")
    def state():
        return [(p.name, p.stat().st_mode, p.stat().st_uid, p.stat().st_gid)
                for p in [root, *sorted(root.iterdir())]]
    before = state()
    evidence = {"fixture": str(root), "entries": 1101, "cases": {}}
    for name in ("provision", "consume"):
        run = subprocess.run([sys.executable, __file__, name, str(root)],
                             capture_output=True, text=True, timeout=15)
        evidence["cases"][name] = {"returncode": run.returncode,
                                   "stdout": json.loads(run.stdout),
                                   "stderr": run.stderr}
    evidence["ownership_and_modes_unchanged"] = before == state()
    source = Path("src/baton_v12/worker_manager/workspaces.py")
    evidence["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    evidence["total_seconds"] = time.monotonic() - started
    evidence["limits"] = "open tracking excludes scandir's internal descriptor and interpreter baseline; installed incident errno remains unknown"
    (Path(__file__).parent / "REVIEW-EVIDENCE-194488.json").write_text(
        json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
