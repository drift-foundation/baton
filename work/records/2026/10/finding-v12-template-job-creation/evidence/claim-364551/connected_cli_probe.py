"""Probe: the real INSTALLER, then the real CLI creation."""
import io
import json
import os
from pathlib import Path
from unittest import mock

from tests.tools import test_bootstrap as suite
from tools import bootstrap, job_manager


class Case(suite.ValidFixture):
    def runTest(self):
        pass

    def stand_in_runtime(self):
        source = Path(self.root) / "stand-in-distro"
        (source / "_internal").mkdir(parents=True, exist_ok=True)
        (source / "baton-v12-stack").write_text("a stand-in for the launcher")
        (source / "_internal" / "lib.so").write_text("stand-in bytes")
        return str(source)


case = Case()
case.setUp()
try:
    destination = case.state
    places = bootstrap.layout(destination)
    document = case.document()
    document.pop("state_root", None)
    inputs = os.path.join(case.root, "install-inputs.json")
    Path(inputs).write_text(json.dumps(document))
    said = {"command": "baton-v12-stack", "frozen": True,
            "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
            "schema_assets": {"agent-session-1.0": 10,
                              "worker-control-1.0": 20},
            "native_rpds": str(Path(case.stand_in_runtime())
                               / "_internal" / "lib.so")}
    out = io.StringIO()
    with mock.patch.object(bootstrap, "_identity_of",
                           lambda command, runtime=None, distro=None: said):
        code = bootstrap.main(
            ["--inputs", inputs, "--destination", destination,
             "--distro", case.stand_in_runtime(), "--no-repositories"],
            stream=out)
    print("install exit:", code)
    print("install said:", out.getvalue()[-400:])
    print("files:", sorted(os.listdir(destination)))
    from baton_v12.worker_manager import ControlStore
    from tools import job_manager
    from tools.creation_ports import instance_identity

    owned = instance_identity(destination)
    with ControlStore.open(owned["control_store"], incarnation="manager-1",
                           clock=lambda: "2026-09-02T00:00:00.000Z"):
        pass
    argv = ["--store", owned["job_store"], "--incarnation", "cli-1",
            "--authority-uuid", owned["authority_uuid"],
            "create", "--instance", destination,
            "--control", owned["control_store"],
            "--authority", owned["authority_store"],
            "--task", "cli-first", "--statement", "The first CLI task.",
            "--acceptance", "The CLI creates a bound, servable Job.",
            "--work-scope", "v12/python/tools/job_manager.py"]
    said = io.StringIO()
    code = job_manager.main(argv, stream=said)
    print("CLI exit:", code)
    print("CLI said:", said.getvalue()[:1500])
    configuration = json.loads(
        open(os.path.join(destination, "deployment.json")).read())
    print("bindings now:", json.dumps(
        configuration.get("job_bindings"), indent=1)[:600])
    inputs_now = json.loads(
        open(os.path.join(destination, "install-inputs.json")).read())
    print("install jobs now:", json.dumps(inputs_now.get("jobs"))[:400])
    # REPLAY: the same argv again.
    again = io.StringIO()
    print("replay exit:", job_manager.main(argv, stream=again))
    print("replay said:", again.getvalue()[:600])
    configuration = json.loads(
        open(os.path.join(destination, "deployment.json")).read())
    print("bindings after replay:",
          len(configuration.get("job_bindings") or []))
finally:
    case.doCleanups()
