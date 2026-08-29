"""W36540 — does the custody helper actually remove the measured defect?

PLAN 1 and 2, asked of a real daemon before anything is wired: a directory a
real worker created with content in it, at a mode the worker chose, and the
question is whether the manager can remove the tree AFTER one custody act and
not before.
"""
import json, os, subprocess, sys, uuid
sys.path.insert(0, "/home/sl/src/baton/v12/python")
sys.path.insert(0, "/home/sl/src/baton/v12/python/src")

from baton_v12.worker_manager import custody, workspaces          # noqa: E402
from baton_v12.contracts import ContractRefusal                   # noqa: E402

ENGINE = os.environ.get("BATON_V12_ENGINE", "docker")
GROUP = int(os.environ.get("BATON_V12_WORKSPACE_GROUP", os.getgid()))
IMAGE = os.environ["BATON_V12_IMAGE"]


def run(argv):
    done = subprocess.run(argv, capture_output=True, timeout=300)
    return done.returncode, done.stdout.decode(), done.stderr.decode()


def main():
    storage = f"/tmp/w36540-{uuid.uuid4().hex[:8]}"
    os.makedirs(storage)
    from baton_v12.worker_manager import ControlStore
    store = ControlStore.open(os.path.join(storage, "c.sqlite3"),
                              incarnation="probe",
                              clock=lambda: "2026-08-29T00:00:00.000Z")
    workspaces.configure_workspace_group(store, GROUP)
    group = workspaces.configured_workspace_group(store)
    roots = workspaces.assignment_workspace(group, storage, "attempt-1")
    place = roots["workspace"]

    print("W36540 — CUSTODY OVER WHAT THE WORKER LEAVES")
    print("=" * 60)
    print(f"engine {ENGINE}   workspace group {GROUP}   manager {os.getuid()}")
    print()

    # A REAL WORKER, creating the exact shape the defect is about.
    worker = (
        "import os\n"
        "os.umask(0o022)\n"
        "os.makedirs('/workspace/worker-made-dir/nested', exist_ok=True)\n"
        "open('/workspace/worker-made-dir/nested/deep.txt','w').write('x')\n"
        "os.chmod('/workspace/worker-made-dir/nested', 0o700)\n"
        "print('worker done', os.getuid(), os.getgid())\n")
    code, out, err = run([
        ENGINE, "run", "--rm", "--user", "65532:65532",
        # W33936's mechanism, which is the precondition this Work builds on:
        # the worker can write the root because it holds the configured group.
        "--group-add", str(GROUP),
        "--mount", f"type=bind,source={place},target=/workspace",
        "--entrypoint", "python3", IMAGE, "-c", worker])
    print("the worker ran:", out.strip() or err.strip()[:200])

    inner = os.path.join(place, "worker-made-dir")
    held = os.lstat(inner)
    print(f"what it left: {inner.split('/')[-1]} uid={held.st_uid} "
          f"mode={oct(held.st_mode & 0o7777)}  (manager is uid {os.getuid()})")
    print()

    print("BEFORE CUSTODY — the manager's own removal:")
    try:
        workspaces.discard_workspace(storage, "attempt-1")
        print("    REMOVED (the defect is not reproduced)")
        return 1
    except ContractRefusal as refusal:
        print(f"    REFUSED: {refusal.message[:150]}...")
    print()

    look = custody.custody_vector(
        ENGINE, image_digest=IMAGE, name=f"baton-custody-{uuid.uuid4().hex[:8]}",
        attempt_root=os.path.dirname(place), operation="inspect",
        workspace_group=group)
    code, out, err = run(look)
    print("WHAT THE CUSTODIAN SEES:")
    print("   ", (out.strip() or err.strip())[:600])
    print()

    name = f"baton-custody-{uuid.uuid4().hex[:8]}"
    argv = custody.custody_vector(ENGINE, image_digest=IMAGE, name=name,
                                  attempt_root=os.path.dirname(place),
                                  operation="normalize",
                                  workspace_group=group)
    code, out, err = run(argv)
    print("THE CUSTODY ACT:")
    print(f"    exit {code}: {out.strip()[:200] or err.strip()[:200]}")
    print()

    print("AFTER CUSTODY — the same removal, unchanged:")
    try:
        removed = workspaces.discard_workspace(storage, "attempt-1")
        print(f"    REMOVED = {removed}; the tree is gone: "
              f"{not os.path.exists(os.path.join(storage, 'attempt-1'))}")
        return 0
    except ContractRefusal as refusal:
        print(f"    STILL REFUSED: {refusal.message[:200]}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
