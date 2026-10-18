#!/usr/bin/env python3
"""Drive the EXACT candidate's `record` verbs at the real command boundary.

Review 2026-10-18T09-12-00Z asks for exact-candidate packaged-command evidence,
because an older bundle cannot establish a changed command's behaviour.

WHAT THIS IS AND IS NOT. `packaging/stack.spec` freezes exactly one script --
`tools/stack_command.py`, with `pathex` of the distribution root and its `src`
-- so this driver runs that same script, in a subprocess, with that same import
path. Argv parsing, verb dispatch, the JSON written to stdout and the exit code
are therefore the packaged command's own, measured on the candidate's bytes.

WHAT IS NOT MEASURED, stated rather than implied: FREEZING. PyInstaller is not
installed in this environment, so no bundle was built from these bytes and this
is not a frozen-bundle run. Fetching PyInstaller would reach an external index
and change the environment, which I did not do. The already disclosed build
stamp limitation is unchanged and separate.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

CANDIDATE = "/home/sl/baton-instances/w321688-321989-candidate"
SCRIPT = os.path.join(CANDIDATE, "tools", "stack_command.py")


def command(*operands, cwd):
    """The packaged entry script, by the spec's own path, as a subprocess."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [CANDIDATE, os.path.join(CANDIDATE, "src")])
    done = subprocess.run([sys.executable, SCRIPT, *operands], cwd=cwd,
                          env=env, capture_output=True, text=True,
                          timeout=180)
    return done.returncode, done.stdout, done.stderr


def selector_state(out):
    try:
        return (json.loads(out).get("restored_selector") or {}).get("state")
    except ValueError:
        return None


def faults(out):
    try:
        return json.loads(out).get("faults")
    except ValueError:
        return None


