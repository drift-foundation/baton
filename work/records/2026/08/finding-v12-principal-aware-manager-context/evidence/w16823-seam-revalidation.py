"""W16823 PLAN 1 — what the manager can actually reach, measured.

The brief is explicit that this correction CONSUMES W16821's reviewed authority
projection and must not guess it in parallel.  W16821 is now closed satisfying,
so this asks the delivered surface what it answers, through the only object the
manager ever holds: a participant-bound `Session` behind `AuthorityPort`.

It writes nothing and changes nothing.  Run from `v12/python` with
`PYTHONPATH=src python3 <this file>`.
"""

import json
import os
import tempfile

from baton_v12.authority import Authority, V11, V12
from baton_v12.worker_manager.authority_port import (CLAIM_ANSWER,
                                                     PROJECTION_READ,
                                                     PROJECTION_UNREAD)

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
V11_WORK = "0123abcd-W8"
NOW = "2026-08-28T22:00:00.000Z"
A = "org_a.worker"
B = "org_b.worker"
ONE = "principal:one"


def deployment(root):
    face = Authority.create(os.path.join(root, "authority.sqlite3"),
                            authority_uuid=UUID, clock=lambda: NOW)
    core = face._core
    core.create_work(WORK, "impl", contract=V12, scope="scope:platform")
    core.create_work(V11_WORK, "impl", contract=V11, scope="scope:platform")
    core.add_route_handler("impl", A)
    core.add_route_handler("impl", B)
    # ONE PRINCIPAL, TWO ENDPOINT ADDRESSES -- the acceptance's own setup.
    face.bind_endpoint(A, ONE)
    face.bind_endpoint(B, ONE)
    return face


print("W16823 — THE AUTHORITY SEAM, AS THE MANAGER SEES IT")
print("=" * 74)
print()

with tempfile.TemporaryDirectory(prefix="w16823-seam-") as root:
    face = deployment(root)
    session = face.session(A)

    print("=== 1. WHAT `claim` ANSWERS, which is what the port owns")
    answer = session.claim({"work_id": WORK, "operation_id": "op-1"})
    print(f"    members : {sorted(answer)}")
    print(f"    the port requires exactly: {sorted(CLAIM_ANSWER)}")
    print(f"    answer  : {json.dumps(answer)}")
    print()
    print("    NO AUTHORIZATION CONTEXT. The four-part fence and nothing else.")
    print()

    print("=== 2. WHERE THE DECISION ACTUALLY IS")
    claimed = [one for one in session.assignment_events(WORK)
               if one["cause"] == "claimed"]
    print(f"    assignment_events -> {len(claimed)} claim event(s)")
    for one in claimed:
        print(f"      seq {one['seq']}  {json.dumps(one['decision'])}")
    print()
    print("    Complete and exact -- and reachable only by picking a claim")
    print("    event out of a list. The event's own `seq` is the exact")
    print("    identity W16821's re-review established, and the claim answer")
    print("    carries no way to name it.")
    print()

    print("=== 3. THE AMBIGUITY THAT MAKES 'PICK THE NEWEST' UNSOUND")
    print("    A v11 assignment mints no generation, so two claims through one")
    print("    endpoint are two acts with identical four-part identities.")
    # The v12 claim above holds this principal's ONE slot -- which is the
    # correction working -- so it is released before the v11 Work is claimed.
    session.end({"expect": session.assignment_of(WORK),
                 "operation_id": "op-release"})
    session.claim({"work_id": V11_WORK, "operation_id": "op-2"})
    first = session.assignment_of(V11_WORK)
    session.end({"expect": first, "operation_id": "op-3"})
    second_answer = session.claim({"work_id": V11_WORK,
                                   "operation_id": "op-4"})
    v11_claims = [one for one in session.assignment_events(V11_WORK)
                  if one["cause"] == "claimed"]
    print(f"    first claim answer  : {json.dumps(first)}")
    print(f"    second claim answer : {json.dumps(second_answer)}")
    print(f"    identical           : {first == second_answer}")
    print(f"    claim events        : "
          f"{[one['seq'] for one in v11_claims]}")
    print("    Both events match the same answer, so a manager matching on the")
    print("    answer cannot say WHICH claim it just made. That is exactly the")
    print("    join W16821's own re-review refused as 'not an exact identity'.")
    print()

    print("=== 4. WHAT IS ALREADY PRINCIPAL-GLOBAL WITHOUT ANY CHANGE")
    print(f"    slot_holder({A!r}) -> {session.slot_holder(A)!r}")
    print(f"    slot_holder({B!r}) -> {session.slot_holder(B)!r}")
    print("    Capacity is ALREADY observable principal-globally: asking")
    print("    through the OTHER endpoint answers about the same held Work,")
    print("    because W16821 keyed the slot by principal. The manager needs")
    print("    no new member for that half of the correction.")
    print()

    print("=== 5. WHAT THE PROJECTION CARRIES")
    projection = session.project_work(WORK)
    print(f"    project_work members: {sorted(projection)}")
    print(f"    scope               : {projection['scope']!r}")
    print(f"    close_decision      : {projection['close_decision']!r}")
    print(f"    the port reads      : {sorted(PROJECTION_READ)}")
    print(f"    the port names unread: {sorted(PROJECTION_UNREAD)}")
    print()

    print("=== 6. WHAT THE SESSION DOES NOT EXPOSE")
    surface = {name for name in dir(session) if not name.startswith("_")}
    for name in ("principal_of", "grants_of", "decision_of", "endpoints_of",
                 "policy_generation", "slot_holder_of_principal"):
        print(f"    {name:26} {'present' if name in surface else 'ABSENT'}")
    print()
    print("    All six are CONFIGURATION on the bootstrap face, which the")
    print("    manager never holds -- correctly, and not the gap: the manager")
    print("    should not be able to ask about other principals. What it needs")
    print("    is the decision for the claim IT just made.")
    face.dispose()
