"""W376956 probe 2: the create step whose effect is UNPROVEN and whose name a
foreign object then holds -- and what the retry does with it.

Disposable filesystem only.
"""
import io
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
launch = str(home / "w-1" / "launch")
storage = str(home / "w-1" / "storage")
document = {"authority_uuid": "0" * 31 + "a",
            "workers": [{"worker_id": "w-1", "deployment": {
                "workspace_storage": storage,
                "launch_home": launch,
                "credential_home": str(home / "w-1" / "credentials")}}]}

real = os.mkdir
theirs = "somebody else took the name\n"


def interrupted(leaf, *operands, **named):
    if str(leaf) == "launch":
        # A foreign file appears at the name while this call is interrupted:
        # the effect is NOT this attempt's, and it cannot tell.
        with open(launch, "w", encoding="utf-8") as writing:
            writing.write(theirs)
        raise OSError(4, "interrupted")
    made = real(leaf, *operands, **named)
    if str(leaf) == "storage":
        with open(os.path.join(storage, "theirs.txt"), "w",
                  encoding="utf-8") as writing:
            writing.write("a foreign addition under an owned root\n")
    return made


def install(stream):
    with mock.patch.object(bootstrap, "_identity_of",
                           lambda command, runtime=None, distro=None: said):
        admitted = bootstrap.admit(destination, str(source))
        return bootstrap.install(destination, str(source), document,
                                 stream=stream, admitted=admitted, now=1.0)


out = io.StringIO()
with mock.patch.object(os, "mkdir", interrupted):
    try:
        install(out)
    except BaseException as failure:
        print("FIRST RAISED", type(failure).__name__, ":", failure)
print("\n--- first stream ---")
print(out.getvalue())

print("foreign file at the uncertain name:", repr(open(launch).read()))
print("foreign addition under the owned root:",
      os.path.lexists(os.path.join(storage, "theirs.txt")))

again = io.StringIO()
try:
    install(again)
except BaseException as failure:
    print("\nRETRY RAISED", type(failure).__name__, ":", failure)
print("--- retry stream ---")
print(again.getvalue())
print("--- end ---")
print("the foreign bytes after the retry:", repr(open(launch).read()))
for place in (places["distro"], places["justfile"], places["instance"]):
    print("lexists", os.path.lexists(place), place)
