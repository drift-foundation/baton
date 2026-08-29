"""Measure W26291's LAUNCH-DOCUMENT guards by removing them.

A guard nothing observes is not established. Each mutation below breaks ONE
rule the live contract promises; the suites must fail.

WHAT THIS REPLACED. `evidence/w26291-mutation-harness.py` measured the
SUPERSEDED transport -- four `BATON_WORKER_*` values on a command line -- and
is kept beside this file as history rather than deleted. Its nine mutations
say nothing about the contract that is now live, and the review was explicit
that a green measurement of a retired design is not acceptance evidence.

BOTH SIDES ARE MUTATED, because the contract has two ends and the whole defect
this Work exists for was two closed components that could not meet. The manager
half lives in `v12/python/src/baton_v12/worker_manager/`; the worker half is
`v12/worker/baton_worker.py`, which is a different tree and a different
program.

THE REAL-ENGINE SUITE IS IN THE MEASUREMENT. A mutation caught only by
in-process fixtures is a rule established against material this repository
wrote for itself, and half of these rules -- the read-only bind, the fixed
mount target, the file mode a container has to be able to read -- are only
true of a real container. `test_worker_container` rebuilds the image from the
recipe per class, so a mutated worker really is the worker under test.

`__pycache__` is dropped per write: these rewrites land inside one filesystem
timestamp tick and CPython's mtime+size invalidation misses that.
"""

import pathlib
import shutil
import subprocess
import sys

HOME = pathlib.Path("/home/sl/src/baton/v12/python")
SRC = HOME / "src" / "baton_v12" / "worker_manager"
WORKER = pathlib.Path("/home/sl/src/baton/v12/worker")
# `test_credentials` is in the measurement because the launch document and the
# credential delivery settle TOGETHER on a refused start -- the second
# re-review found a refusal that bypassed that settlement, and the cases
# covering it live there. A mutation nothing runs is not measured.
MODULES = ["tests.manager.test_launch", "tests.manager.test_oci",
           "tests.manager.test_credentials",
           "tests.manager.test_worker_image",
           "tests.manager.test_worker_container"]

