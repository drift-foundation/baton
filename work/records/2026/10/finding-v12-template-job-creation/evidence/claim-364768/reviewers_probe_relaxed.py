"""The reviewer's own probe, with its one assumption relaxed.

`install_probe.py` calls `ConnectedCreationCase.installed`, which ASSERTS the
install succeeded -- so against the corrected candidate it raises before it
can report, because the install now refuses. This runs the same three cases
and reports what each one leaves behind, which is what the probe was asking.
Nothing else is changed: the same fixture, the same three setups, the same
four questions.
"""
import json
from pathlib import Path
from unittest import mock

from tests.tools.test_connected_creation import ConnectedCreationCase
from tools import instance


def probe(kind):
    case = ConnectedCreationCase()
    case.setUp()
    try:
        target = Path(case.state) / "install-inputs.json"
        external = Path(case.root) / "foreign.json"
        if kind == "existing":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("FOREIGN")
        if kind == "temp-symlink":
            external.write_text("FOREIGN")
            target.parent.mkdir(parents=True, exist_ok=True)
            Path(str(target) + ".tmp").symlink_to(external)
        if kind == "temp-partial-symlink":
            external.write_text("FOREIGN")
            target.parent.mkdir(parents=True, exist_ok=True)
            Path(str(target) + ".partial").symlink_to(external)
        refused = None
        if kind == "failed-selector":
            with mock.patch.object(
                    instance, "create",
                    side_effect=instance.InstanceRefusal(
                        "injected selector failure")):
                try:
                    case.installed()
                except AssertionError as caught:
                    refused = str(caught)[:120]
        else:
            try:
                case.installed()
            except AssertionError as caught:
                refused = str(caught)[:160]
        return {"kind": kind,
                "install_refused": refused is not None,
                "refusal": refused,
                "input_exists": target.exists(),
                "input_symlink": target.is_symlink(),
                "foreign_preserved": (external.read_text() == "FOREIGN"
                                      if external.exists()
                                      else target.exists()
                                      and target.read_text() == "FOREIGN"),
                "selector_exists": (Path(case.state) / "instance.json").exists()}
    finally:
        case.doCleanups()


for kind in ("existing", "temp-symlink", "temp-partial-symlink",
             "failed-selector"):
    print(json.dumps(probe(kind), indent=1))
