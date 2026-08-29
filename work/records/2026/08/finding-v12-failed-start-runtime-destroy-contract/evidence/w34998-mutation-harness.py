#!/usr/bin/env python3
"""W34998 — every guard the sibling provider adds, measured BY REMOVAL.

The whole point of a SIBLING command is that the two member sets are closed
against each other. A guard that is not load-bearing would let exactly the
conflation the approver ruling forbids back in, so each mutation below removes
or weakens one rule and requires a NAMED case to fail.

Run from `v12/python`:

    PYTHONPATH=src python3 <this file>

Nothing is left modified: every source is restored from the bytes read at the
start, in a `finally`, whatever happens.
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path("src/baton_v12/worker_manager")
OCI = ROOT / "oci.py"
DOCUMENTS = ROOT / "documents.py"

SUITE = "tests.manager.test_failed_start_destroy"

MUTATIONS = [
    ("the failed-start body is closed to its own five", OCI,
     '            required=documents.FAILED_START_DESTROY_COMMAND,\n'
     '            optional=("operation",))',
     '            required=("assignment_ref", "runtime_attempt_id",\n'
     '                      "runtime_id", "retention_policy_digest"),\n'
     '            optional=("operation", "failed_start_record_digest",\n'
     '                      "intake_receipt_digest"))',
     SUITE),
    ("the receipt-authorized body stays closed to ITS five", OCI,
     '        taken = boundaries.document(command, "a destroy command",\n'
     '                                    required=documents.DESTROY_COMMAND,\n'
     '                                    optional=("operation",))',
     '        taken = boundaries.document(command, "a destroy command",\n'
     '                                    required=("assignment_ref",\n'
     '                                              "runtime_attempt_id",\n'
     '                                              "runtime_id",\n'
     '                                              "retention_policy_digest"),\n'
     '                                    optional=("operation",\n'
     '                                              "intake_receipt_digest",\n'
     '                                              "failed_start_record_digest"))',
     SUITE),
    ("the runtime identity is owned before the engine", OCI,
     '        runtime_id = boundaries.identity(named, f"{what} runtime id")',
     '        runtime_id = named',
     SUITE),
    ("the failure digest never enters the receipt document", DOCUMENTS,
     '''    "destroy.command": (("assignment_ref", "runtime_attempt_id", "runtime_id",
                         "intake_receipt_digest",
                         "retention_policy_digest"), ()),''',
     '''    "destroy.command": (("assignment_ref", "runtime_attempt_id", "runtime_id",
                         "intake_receipt_digest",
                         "retention_policy_digest"),
                        ("failed_start_record_digest",)),''',
     SUITE),
    ("the two methods share ONE removal core", OCI,
     '        return self._removed(taken["runtime_id"], "a failed-start")',
     '        runtime_id = boundaries.identity(taken["runtime_id"],\n'
     '                                         "a failed-start runtime id")\n'
     '        self.run(destroy_vector(self.engine, runtime_id=runtime_id))\n'
     '        observed = self.observe(runtime_id)\n'
     '        return {"runtime_id": runtime_id, "state": observed["state"],\n'
     '                "why": observed["why"],\n'
     '                "credentials": self._torn_down(observed),\n'
     '                "launch": self._launch_ended(\n'
     '                    observed["state"] == "absent", observed["why"])}',
     SUITE),
    ("only positive absence settles the deliveries", OCI,
     '        if observed["state"] != "absent":\n'
     '            return {"lifecycle_state": "unresolved",\n'
     '                    "why": observed["why"]}',
     '        if False:\n'
     '            return {"lifecycle_state": "unresolved",\n'
     '                    "why": observed["why"]}',
     SUITE),
]


def run(module):
    return subprocess.run([sys.executable, "-m", "unittest", module],
                          capture_output=True, text=True,
                          env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"})


def main():
    held = {path: path.read_bytes() for path in {OCI, DOCUMENTS}}
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

    print("W34998 MUTATION HARNESS")
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
