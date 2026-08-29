"""W33936 — the writable root, asked of a real container.

PLAN 1 and 2: revalidate the ownership, the fixed worker identity and every
manager-owned path's mode, so the least-privilege boundary is chosen from
measurement rather than from reasoning about what the modes probably are.

It starts one execution runtime through `request_runtime_start` and runs a
probe inside the exact argv the manager composed, entrypoint only replaced.

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
from baton_v12.worker_manager import credentials, launch, workspaces  # noqa: E402
from tests.manager import test_lifecycle_composition as W           # noqa: E402

PROBE = r'''
import json, os
out = {"running_as": [os.getuid(), os.getgid()],
       "groups": sorted(os.getgroups())}
for one in ("/input", "/input/input.json", "/workspace",
            "/run/baton/launch.json", "/run/baton/credentials/registry"):
    try:
        held = os.stat(one)
    except OSError as error:
        out[one] = f"{type(error).__name__}"
        continue
    answer = {"mode": oct(held.st_mode & 0o777), "uid": held.st_uid,
              "gid": held.st_gid,
              "r": os.access(one, os.R_OK), "w": os.access(one, os.W_OK),
              "x": os.access(one, os.X_OK)}
    target = os.path.join(one, "w33936") if os.path.isdir(one) else one
    try:
        with open(target, "a") as handle:
            handle.write("x")
        answer["wrote"] = True
        if os.path.isdir(one):
            os.unlink(target)
    except OSError as error:
        answer["wrote"] = f"{type(error).__name__}: {error.errno}"
    out[one] = answer
print(json.dumps(out))
'''


class Probe(W.Composition, unittest.TestCase):
    engine = "docker"
    required = True

    def runProbe(self):
        adapter, roots, inputs = self.prepared()
        delivery = self.credential()
        adapter = self.adapter(roots=roots, mounts=self.plan(roots),
                               credential_delivery=delivery)
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        argv = next(list(one) for one in reversed(self.engine_calls)
                    if "run" in one)
        Probe.user = argv[argv.index("--user") + 1]
        name = f"{W.MARK}-w33936-{uuid.uuid4().hex[:10]}"
        argv[argv.index("--name") + 1] = name
        self.made.append(name)
        image = argv[-1]
        argv = argv[:-1]
        # The attempt's labels are dropped so the probe is not a second
        # container carrying them; everything the delivery is made of stays.
        stripped, index = [], 0
        while index < len(argv):
            if argv[index] == "--label":
                index += 2
                continue
            if argv[index] == "--detach":
                index += 1
                continue
            stripped.append(argv[index])
            index += 1
        argv = stripped + ["--entrypoint", "python3", image, "-c", PROBE]
        finished = subprocess.run(argv, capture_output=True, timeout=300)
        raw = finished.stdout.decode("utf-8", "replace")
        assert raw.strip(), finished.stderr.decode("utf-8", "replace")[-2000:]
        Probe.answer = json.loads(raw.strip().splitlines()[-1])
        Probe.host = {}
        for label, place in (("inputs root", roots["inputs"]),
                             ("workspace root", roots["workspace"]),
                             ("assignment home",
                              os.path.dirname(roots["workspace"])),
                             ("launch root", adapter.launch_delivery.root),
                             ("credential root", delivery.root)):
            held = os.stat(place)
            Probe.host[label] = {"mode": oct(held.st_mode & 0o777),
                                 "uid": held.st_uid, "gid": held.st_gid}


def main():
    print("W33936 — THE WRITABLE ROOT, ASKED OF A REAL CONTAINER")
    print("=" * 74)
    print()
    print("the modes the manager's own components declare:")
    print(f"    workspaces.READ_ONLY_FILE  = {oct(workspaces.READ_ONLY_FILE)}")
    print(f"    workspaces.READ_ONLY_DIR   = {oct(workspaces.READ_ONLY_DIR)}")
    print(f"    launch.READ_ONLY_FILE      = {oct(launch.READ_ONLY_FILE)}")
    print(f"    launch.READ_ONLY_DIR       = {oct(launch.READ_ONLY_DIR)}")
    print(f"    credentials.VOLATILE_DIR   = {oct(credentials.VOLATILE_DIR)}")
    print(f"    credentials.VOLATILE_FILE  = {oct(credentials.VOLATILE_FILE)}")
    print(f"    the manager runs as        = {os.getuid()}:{os.getgid()}")
    print()

    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(
        unittest.TestSuite([Probe("runProbe")]))
    if not result.wasSuccessful():
        return 1

    print()
    print(f"THE COMPOSED --user IS {Probe.user!r}")
    print()
    print("THE HOST SIDE:")
    for label in Probe.host:
        print(f"    {label:18} {Probe.host[label]}")
    print()
    print("THE CONTAINER SIDE:")
    print(f"    running as {Probe.answer['running_as']} "
          f"groups {Probe.answer['groups']}")
    for place in ("/input", "/input/input.json", "/workspace",
                  "/run/baton/launch.json",
                  "/run/baton/credentials/registry"):
        print(f"    {place}")
        print(f"      {Probe.answer[place]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
