#!/usr/bin/env python3
"""W16823 — every guard this cut adds, measured BY REMOVAL.

A case that passes proves the code does not fail today.  It does not prove the
guard beside it is doing anything, and this campaign has already turned up two
guards that measured zero against their own suites.  So each mutation below
deletes or weakens exactly ONE rule and requires a NAMED case to fail.

Run from `v12/python`:

    PYTHONPATH=src python3 <this file>

Nothing is left modified: every source is restored from the bytes read at the
start, in a `finally`, whatever happens.
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path("src/baton_v12")
PORT = ROOT / "worker_manager/authority_port.py"
OFFERS = ROOT / "worker_manager/offers.py"
ATTEMPTS = ROOT / "worker_manager/attempts.py"
CORE = ROOT / "authority/core.py"
DOCUMENTS = ROOT / "worker_manager/documents.py"

# (name, file, original, replacement, module that must fail)
MUTATIONS = [
    ("the claim event is an act identity", PORT,
     'if type(event) is bool or type(event) is not int or event < 1:',
     'if False:',
     "tests.manager.test_principal_context"),
    ("the endpoint IS the assignment's participant", PORT,
     'if decision["endpoint"] != assignment["participant"]:',
     'if False:',
     "tests.manager.test_principal_context"),
    ("the scope is the one this offer froze", PORT,
     'if decision["effective_scope"] != scope:',
     'if False:',
     "tests.manager.test_principal_context"),
    ("the role is the route this offer froze", PORT,
     'if decision["role"] != role:',
     'if False:',
     "tests.manager.test_principal_context"),
    ("the grant provenance is a closed vocabulary", PORT,
     'if decision["grant"] not in GRANT_PROVENANCE:',
     'if False:',
     "tests.manager.test_principal_context"),
    ("the policy generation counts from one", PORT,
     'if type(policy) is bool or type(policy) is not int or policy < 1:',
     'if False:',
     "tests.manager.test_principal_context"),
    ("a committed settlement is the whole result", PORT,
     '''            self._claim_result(answer["result"], work_id, authority_uuid,
                               scope, role, "the committed claim")''',
     '''            self._assignment(answer["result"]["assignment"], work_id,
                             authority_uuid, "the committed claim")''',
     "tests.manager.test_principal_context"),
    ("the context rides the offer settlement signature", OFFERS,
     '''{"offer_id": offer_id, "state": state,
                                   "context": context}''',
     '''{"offer_id": offer_id, "state": state}''',
     "tests.manager.test_principal_context"),
    ("the context rides the activation signature", ATTEMPTS,
     '''"context": context})''',
     '''})''',
     "tests.manager.test_principal_context"),
    ("an offer with no context activates nothing", ATTEMPTS,
     '    if any(value is None for value in context.values()):',
     '    if False:',
     "tests.manager.test_principal_context"),
    ("the labels carry the principal", DOCUMENTS,
     '''                        "participant", "generation", "principal",
                        "effective_scope", "profile_digest",''',
     '''                        "participant", "generation", "profile_digest",''',
     "tests.manager.test_principal_context"),
    ("the claim answers the decision it was taken under", CORE,
     '''            return {"assignment": self.assignment_of(work_id),
                    "claim_event": claim_event,
                    "decision": self._decision("claim", str(claim_event))}''',
     '''            return {"assignment": self.assignment_of(work_id),
                    "claim_event": claim_event,
                    "decision": decision.as_document()}''',
     None),  # equivalence, checked separately -- see below
    ("the claim answers the exact claim event", CORE,
     '''                    "claim_event": claim_event,''',
     '''                    "claim_event": 1,''',
     "tests.authority.test_claim_result"),
]


def run(module):
    return subprocess.run(
        [sys.executable, "-m", "unittest", module],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"})


def main():
    held = {path: path.read_bytes()
            for path in {PORT, OFFERS, ATTEMPTS, CORE, DOCUMENTS}}
    report = []
    try:
        for name, path, original, replacement, module in MUTATIONS:
            text = path.read_text()
            if original not in text:
                report.append((name, "STALE", "the anchor is not in the tree"))
                continue
            if module is None:
                report.append((name, "SKIPPED",
                               "a deliberate equivalence, not a guard"))
                continue
            path.write_text(text.replace(original, replacement, 1))
            try:
                answer = run(module)
            finally:
                path.write_bytes(held[path])
            failing = [line for line in answer.stderr.splitlines()
                       if line.startswith(("FAIL:", "ERROR:"))]
            report.append((name, "CAUGHT" if answer.returncode else "MEASURED "
                           "ZERO",
                           failing[0] if failing else answer.stderr.strip()
                           .splitlines()[-1:] or "no failure"))
    finally:
        for path, bytes_ in held.items():
            path.write_bytes(bytes_)

    print("W16823 MUTATION HARNESS")
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
