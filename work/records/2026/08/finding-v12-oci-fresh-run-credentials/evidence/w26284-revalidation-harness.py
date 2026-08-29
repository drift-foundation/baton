"""W26284 PLAN 1: revalidate W6634's credential spike by REMOVING its rules.

The finding says provisional code is evidence, not accepted implementation, and
last Work's measurement found a guard that had been sitting in this same spike
with nothing observing it -- standing in for a named acceptance clause. So the
revalidation is a measurement rather than a reading: each rule the finding names
is removed, and a rule nothing notices is one this provider has not established
however carefully it is written.

Nothing here is a fix. This is the search.
"""

import pathlib
import shutil
import subprocess
import sys

HOME = pathlib.Path("/home/sl/src/baton/v12/python")
SRC = HOME / "src" / "baton_v12" / "worker_manager"
MODULES = ["tests.manager.test_credentials", "tests.manager.test_oci",
           "tests.manager.test_secrets", "tests.manager.test_text_sweep",
           "tests.manager.test_credentials_engine"]

MUTATIONS = [
    # -- "registered as live BEFORE any materialization" ----------------------
    ("the bearer is registered live AFTER it is written", "credentials.py",
     "                # LIVE BEFORE IT IS ANYWHERE ELSE.\n"
     "                remember_secret(bearer)\n"
     "                bearers[name] = bearer\n",
     "                bearers[name] = bearer\n"),
    ("...and registered only once the file is closed", "credentials.py",
     "                finally:\n                    os.close(handle)\n",
     "                finally:\n                    os.close(handle)\n"
     "                remember_secret(bearer)\n"),

    ("the bearer is never registered live at all", "credentials.py",
     "                # LIVE BEFORE IT IS ANYWHERE ELSE.\n"
     "                remember_secret(bearer)\n",
     "                pass\n"),

    # -- "mode-0600 files beneath an assignment-private mode-0700 root" -------
    ("credential files are world-readable", "credentials.py",
     "VOLATILE_FILE = 0o600", "VOLATILE_FILE = 0o644"),

    ("the volatile root is world-traversable", "credentials.py",
     "VOLATILE_DIR = 0o700", "VOLATILE_DIR = 0o755"),

    ("the mode is applied after the open rather than at it", "credentials.py",
     "                handle = os.open(place, os.O_WRONLY | os.O_CREAT | "
     "os.O_EXCL,\n                                 VOLATILE_FILE)",
     "                handle = os.open(place, os.O_WRONLY | os.O_CREAT | "
     "os.O_EXCL,\n                                 0o666)\n"
     "                os.chmod(place, VOLATILE_FILE)"),

    ("an existing name is written through", "credentials.py",
     "os.O_WRONLY | os.O_CREAT | os.O_EXCL,", "os.O_WRONLY | os.O_CREAT,"),

    ("an existing credential root is reused", "credentials.py",
     "        if os.path.exists(root):", "        if False:"),

    # -- the slot grammar, which is a containment rule ------------------------
    ("a slot name may leave the root it names an entry of", "credentials.py",
     r'_SLOT = re.compile(r"\A[a-z0-9][a-z0-9._-]{0,62}\Z")',
     r'_SLOT = re.compile(r"\A[^\x00]{1,63}\Z")'),

    # -- the bounds -----------------------------------------------------------
    ("a bearer of any width is written", "credentials.py",
     "                if len(bearer) > MAX_BEARER:", "                if False:"),

    ("an assignment may authorize unboundedly many slots", "credentials.py",
     "MAX_SLOTS = 16", "MAX_SLOTS = 100000"),

    # -- "failure preserves live-secret tracking and converges to absence" ----
    ("a failed materialization leaves its root behind", "credentials.py",
     "            if _discard(root):\n"
     "                for value in bearers.values():\n"
     "                    forget_secret(value)\n"
     "                raise",
     "            if True:\n"
     "                for value in bearers.values():\n"
     "                    forget_secret(value)\n"
     "                raise"),

    ("a failed materialization forgets BEFORE it removes", "credentials.py",
     "            if _discard(root):\n"
     "                for value in bearers.values():\n"
     "                    forget_secret(value)\n"
     "                raise",
     "            for value in bearers.values():\n"
     "                forget_secret(value)\n"
     "            if _discard(root):\n"
     "                raise"),

    # -- review [P1]: the removal's ANSWER, not merely its ORDER --------------
    #
    # The two above watch a SUCCESSFUL removal, which is how nineteen
    # mutations were caught while a filesystem refusal still disarmed the
    # registry over bytes still on disk. This one makes the proof vacuous
    # exactly the way ignoring the boolean did.
    ("a failed materialization forgets whether or not the root is gone",
     "credentials.py",
     "            if _discard(root):\n"
     "                for value in bearers.values():\n"
     "                    forget_secret(value)\n"
     "                raise",
     "            _discard(root)\n"
     "            for value in bearers.values():\n"
     "                forget_secret(value)\n"
     "            raise"),

    # -- "forgets a bearer only after positive absence is established" -------
    ("teardown forgets the bearer before proving the file is gone",
     "credentials.py",
     "        for source, _target in delivery.mounts():\n"
     "            _gone(source, \"a volatile credential\", os.remove)",
     "        for value in delivery.bearers().values():\n"
     "            forget_secret(value)\n"
     "        for source, _target in delivery.mounts():\n"
     "            _gone(source, \"a volatile credential\", os.remove)"),

    ("removal is trusted rather than proved", "credentials.py",
     "    if os.path.lexists(place):", "    if False:"),

    ("teardown does not remove the lifecycle record", "credentials.py",
     "        _gone(self.state_path(delivery.attempt_id),\n"
     "              \"a credential lifecycle record\", os.remove)",
     "        pass"),

    # -- "mounted read-only at the fixed worker path" -------------------------
    # ANCHORED THROUGH THE WORD "credential", because W26291 added a second
    # read-only mount for the launch document whose composition AND whose
    # collision prose are byte-identical to this one -- so both the bare argv
    # line and the refusal tail above it match twice. The harness reported
    # that as an anchor failure rather than silently mutating the wrong one,
    # which is the check doing its job; the duplication itself belongs to
    # W26291 and is named here rather than edited from this Work.
    ("a credential is mounted writable", "oci.py",
     '                _denied(f"a credential mount lands on {name_value(target)}, "\n                        f"which this assignment already mounts; the worker "\n                        f"would read one of the two and neither this manager "\n                        f"nor the engine says which")\n        argv += ["--mount",\n                 f"type=bind,source={source},target={target},readonly=true"]',
     '                _denied(f"a credential mount lands on {name_value(target)}, "\n                        f"which this assignment already mounts; the worker "\n                        f"would read one of the two and neither this manager "\n                        f"nor the engine says which")\n        argv += ["--mount",\n                 f"type=bind,source={source},target={target},readonly=false"]'),

    ("a credential mount may land anywhere", "oci.py",
     "    if len(pairs) > credentials.MAX_SLOTS:",
     "    if False and len(pairs) > credentials.MAX_SLOTS:"),

    # -- "never in argv, environment, labels, durable records, diagnostics" ---
    #
    # Review [P1]: the sweep used to live in `run_vector` and covered only the
    # vector that function composed, so the duplicate probe reached the engine
    # first and unswept. It now has one owner, and this removes it there --
    # which is the only place that can be removed, because it is the only
    # place it exists.
    ("no engine vector is swept for a live bearer", "oci.py",
     '        check_no_durable_secret(list(argv), what="an engine vector")',
     "        pass"),
]