def main():
    home = tempfile.mkdtemp(prefix="packaged-command-")
    results = []
    try:
        # THE REAL INSTANCE, by the real producer and the real layout --
        # `tools.instance.emit`/`layout` and the supported store openers, the
        # same sources the focused cases use. `record` has no verb that stands
        # a deployment up, and handcrafting a selector here would prove the
        # command agrees with a double.
        sys.path[:0] = [CANDIDATE, os.path.join(CANDIDATE, "src")]
        from tools import instance as contract
        from baton_v12.authority import Authority
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore

        uuid = "a" * 32
        destination = os.path.join(home, "instance")
        places = contract.layout(destination)
        os.makedirs(places["stores"])
        authority = Authority.create(places["authority_store"],
                                     authority_uuid=uuid)
        authority.create_work(uuid[:8] + "-W1", "impl", operation_id="op-c")
        authority.dispose()
        clock = (lambda: "2026-10-18T09:00:00.000Z")
        JobStore.open(places["job_store"], authority_uuid=uuid,
                      incarnation="jobs-1", clock=clock).close()
        ControlStore.open(places["control_store"], incarnation="manager-1",
                          clock=clock).close()
        with open(places["deployment"], "w", encoding="utf-8") as handle:
            json.dump({"schema": "baton.v12.deployment/1"}, handle)
        for name in ("state", "logs", "repository"):
            os.makedirs(places[name], exist_ok=True)
            with open(os.path.join(places[name], "kept.txt"), "w",
                      encoding="utf-8") as handle:
                handle.write(f"retained {name}\n")
        os.makedirs(os.path.dirname(places["command"]), exist_ok=True)
        with open(places["command"], "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nexit 0\n")
        described = contract.emit(
            destination, authority_uuid=uuid,
            identity={"version": "12.0.0", "command": "baton-v12-stack"},
            runtime={"files": 81, "digest": "c1ef3d23"},
            now="2026-10-18T09:00:00.000Z")
        wrong = contract.malformed(described, places["instance"])
        if wrong:
            print("the fixture is not a selector the real validator accepts:",
                  wrong, file=sys.stderr)
            return 2
        instance = places["instance"]
        with open(instance, "w", encoding="utf-8") as handle:
            json.dump(described, handle)

        def manifested():
            code, out, err = command("record", "recovery-manifest",
                                     "--instance", instance, cwd=home)
            return code, out, err

        code, out, err = manifested()
        results.append({"what": "recovery-manifest on the live instance",
                        "exit": code, "schema": (json.loads(out)["schema"]
                                                 if code == 0 else None),
                        "records_selector_document":
                            code == 0
                            and isinstance(json.loads(out).get(
                                "instance_document"), dict)})
        if code != 0:
            print("manifest refused:", err[-600:], file=sys.stderr)
            return 2
        manifest_bytes = out
        manifest = os.path.join(home, "manifest.json")
        with open(manifest, "w", encoding="utf-8") as handle:
            handle.write(manifest_bytes)

        restored = os.path.join(home, "restored")
        pristine = os.path.join(home, "pristine")
        shutil.copytree(destination, pristine, symlinks=True)
        # THE ORIGINAL IS GONE from here on, which is both what a real recovery
        # looks like and the only way the writer question can be answered: with
        # the old destination still present, every check correctly reports
        # writer uncertainty and no scenario could ever reach exit 0.
        shutil.rmtree(destination)

        def fresh():
            if os.path.isdir(restored):
                shutil.rmtree(restored)
            shutil.copytree(pristine, restored, symlinks=True)
            with open(manifest, "w", encoding="utf-8") as handle:
                handle.write(manifest_bytes)

        def checked():
            return command("record", "recovery-check", "--manifest", manifest,
                           "--root", restored, cwd=home)

        def selector_of(root):
            return os.path.join(root, os.path.relpath(places["instance"],
                                                      destination))

        def rewrite(path, **members):
            with open(path, "r", encoding="utf-8") as handle:
                held = json.load(handle)
            held.update(members)
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(held, handle)
            return held

        # 1 -- the complete restore, unchanged, still clean.
        fresh()
        code, out, err = checked()
        results.append({"what": "complete unchanged restore",
                        "exit": code, "faults": faults(out),
                        "selector": selector_state(out),
                        "schema_compatible":
                            json.loads(out).get("schema_compatible")
                            if out.strip() else None})

        # 2 -- the restored selector REMOVED.
        fresh()
        os.remove(selector_of(restored))
        code, out, err = checked()
        results.append({"what": "restored selector removed",
                        "exit": code, "faults": faults(out),
                        "selector": selector_state(out)})

        # 3 -- the restored selector naming ANOTHER authority.
        fresh()
        rewrite(selector_of(restored), authority_uuid="f" * 32)
        code, out, err = checked()
        results.append({"what": "restored selector names another authority",
                        "exit": code, "faults": faults(out),
                        "selector": selector_state(out)})

        # 4 -- the supported rewrite: relocated to THIS root.
        fresh()
        rewrite(selector_of(restored), destination=restored)
        code, out, err = checked()
        results.append({"what": "selector relocated to the restored root",
                        "exit": code, "faults": faults(out),
                        "selector": selector_state(out)})

        # 5 -- relocated SOMEWHERE ELSE, which is not the supported rewrite.
        fresh()
        rewrite(selector_of(restored),
                destination=os.path.join(home, "somewhere-else"))
        code, out, err = checked()
        results.append({"what": "selector relocated to a third path",
                        "exit": code, "faults": faults(out),
                        "selector": selector_state(out)})

        # 6 -- JSON null, and the representative non-objects. Review
        #      2026-10-18T09-29-00Z P2: `null` parsed, skipped the contract
        #      validator and raised TypeError out of the public command.
        for body, named in (("null", "NoneType"), ("[]", "list"),
                            ('"instance"', "str"), ("3", "int"),
                            ("true", "bool")):
            fresh()
            with open(selector_of(restored), "w", encoding="utf-8") as handle:
                handle.write(body)
            code, out, err = checked()
            held = {}
            try:
                held = json.loads(out).get("restored_selector") or {}
            except ValueError:
                pass
            results.append({
                "what": f"restored selector holding JSON {body}",
                "exit": code, "faults": faults(out),
                "selector": held.get("state"),
                "validator_named_the_type": named in (held.get("why") or ""),
                "no_traceback": "Traceback" not in err})

        # 7 -- a manifest without the `/3` selector document.
        fresh()
        held = json.loads(manifest_bytes)
        held.pop("instance_document", None)
        with open(manifest, "w", encoding="utf-8") as handle:
            json.dump(held, handle)
        code, out, err = checked()
        results.append({"what": "manifest lacking the /3 selector document",
                        "exit": code, "faults": faults(out),
                        "selector": selector_state(out)})

        print(json.dumps({
            "schema": "baton.w321688.packaged-command-evidence/1",
            "entry_script": SCRIPT,
            "boundary": "the spec's own frozen script, run as a subprocess "
                        "with the spec's own import path",
            "frozen_bundle_built": False,
            "why_not": "PyInstaller is not installed in this environment and "
                       "installing it would reach an external index",
            "results": results}, indent=1, sort_keys=True))
        return 0
    finally:
        shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
