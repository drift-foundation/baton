"""Successor Stage B preparation: automatically seed, then emit engine vectors.

No subprocess/engine/provider invocation. Actual credential access requires the
owner-selected source/copy ruling and claim; --check verifies code only.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent


def checked_source(source):
    source = Path(source).resolve()
    for row in json.loads((HERE / "lifecycle-files.json").read_text())["files"]:
        path = source / row["path"]
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("lifecycle source identity disagrees: " + row["path"])
    return source


def commands(selection):
    previous = HERE / "render_commands.py"
    pin = json.loads((HERE / "renderer-pin.json").read_text())
    if hashlib.sha256(previous.read_bytes()).hexdigest() != pin["render_commands_sha256"]:
        raise ValueError("predecessor renderer identity disagrees")
    spec = importlib.util.spec_from_file_location("qualified_predecessor", previous)
    renderer = importlib.util.module_from_spec(spec); spec.loader.exec_module(renderer)
    return renderer.render(selection, "live")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("selection")
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    s = json.loads(Path(a.selection).read_text())
    source = checked_source(s["lifecycle_source"])
    if a.check:
        print(json.dumps({"code_verified": True, "credentials_read": False, "execution_selected": False}))
        return
    if not s.get("authorization_credential_copy") or not s.get("credential_source_configuration"):
        raise ValueError("credential copy/source configuration is unselected")
    vectors = commands(s)  # All existing Stage B gates before source access.
    sys.path[:0] = [str(source / "v12/python"), str(source / "v12/python/src")]
    from tools.qualification_credentials import prepare_selected
    result = prepare_selected(s, s["credential_source_configuration"])
    vectors["credential_preparation"] = result
    vectors["prerequisites"] += "; successor credential preparation completed; original context/instruction staging, root isolation, cessation and cleanup requirements still apply"
    print(json.dumps(vectors, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError):
        raise SystemExit("qualification preparation refused; retain private state for recovery, do not reseed or retry automatically") from None