def run():
    return subprocess.run(
        [sys.executable, "-B", "-m", "unittest", *MODULES],
        cwd=HOME, capture_output=True, timeout=900,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin", "HOME": "/home/sl"})


def drop_cache():
    for cache in HOME.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def main():
    drop_cache()
    base = run()
    print(f"BASELINE  {'OK' if base.returncode == 0 else 'FAILING'}\n")
    if base.returncode != 0:
        print(base.stderr.decode()[-2500:])
        return 1
    unestablished = []
    for name, where, before, after in MUTATIONS:
        place = SRC / where
        original = place.read_text()
        if original.count(before) != 1:
            print(f"[ANCHOR] {name}: {original.count(before)}x in {where}")
            unestablished.append(f"{name} (anchor)")
            continue
        place.write_text(original.replace(before, after))
        drop_cache()
        try:
            found = run()
        finally:
            place.write_text(original)
            drop_cache()
        if found.returncode == 0:
            print(f"[UNSEEN] {name}")
            unestablished.append(name)
        else:
            tail = found.stderr.decode()
            failed = sorted({line.split(" ")[1] for line in tail.splitlines()
                             if line.startswith(("FAIL: ", "ERROR: "))})
            print(f"[caught] {name}\n         "
                  f"{', '.join(failed)[:150] or '?'}")
    print()
    if unestablished:
        print(f"{len(unestablished)} UNESTABLISHED of {len(MUTATIONS)}:")
        for one in unestablished:
            print(f"  - {one}")
        return 1
    print(f"all {len(MUTATIONS)} mutations caught")
    return 0


if __name__ == "__main__":
    sys.exit(main())
