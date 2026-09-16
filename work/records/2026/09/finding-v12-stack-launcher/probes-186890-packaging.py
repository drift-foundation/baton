"""W183883 claim186890 — the one probe that has to BUILD to mean anything.

`tests/tools/test_packaging.py` exists because the stand-ins could not see what
a real build has. So the only honest way to ask whether it holds the defect a
real build found -- an identity reporting `rpds.__file__`, an `__init__.py`
frozen into the archive and absent from disk -- is to put that line back, BUILD
the bundle, and run the module against it.

Baseline first [J1]: the pristine tree is built and the module passes against
that bundle. Then one line is reverted, the bundle is rebuilt, and the module
must fail on the native-validator assertion.

Run against an isolated COPY of the tree. Nothing here edits the checkout, and
the build goes to the copy's own `build/` directory.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-186890-packaging")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}
PREPARED = pathlib.Path("/home/sl/.local/state/baton-v12-venv/bin/python")

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)

TARGET = TREE / "python" / "tools" / "stack_command.py"
PRISTINE = TARGET.read_text()
DISTRO = TREE / "python" / "build" / "out" / "distro"

OWNED = """        from rpds import rpds as native
        said["native_rpds"] = getattr(native, "__file__", "imported")"""
REVERTED = """        import rpds
        said["native_rpds"] = getattr(rpds, "__file__", "imported")"""

CHECK = ("tests.tools.test_packaging.WhatTheBundleSaysItIs"
         ".test_the_native_validator_is_ONE_OF_THE_FILES_THIS_BUNDLE_BINDS")


def caches():
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def build():
    caches()
    if DISTRO.parent.exists():
        shutil.rmtree(DISTRO.parent)
    done = subprocess.run(
        [str(PREPARED.parent / "pyinstaller"), "--noconfirm", "--clean",
         "--distpath", "build/out", "--workpath", "build/work",
         "packaging/stack.spec"],
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=900)
    return done


def run():
    done = subprocess.run(
        [str(PREPARED), "-B", "-m", "unittest", CHECK],
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONPATH="src:.",
                 BATON_V12_STACK_DISTRO=str(DISTRO)))
    return done


started = time.monotonic()
TARGET.write_text(PRISTINE)
built = build()
assert built.returncode == 0, built.stderr[-800:]
baseline = run()
print("baseline on a pristine BUILD:",
      "PASSES" if baseline.returncode == 0 else "DOES NOT -- the probe is invalid")
assert "skipped" not in baseline.stderr.lower(), "the probe measured a SKIP"

text = TARGET.read_text()
assert OWNED in text
TARGET.write_text(text.replace(OWNED, REVERTED, 1))
rebuilt = build()
assert rebuilt.returncode == 0, rebuilt.stderr[-800:]
reverted = run()
TARGET.write_text(PRISTINE)

intended = ("AssertionError" in reverted.stderr
            and "__init__.py" in reverted.stderr)
killed = (baseline.returncode == 0 and reverted.returncode != 0 and intended)
print("reverted and REBUILT:",
      "FAILED (required)" if reverted.returncode else "PASSED -- PROVES NOTHING")
print("failed on the intended assertion:", intended)

TARGET.write_text(PRISTINE)
rebuilt_again = build()
restored = run()
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
seconds = time.monotonic() - started
(TREE.parent / "results-186890-packaging.json").write_text(json.dumps(
    {"probe": "R1-the-identity-reports-the-package-__init__-again",
     "check": CHECK,
     "baseline_passes_on_a_pristine_build": baseline.returncode == 0,
     "reverted_returncode": reverted.returncode,
     "failed_on_the_intended_assertion": intended,
     "what_the_reverted_bundle_reported":
         [one for one in reverted.stderr.splitlines() if "__init__.py" in one][:1],
     "valid_kill": killed, "restored_ok": restored.returncode == 0,
     "builds": 3, "total_seconds": round(seconds, 3)}, indent=2, sort_keys=True))
print("valid kill:", killed, "| seconds:", round(seconds, 3))
