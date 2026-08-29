#!/usr/bin/env python3
"""W32648 — every guard the failed-start ending adds, measured BY REMOVAL.

Run from `v12/python`:

    PYTHONPATH=src python3 <this file>

Nothing is left modified: every source is restored from the bytes read at the
start, in a `finally`, whatever happens.
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path("src/baton_v12/worker_manager")
INTAKE = ROOT / "intake.py"
ATTEMPTS = ROOT / "attempts.py"
SUITE = "tests.manager.test_attempts"

MUTATIONS = [
    ("the record is what authorizes the removal", INTAKE,
     '''    if held is None or held.get("state") != "committed" \\
            or held.get("result") is None:''',
     '''    if False:''', SUITE),
    ("the assignment is fenced before anything is destroyed", INTAKE,
     '''    if live == expect:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} is still the live assignment "
            f"for {expect['participant']} generation {expect['generation']}; "
            f"a failed start is fenced at the authority before anything is "
            f"destroyed, and this assignment is still authorized to execute")''',
     '''    if False:
        raise ContractRefusal("refused", "precondition", "unreachable")''',
     SUITE),
    ("an uncertain attempt has nothing to remove", INTAKE,
     '''    if attempt["execution_runtime"] == "uncertain":
        raise ContractRefusal(
            "runtime-observation", "quiescence-unknown",
            f"attempt {name_value(attempt_id)} execution runtime is uncertain; "
            f"the failed start attached no identity this manager can name, so "
            f"there is nothing to remove and nothing to prove absent")''',
     '''    if False:
        raise ContractRefusal("runtime-observation", "quiescence-unknown", "x")''',
     SUITE),
    ("the ending is retained rather than complete", INTAKE,
     '''    observe(store, attempt_id=attempt_id, axis="cleanup", value="retained")''',
     '''    observe(store, attempt_id=attempt_id, axis="cleanup", value="complete")''',
     SUITE),
    ("only positive absence is an ending", INTAKE,
     '''    state = observed["state"]
    if state != "absent":
        observe(store, attempt_id=attempt_id, axis="cleanup", value="failed")
        return documents.cleanup_settled(
            attempt_id=attempt_id, cleanup="failed", state=state,
            why=observed["why"], kept=[], operation=dict(operation))
    if attempt["execution_runtime"] != "destroyed":
        observe(store, attempt_id=attempt_id, axis="execution_runtime",
                value="destroyed")
    observe(store, attempt_id=attempt_id, axis="cleanup", value="retained")''',
     '''    state = observed["state"]
    observe(store, attempt_id=attempt_id, axis="cleanup", value="retained")''',
     SUITE),
    # Review [P0]: the record must be BOUND to the runtime being destroyed.
    ("the record's kind is verified", INTAKE,
     '    if held.get("kind") != "runtime.start-failed":',
     '    if False:', SUITE),
    ("the record's facts are this attempt's own", INTAKE,
     '        if record[member] != mine:',
     '        if False:', SUITE),
    ("the failed-start journal identity is stable for one start act",
     ATTEMPTS,
     '''    return "runtime.start-failed:" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _fixed_assignment(attempt),
        "start_operation_id": _start_operation_id(attempt),
    })[len("sha256:"):]''',
     '''    return "runtime.start-failed:" + digest({
        "attempt_id": attempt["runtime_attempt_id"],
        "assignment": _fixed_assignment(attempt),
        "start_operation_id": _start_operation_id(attempt),
        "runtime_id": attempt["runtime_id"],
        "execution_runtime": attempt["execution_runtime"],
    })[len("sha256:"):]''', SUITE),
]


def run(module):
    return subprocess.run([sys.executable, "-m", "unittest", module],
                          capture_output=True, text=True,
                          env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"})


def main():
    held = {path: path.read_bytes() for path in {INTAKE, ATTEMPTS}}
    report = []
    try:
        for name, path, original, replacement, module in MUTATIONS:
            text = path.read_text()
            if original not in text:
                report.append((name, "STALE", "the anchor is not in the tree"))
                continue
            path.write_text(text.replace(original, replacement, 1))
            try:
                answer = run(module)
            finally:
                path.write_bytes(held[path])
            failing = [line for line in answer.stderr.splitlines()
                       if line.startswith(("FAIL:", "ERROR:"))]
            report.append((name,
                           "CAUGHT" if answer.returncode else "MEASURED ZERO",
                           failing[0] if failing
                           else (answer.stderr.strip().splitlines()[-1:]
                                 or ["no failure"])[0]))
    finally:
        for path, bytes_ in held.items():
            path.write_bytes(bytes_)

    print("W32648 MUTATION HARNESS")
    print("=" * 70)
    worst = 0
    for name, verdict, detail in report:
        print(f"[{verdict:<13}] {name}")
        print(f"                {detail}")
        if verdict in ("MEASURED ZERO", "STALE"):
            worst = 1
    print("=" * 70)
    print("A guard nothing fails without is not a guard." if worst
          else "Every guard is load-bearing.")
    return worst


if __name__ == "__main__":
    sys.exit(main())
