"""Public-surface reproduction for the null-generation history collision.

Run from v12/python:
  PYTHONPATH=src python3 ../../work/records/2026/08/finding-v12-principal-scope-authority-seam/evidence/w16821-v11-reclaim-history-repro.py
"""

import os
import tempfile

from baton_v12.authority import Authority, V11

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
WHO = "baton.claude"

with tempfile.TemporaryDirectory(prefix="w16821-v11-history-") as root:
    path = os.path.join(root, "authority.sqlite3")
    face = Authority.create(path, authority_uuid=UUID,
                            clock=lambda: "2026-08-28T21:20:00.000Z")
    core = face._core
    core.create_work(WORK, "impl", contract=V11)
    core.add_route_handler("impl", WHO)

    first = core.claim(WORK, WHO, operation_id="claim-1")
    core.activity(first, key="first-act")
    before = face.activities(WORK)[0]["decision"]
    core.end(first, operation_id="release-1")

    face.bind_endpoint(WHO, "principal:one-person")
    second = core.claim(WORK, WHO, operation_id="claim-2")
    core.activity(second, key="second-act")
    after = face.activities(WORK)
    claims = [event["decision"] for event in face.assignment_events(WORK)
              if event["cause"] == "claimed"]

    print("assignment-identities-equal", first == second)
    print("claim-principals", [decision["principal"] for decision in claims])
    print("first-before", before["principal"])
    print("activity-principals-after",
          [activity["decision"]["principal"] for activity in after])
    assert before["principal"] == "principal:baton.claude"
    assert [decision["principal"] for decision in claims] == [
        "principal:baton.claude", "principal:one-person"]
    assert after[0]["decision"] == before, after
