#!/usr/bin/env python3
"""W32649 — every guard the lane adds, measured BY REMOVAL.

A passing case proves the code does not fail today. It does not prove the guard
beside it is doing anything, and this campaign has already found guards that
measured zero against their own suites. Each mutation below removes or weakens
exactly ONE rule and requires a NAMED case to fail.

Run from `v12/python`:

    PYTHONPATH=src python3 <this file>

Nothing is left modified: every source is restored from the bytes read at the
start, in a `finally`, whatever happens.
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path("src/baton_v12/worker_manager")
LANES = ROOT / "lanes.py"
ATTEMPTS = ROOT / "attempts.py"
INTAKE = ROOT / "intake.py"

LANE = "tests.manager.test_runtime_lane"

MUTATIONS = [
    ("the predecessor interlock is asked at all", LANES,
     "    if not found:\n        return\n    holder = found[0]",
     "    if True:\n        return\n    holder = found[0]", LANE),
    ("the interlock is asked of the WORK, not of the lane", LANES,
     '"WHERE authority_uuid = ? AND work_id = ? AND holder <> ?",\n'
     '        (reference["authority_uuid"], reference["work_id"],\n'
     '         attempt_id)).fetchall()',
     '"WHERE lane_id = ? AND holder <> ?",\n'
     '        (_lane_id(reference), attempt_id)).fetchall()', LANE),
    ("the release is bound to the holder", LANES,
     '"DELETE FROM runtime_lanes WHERE lane_id = ? AND holder = ?",\n'
     '        (_lane_id(reference), attempt_id)).rowcount',
     '"DELETE FROM runtime_lanes WHERE lane_id = ?",\n'
     '        (_lane_id(reference),)).rowcount', LANE),
    ("the principal is part of the identity", LANES,
     'LANE_PARTS = ("authority_uuid", "work_id", "principal", '
     '"effective_scope")',
     'LANE_PARTS = ("authority_uuid", "work_id", "assignment_participant",\n'
     '              "effective_scope")', LANE),
    ("the lane is taken when a start is requested", ATTEMPTS,
     '        lanes._occupy_lane(connection, store._now(), '
     'attempt_id=attempt_id,',
     '        _unused = (connection, store._now(), attempt_id) and None\n'
     '        _skipped = lambda *a, **k: None\n'
     '        _skipped(connection, store._now(), attempt_id=attempt_id,',
     LANE),
    ("the early check refuses before anything durable", ATTEMPTS,
     "    lanes._no_predecessor_holds(store._connection, reference, "
     "attempt_id)",
     "    reference = reference", LANE),
    ("the lane is released when cleanup ends", INTAKE,
     "    lanes._release_lane(connection, attempt_id=attempt_id,",
     "    _skipped = lambda *a, **k: None\n"
     "    _skipped(connection, attempt_id=attempt_id,", LANE),
    # Review [P1]: the derived/stored relation, owned where the row is adopted
    # and therefore on BOTH read paths at once.
    ("the stored name must derive from the stored parts", LANES,
     '    if taken["lane_id"] != derived:',
     '    if False:', LANE),
    ("a whole consistent row is still read", LANES,
     '    if taken["lane_id"] != derived:',
     '    if True:', LANE),
    ("a failed cleanup does NOT release", INTAKE,
     '        observe(store, attempt_id=attempt_id, axis="cleanup", '
     'value="failed")\n        return documents.cleanup_settled(',
     '        observe(store, attempt_id=attempt_id, axis="cleanup", '
     'value="failed")\n'
     '        lanes._release_lane(connection, attempt_id=attempt_id,\n'
     '                            reference=lanes.lane_reference(attempt),\n'
     '                            why="failed")\n'
     '        return documents.cleanup_settled(', LANE),
]


def run(module):
    return subprocess.run([sys.executable, "-m", "unittest", module],
                          capture_output=True, text=True,
                          env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"})


def main():
    held = {path: path.read_bytes() for path in {LANES, ATTEMPTS, INTAKE}}
    report = []
    try:
        for name, path, original, replacement, module in MUTATIONS:
            text = path.read_text()
            if original not in text:
                report.append((name, "STALE", "the anchor is not in the tree"))
                continue
            if module is None:
                report.append((name, "SKIPPED",
                               "a deliberate optimistic check; the "
                               "transaction is the decision"))
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

    print("W32649 MUTATION HARNESS")
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