MUTATIONS = [
    # -- the manager authors and freezes the document ------------------------
    ("the document is not walked for live secrets", "launch.py",
     '    check_no_durable_secret(document, what="a worker launch document")',
     "    pass"),

    ("the document is written writable", "launch.py",
     "READ_ONLY_FILE = 0o444",
     "READ_ONLY_FILE = 0o644"),

    # -- re-review [P1/P0]: the invariants the first measurement did not have -
    ("the mode is REQUESTED at creation rather than established",
     "launch.py",
     "            _write_whole(handle, payload)\n"
     "            os.fchmod(handle, READ_ONLY_FILE)",
     "            _write_whole(handle, payload)"),

    # Second re-review [P1]: the refusal was there and it BYPASSED THE
    # SETTLEMENT, so a canonical adapter already holding a credential delivery
    # had its bearer stranded. This restores that shape exactly.
    ("a missing launch document refuses without settling what exists",
     "oci.py",
     "            self._refused_start(\n"
     "                labels,\n"
     "                f\"this start carries no launch document; the worker "
     "reads \"",
     "            _denied(\n"
     "                f\"this start carries no launch document; the worker "
     "reads \""),

    # RE-ANCHORED after the second re-review moved this refusal through the
    # settlement. The harness reported the stale anchor as 0x rather than
    # mutating something else, which is the check doing its job.
    ("a start may carry no launch document at all", "oci.py",
     "        if self.launch_delivery is None:\n"
     "            self._refused_start(",
     "        if False:\n"
     "            self._refused_start("),

    ("the launch root is never ended", "oci.py",
     "        if launch.discard(self.launch_delivery.root):\n"
     "            return {\"lifecycle_state\": \"torn-down\"}",
     "        if True:\n"
     "            return {\"lifecycle_state\": \"torn-down\"}"),

    # Third review [P2]: a listing that FAILED is a different branch from one
    # that succeeded and named a runtime. The mutation below measures the
    # common launch ending; this one measures whether an inventory this manager
    # could not read becomes proved absence.
    ("an unusable inventory listing is treated as proved absence", "oci.py",
     "        except ContractRefusal as refusal:\n"
     "            why = refusal.message",
     "        except ContractRefusal as refusal:\n"
     "            why = None"),

    ("the launch root is discarded without proving absence", "oci.py",
     "        if not proved_absent:\n"
     "            return {\"lifecycle_state\": \"unresolved\", \"why\": why}",
     "        if False:\n"
     "            return {\"lifecycle_state\": \"unresolved\", \"why\": why}"),

    ("describe reports fewer members than the document has",
     "baton_worker.py",
     "    return {name: document[name] for name in LAUNCH_MEMBERS}",
     "    return {name: document[name] for name in LAUNCH_MEMBERS\n"
     "            if name != \"schema\"}"),

    ("the document is written owner-only, which no container can read",
     "launch.py",
     "READ_ONLY_FILE = 0o444",
     "READ_ONLY_FILE = 0o400"),

    ("an existing launch root is written into rather than refused",
     "launch.py",
     "    if os.path.lexists(root):",
     "    if False:"),

    ("the source open is neither exclusive nor no-follow", "launch.py",
     "                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | "
     "os.O_NOFOLLOW,",
     "                         os.O_WRONLY | os.O_CREAT | os.O_TRUNC,"),

    # NOT the no-progress refusal, and the difference is measured rather than
    # chosen: disabling that refusal makes the loop SPIN, so the mutation
    # would hang the harness instead of failing a case. What this removes is
    # the rule the refusal protects -- that the writer reads the answer at all.
    ("a short write delivers a truncated document", "launch.py",
     "        written += step",
     "        written = len(payload)"),

    # -- the adapter mounts it, read-only, at the fixed target ---------------
    ("the launch document is mounted writable", "oci.py",
     '        argv += ["--mount",\n'
     '                 f"type=bind,source={source},target={target},'
     'readonly=true"]\n'
     "    # THE IMAGE, LAST and by digest.",
     '        argv += ["--mount",\n'
     '                 f"type=bind,source={source},target={target},'
     'readonly=false"]\n'
     "    # THE IMAGE, LAST and by digest."),

    ("the mount target is the delivery's word rather than the contract's",
     "oci.py",
     "    if target != launch.LAUNCH_TARGET:",
     "    if False:"),

    ("an assignment mount may land on the launch document", "oci.py",
     "            if taken == target or _within(target, taken):\n"
     "                _denied(f\"a launch document lands on "
     "{name_value(target)}, \"",
     "            if False:\n"
     "                _denied(f\"a launch document lands on "
     "{name_value(target)}, \""),

    ("the adapter accepts a delivery it did not materialize", "oci.py",
     "        if launch_delivery is not None \\\n"
     "                and type(launch_delivery) is not launch.LaunchDelivery:",
     "        if False:"),

    # -- the worker reads it, and reads nothing else -------------------------
    ("the launch open follows a link", "baton_worker.py",
     "        descriptor = os.open(place,\n"
     "                             os.O_RDONLY | os.O_NOFOLLOW | "
     "os.O_NONBLOCK)",
     "        descriptor = os.open(place, os.O_RDONLY)"),

    ("a pipe at the launch path blocks the open", "baton_worker.py",
     "        descriptor = os.open(place,\n"
     "                             os.O_RDONLY | os.O_NOFOLLOW | "
     "os.O_NONBLOCK)",
     "        descriptor = os.open(place, os.O_RDONLY | os.O_NOFOLLOW)"),

    ("the descriptor's regular-file proof is gone", "baton_worker.py",
     "        if not stat.S_ISREG(os.fstat(descriptor).st_mode):",
     "        if False:"),

    ("the read is not bounded", "baton_worker.py",
     "        raw = os.read(descriptor, MAX_LAUNCH_BYTES + 1)",
     "        raw = os.read(descriptor, 1 << 30)"),

    ("a writable launch document is accepted", "baton_worker.py",
     "        writable = os.open(place, os.O_WRONLY | os.O_NOFOLLOW)",
     "        raise OSError(0, 'no write-open attempted')\n"
     "        writable = os.open(place, os.O_WRONLY | os.O_NOFOLLOW)"),

    ("the member set is not closed", "baton_worker.py",
     "    if missing or extra:\n"
     "        raise WorkerFault(\n"
     '            "launch",',
     "    if False:\n"
     "        raise WorkerFault(\n"
     '            "launch",'),

    ("a document from another generation is read anyway", "baton_worker.py",
     '    if document["schema"] != LAUNCH_SCHEMA:',
     "    if False:"),

    ("a launch value is not held to its type or its ceiling",
     "baton_worker.py",
     "        if type(value) is not str or not value:\n"
     "            raise WorkerFault(\n"
     '                "launch",\n'
     '                f"{place} carries a {name} that is not bounded '
     'non-empty text")',
     "        if False:\n"
     "            raise WorkerFault(\n"
     '                "launch",\n'
     '                f"{place} carries a {name} that is not bounded '
     'non-empty text")'),

    ("this runtime answers an operation it is not entitled to",
     "baton_worker.py",
     "    if operation not in OPERATIONS:",
     "    if False:"),
]


def place_of(where):
    return (WORKER if where == "baton_worker.py" else SRC) / where


def run():
    return subprocess.run(
        [sys.executable, "-B", "-m", "unittest", *MODULES],
        cwd=HOME, capture_output=True, timeout=2400,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin", "HOME": "/home/sl"})


def drop_cache():
    for cache in list(HOME.rglob("__pycache__")) + \
            list(WORKER.rglob("__pycache__")):
        shutil.rmtree(cache, ignore_errors=True)


def main():
    drop_cache()
    base = run()
    print(f"BASELINE  {'OK' if base.returncode == 0 else 'FAILING'}\n")
    if base.returncode != 0:
        print(base.stderr.decode()[-3000:])
        return 1
    unestablished = []
    for name, where, before, after in MUTATIONS:
        target = place_of(where)
        original = target.read_text()
        if original.count(before) != 1:
            print(f"[ANCHOR] {name}: {original.count(before)}x in {where}")
            unestablished.append(f"{name} (anchor)")
            continue
        target.write_text(original.replace(before, after))
        drop_cache()
        try:
            found = run()
        finally:
            target.write_text(original)
            drop_cache()
        if found.returncode == 0:
            print(f"[UNSEEN] {name}")
            unestablished.append(name)
        else:
            tail = found.stderr.decode()
            failed = sorted({line.split(" ")[1] for line in tail.splitlines()
                             if line.startswith(("FAIL: ", "ERROR: "))})
            print(f"[caught] {name}\n         "
                  f"{', '.join(failed)[:300] or '?'}")
    print()
    if unestablished:
        print(f"{len(unestablished)} UNESTABLISHED:")
        for one in unestablished:
            print(f"  - {one}")
        return 1
    print(f"all {len(MUTATIONS)} mutations caught")
    return 0


if __name__ == "__main__":
    sys.exit(main())
