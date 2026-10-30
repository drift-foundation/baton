"""W376956 probe: what the CONNECTED create-step failure actually does.

Disposable filesystem only. No engine, provider, operational install or
retained store.
"""
import io
import json
import os
import pathlib
import sys
import tempfile
from unittest import mock

here = pathlib.Path("/home/sl/src/baton/v12/python")
sys.path.insert(0, str(here / "src"))
sys.path.insert(0, str(here))

import baton_v12.job_manager  # noqa: F401  (import order)
from tools import instance, stack_command  # noqa: F401
from tools import bootstrap

temp = tempfile.TemporaryDirectory(prefix="v12-create-step-")
root = pathlib.Path(os.path.realpath(temp.name))
source = root / "built"
(source / "_internal" / "rpds").mkdir(parents=True)
(source / "baton-v12-stack").write_text("the launcher")
(source / "_internal" / "rpds" / "rpds.so").write_text("native")
destination = str(root / "deployment")
places = instance.layout(destination)
said = {"command": "baton-v12-stack", "frozen": True,
        "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
        "schema_assets": {"agent-session-1.0": 10, "worker-control-1.0": 20},
        "native_rpds": str(source / "_internal" / "rpds" / "rpds.so")}

home = root / "prerequisites"
document = {"authority_uuid": "0" * 31 + "a",
            "workers": [{"worker_id": "w-1", "deployment": {
                "workspace_storage": str(home / "w-1" / "storage"),
                "launch_home": str(home / "w-1" / "launch"),
                "credential_home": str(home / "w-1" / "credentials")}}]}

print("planned roots:")
for who, name, place in bootstrap.prerequisite_places(document):
    print("   ", who, name, place)

real = os.mkdir
order = []


def failing(leaf, *operands, **named):
    order.append(str(leaf))
    if str(leaf) == "launch":
        raise OSError(5, "the device went away mid-create")
    return real(leaf, *operands, **named)


out = io.StringIO()
with mock.patch.object(bootstrap, "_identity_of",
                       lambda command, runtime=None, distro=None: said):
    admitted = bootstrap.admit(destination, str(source))
    with mock.patch.object(os, "mkdir", failing):
        try:
            bootstrap.install(destination, str(source), document, stream=out,
                              admitted=admitted, now=1.0)
        except BaseException as failure:
            print("\nRAISED", type(failure).__name__, ":", failure)
            print("CAUSE ", type(failure.__cause__).__name__, ":",
                  failure.__cause__)

print("\nmkdir leaves seen:", order)
print("\n--- stream ---")
print(out.getvalue())
print("--- end ---")
for place in (places["distro"], places["justfile"], places["instance"],
              str(home / "w-1" / "storage"), str(home / "w-1" / "launch"),
              str(home / "w-1" / "credentials")):
    print("lexists", os.path.lexists(place), place)
