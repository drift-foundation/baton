"""Measure W6636's composition by removing what it claims to establish.

A guard nothing observes is not established. Each mutation below breaks ONE
rule in the components this Job composes, and the composition module must fail.
A mutation nothing catches is a claim this Job has not earned.

The `__pycache__` drop per write is not decoration: these rewrites land inside
one filesystem timestamp tick, and CPython's mtime+size invalidation misses
that -- a harness without it measures the PREVIOUS build and reports whatever
it liked.
"""

import pathlib
import shutil
import subprocess
import sys

HOME = pathlib.Path("/home/sl/src/baton/v12/python")
SRC = HOME / "src" / "baton_v12" / "worker_manager"
MODULE = "tests.manager.test_lifecycle_composition"

MUTATIONS = [
    ("start: activation is not required", "attempts.py",
     '''    if attempt["assignment_generation"] is None:
        raise ContractRefusal(''',
     '''    if False:
        raise ContractRefusal('''),

    ("start: the adapter's plan is not held to the proved root", "attempts.py",
     "    _plan_agrees(adapter, attempt_id, inputs)\n",
     "    pass  # MUTATION\n"),

    ("start: the input root is not authorized", "attempts.py",
     "        authorize_input_root(store, attempt_id=attempt_id, inputs=inputs)",
     "        pass  # MUTATION"),

    ("start: a second start is not refused", "attempts.py",
     '''    if attempt["execution_runtime"] != "not-started":
        raise ContractRefusal(''',
     '''    if False:
        raise ContractRefusal('''),

    ("cancel: the runtime is stopped before the authority is fenced",
     "attempts.py",
     '''    fenced = port.cancel(expected, authority_operation_id, reason,
                         expected["work_ref"]["work_id"],
                         expected["work_ref"]["authority_uuid"])''',
     '''    _order_quiescence(store, agent, adapter, attempt_id, expected,
                      manager_operation_id)  # MUTATION: stop first
    fenced = port.cancel(expected, authority_operation_id, reason,
                         expected["work_ref"]["work_id"],
                         expected["work_ref"]["authority_uuid"])'''),

    ("reconcile: multiplicity is not a cancellation", "attempts.py",
     "    if len(found) > 1:\n        return _cancel(store, attempt_id,\n"
     "                       f\"{len(found)} runtimes carry",
     "    if False:\n        return _cancel(store, attempt_id,\n"
     "                       f\"{len(found)} runtimes carry"),

    ("reconcile: a restart starts a second runtime instead of adopting",
     "attempts.py",
     "    if len(found) == 1:\n",
     "    if False:\n"),

    ("oci: a consent container may mount the assignment's roots", "oci.py",
     '''MOUNTABLE = {"consent": (), "execution": ("inputs", "workspace")}''',
     '''MOUNTABLE = {"consent": ("inputs", "workspace"),
             "execution": ("inputs", "workspace")}'''),

    ("oci: the delivery's input bind is not held to the authorized root",
     "oci.py",
     "        self._mounts_the_authorized_root(taken.get(\"input_root\"))",
     "        pass  # MUTATION"),

    ("oci: a torn-down credential is reported for one never delivered",
     "oci.py",
     '''            # NOT `absent`, which is what the RUNTIME state beside this says.
            # One word meaning two things in one document is how a reader
            # concludes a credential was torn down because a container was.
            return {"lifecycle_state": "not-delivered"}''',
     '''            return {"lifecycle_state": "absent"}'''),

    ("oci: the input root is mounted writable", "oci.py",
     '''                 f"type=bind,source={source},target={target},"
                 f"readonly={'false' if writable else 'true'}"]''',
     '''                 f"type=bind,source={source},target={target},"
                 f"readonly=false"]'''),

    ("authorize: a superseded generation's root is accepted", "attempts.py",
     '''    if delivered["assignment_ref"] != expected:
        raise ContractRefusal(
            "stale-assignment", "generation",''',
     '''    if False:
        raise ContractRefusal(
            "stale-assignment", "generation",'''),

    ("reconcile: an unlistable runtime is called absent, not uncertain",
     "attempts.py",
     '''        return documents.runtime_uncertain(
            attempt_id=attempt_id, decision="uncertain",''',
     '''        return documents.runtime_uncertain(
            attempt_id=attempt_id, decision="absent",'''),

    ("reconcile: a cold restart calls an unlistable runtime absent",
     "attempts.py",
     '''    return documents.runtime_uncertain(
        attempt_id=attempt_id, decision="uncertain",''',
     '''    return documents.runtime_uncertain(
        attempt_id=attempt_id, decision="absent",'''),

    ("offers: a declined offer can still be claimed", "offers.py",
     '''        with held_secret(bearer):
            return _settle_terminal(store, issued, "declined",''',
     '''        with held_secret(bearer):
            return _settle_terminal(store, issued, "accepted",'''),

    ("attempts: a reconciliation label is dropped", "attempts.py",
     '''        generation=attempt["assignment_generation"],''',
     '''        generation=999,'''),

    ("oci: observe calls everything absent", "oci.py",
     '''    def observe(self, runtime_id):''',
     '''    def observe(self, runtime_id):
        return {"state": "absent", "why": "MUTATION", "mounts": None}'''),

    ("intake: cleanup destroys without an intake receipt", "intake.py",
     '''                value="blocked-on-intake")
    return documents.cleanup_blocked(''',
     '''                value="complete")
    return documents.cleanup_blocked('''),
]


def run():
    return subprocess.run(
        [sys.executable, "-B", "-m", "unittest", MODULE],
        cwd=HOME, capture_output=True, timeout=1800,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin",
             "HOME": "/home/sl"})


def drop_cache():
    for cache in HOME.rglob("__pycache__"):
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
        place = SRC / where
        original = place.read_text()
        if original.count(before) != 1:
            print(f"[SKIP  ] {name}\n         "
                  f"anchor appears {original.count(before)}x in {where}")
            unestablished.append(name + " (anchor)")
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
                  f"{', '.join(one for one in failed) or '?'}")
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
