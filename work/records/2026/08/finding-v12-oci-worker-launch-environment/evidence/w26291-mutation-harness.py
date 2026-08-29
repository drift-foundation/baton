"""Measure W26291's launch-environment seam by removing its rules."""
import pathlib, shutil, subprocess, sys

HOME = pathlib.Path("/home/sl/src/baton/v12/python")
SRC = HOME / "src" / "baton_v12" / "worker_manager"
MODULES = ["tests.manager.test_oci", "tests.manager.test_attempts",
           "tests.manager.test_lifecycle_composition"]

MUTATIONS = [
    ("no environment reaches the engine at all", "oci.py",
     "    if environment is not None:\n"
     "        for key, value in _launch_environment(environment,"
     " posture).items():\n"
     "            argv += [\"--env\", f\"{key}={value}\"]",
     "    pass"),

    ("the manager stops carrying it across the seam", "attempts.py",
     '                                      "environment": environment}))',
     '                                      "environment": None}))'),

    ("the posture is taken from the caller instead of the adapter", "oci.py",
     '    return {"BATON_WORKER_POSTURE": posture, **{name: taken[name]',
     '    return {**{name: taken[name]'),

    ("an unexpected value passes through", "oci.py",
     '    taken = boundaries.document(supplied, "a worker launch environment",\n'
     '                                required=LAUNCH_VALUES)',
     '    taken = dict(supplied)'),

    ("an empty or non-text value is accepted", "oci.py",
     "        if type(value) is not str or not value:", "        if False:"),

    ("a control character is accepted", "oci.py",
     '        if "\\x00" in value or "\\n" in value:', "        if False:"),

    ("a value of any width is accepted", "oci.py",
     "        if len(value) > MAX_LAUNCH_VALUE:", "        if False:"),

    # The real mechanism: the rebuild over the FIXED tuple. Iterating the
    # caller's mapping instead is what would let two spellings of one launch
    # become two command lines.
    ("the environment follows the caller's mapping order", "oci.py",
     '    return {"BATON_WORKER_POSTURE": posture, **{name: taken[name]\n'
     '                                                for name in LAUNCH_VALUES}}',
     '    return {"BATON_WORKER_POSTURE": posture, **taken}'),

    ("the adapter's set drifts from the worker's", "oci.py",
     'WORKER_ENVIRONMENT = ("BATON_WORKER_POSTURE", "BATON_WORKER_SESSION",\n'
     '                      "BATON_WORKER_CONTRACT", "BATON_WORKER_ROLE")',
     'WORKER_ENVIRONMENT = ("BATON_WORKER_POSTURE", "BATON_WORKER_SESSION",\n'
     '                      "BATON_WORKER_CONTRACT", "BATON_WORKER_TASK")'),
]


def run():
    return subprocess.run(
        [sys.executable, "-B", "-m", "unittest", *MODULES],
        cwd=HOME, capture_output=True, timeout=1200,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin", "HOME": "/home/sl"})


def drop_cache():
    for cache in HOME.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def main():
    drop_cache()
    base = run()
    print(f"BASELINE  {'OK' if base.returncode == 0 else 'FAILING'}\n")
    if base.returncode != 0:
        print(base.stderr.decode()[-2500:]); return 1
    missed = []
    for name, where, before, after in MUTATIONS:
        place = SRC / where
        original = place.read_text()
        if original.count(before) != 1:
            print(f"[ANCHOR] {name}: {original.count(before)}x"); missed.append(name); continue
        place.write_text(original.replace(before, after)); drop_cache()
        try:
            found = run()
        finally:
            place.write_text(original); drop_cache()
        if found.returncode == 0:
            print(f"[UNSEEN] {name}"); missed.append(name)
        else:
            tail = found.stderr.decode()
            failed = sorted({l.split(" ")[1] for l in tail.splitlines()
                             if l.startswith(("FAIL: ", "ERROR: "))})
            print(f"[caught] {name}\n         {', '.join(failed)[:130]}")
    print()
    if missed:
        print(f"{len(missed)} UNESTABLISHED:"); [print(" -", one) for one in missed]; return 1
    print(f"all {len(MUTATIONS)} mutations caught"); return 0


if __name__ == "__main__":
    sys.exit(main())
