"""W33935 — the delivered `/input` pair, asked of a real container.

PLAN item 1: revalidate W6's observation against the CURRENT workspace and
worker identity code before acting on it.

It starts one execution runtime through `request_runtime_start` -- the same
production path W6636 composes -- and then runs a probe inside the exact argv
the manager composed, with only the entrypoint replaced.  What it reports is
what a worker would see: the identity it runs as, and for the input root, both
manager-authored documents and the sibling launch document, the mode, the
owner, and whether a read actually succeeds.

Run from `v12/python` with `PYTHONPATH=src python3 <this file>`.
"""

import json
import os
import pathlib
import subprocess
import sys
import unittest
import uuid

REPO = pathlib.Path("/home/sl/src/baton")
sys.path.insert(0, str(REPO / "v12/python"))
sys.path.insert(0, str(REPO / "v12/python/src"))

from baton_v12.worker_manager import request_runtime_start          # noqa: E402
from baton_v12.worker_manager import launch, workspaces             # noqa: E402
from tests.manager import test_lifecycle_composition as W           # noqa: E402

PROBE = r'''
import json, os
out = {"running_as": [os.getuid(), os.getgid()]}
for one in ("/input", "/input/input.json", "/input/assignment.json",
            "/workspace", "/run/baton/launch.json"):
    try:
        held = os.stat(one)
    except OSError as error:
        out[one] = f"{type(error).__name__}: {error}"
        continue
    answer = {"mode": oct(held.st_mode & 0o777), "uid": held.st_uid,
              "gid": held.st_gid}
    if os.path.isdir(one):
        try:
            answer["listable"] = sorted(os.listdir(one))
        except OSError as error:
            answer["listable"] = f"{type(error).__name__}: {error}"
        try:
            with open(os.path.join(one, "w33935-probe"), "w") as handle:
                handle.write("x")
            answer["writable"] = True
            os.unlink(os.path.join(one, "w33935-probe"))
        except OSError as error:
            answer["writable"] = f"{type(error).__name__}: {error}"
    else:
        try:
            with open(one, "rb") as handle:
                answer["read_bytes"] = len(handle.read())
        except OSError as error:
            answer["read_bytes"] = f"{type(error).__name__}: {error}"
        try:
            with open(one, "ab") as handle:
                handle.write(b"x")
            answer["writable"] = True
        except OSError as error:
            answer["writable"] = f"{type(error).__name__}: {error}"
    out[one] = answer
print(json.dumps(out))
'''


class Probe(W.Composition, unittest.TestCase):
    engine = "docker"
    required = True

    def runProbe(self):
        adapter, roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        argv = next(list(one) for one in reversed(self.engine_calls)
                    if "run" in one)
        name = f"{W.MARK}-w33935-{uuid.uuid4().hex[:10]}"
        argv[argv.index("--name") + 1] = name
        self.made.append(name)
        image = argv[-1]
        argv = [one for one in argv[:-1] if one != "--detach"]
        argv += ["--entrypoint", "python3", image, "-c", PROBE]
        finished = subprocess.run(argv, capture_output=True, timeout=300)
        raw = finished.stdout.decode("utf-8", "replace")
        Probe.answer = json.loads(raw.strip().splitlines()[-1])
        # And the HOST side of the same three paths, so the container's answer
        # can be read against what the manager actually wrote.
        Probe.host = {}
        for label, place in (("inputs root", roots["inputs"]),
                             ("input.json",
                              os.path.join(roots["inputs"], "input.json")),
                             ("assignment.json",
                              os.path.join(roots["inputs"],
                                           "assignment.json")),
                             ("workspace", roots["workspace"]),
                             ("launch.json", adapter.launch_delivery.place)):
            held = os.stat(place)
            Probe.host[label] = {"mode": oct(held.st_mode & 0o777),
                                 "uid": held.st_uid, "gid": held.st_gid}


def main():
    print("W33935 — THE DELIVERED /input PAIR, ASKED OF A REAL CONTAINER")
    print("=" * 74)
    print()
    print("the constants this delivery is written with:")
    print(f"    workspaces.READ_ONLY_FILE = {oct(workspaces.READ_ONLY_FILE)}")
    print(f"    workspaces.READ_ONLY_DIR  = {oct(workspaces.READ_ONLY_DIR)}")
    print(f"    launch.READ_ONLY_FILE     = {oct(launch.READ_ONLY_FILE)}")
    print(f"    launch.READ_ONLY_DIR      = {oct(launch.READ_ONLY_DIR)}")
    print()

    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(
        unittest.TestSuite([Probe("runProbe")]))
    if not result.wasSuccessful():
        return 1

    print()
    print("THE HOST SIDE, as the manager wrote it:")
    for label in Probe.host:
        print(f"    {label:16} {Probe.host[label]}")
    print()
    print("THE CONTAINER SIDE, as a worker would find it:")
    print(f"    running as       {Probe.answer['running_as']}")
    for place in ("/input", "/input/input.json", "/input/assignment.json",
                  "/workspace", "/run/baton/launch.json"):
        print(f"    {place}")
        print(f"      {Probe.answer[place]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
