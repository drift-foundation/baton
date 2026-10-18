"""W321690 — the receipt/admission boundary, and the human-approval question.

Review 2026-10-18T17-50-33Z corrected claim 324890: the driver stopped at
integration `claimed`, before ADMISSION, and null receipts at that point prove
nothing about whether receipts are produced.
`integration/driver.py:_accepted_receipts` (1105-1178) writes verification,
review AND approval, and `admit_accepted` calls it before any runtime. So the
real open question is the one the review names: human approval versus this
configured automatic approver.

THIS FILE ANSWERS THAT QUESTION BY DRIVING IT, not by reading the source. It
borrows the accepted integration-worker world -- real coordinator, real
admission driver, real Authority, the engine answering without a daemon and
the provider a real child process over reviewed bytes -- drives the supported
admission, and then asks the owner's own installed command what is due.

WHAT IS SIMULATED AND LABELLED: the engine (`run`/`inspect`/`ps` without a
daemon) and the provider. Everything between them is the accepted composition.
No live model, no live credential, no deployment, no Git mutation. No receipt
is manufactured here and no owner precondition is weakened: every receipt
below is written by the product's own operations.

Run from `v12/python`:

    PYTHONPATH=src:. python3 <this file> --evidence <directory>
"""
import argparse
import io
import json
import pathlib
import time
from contextlib import redirect_stderr, redirect_stdout


def say(answer, place, name):
    place.mkdir(parents=True, exist_ok=True)
    (place / name).write_text(
        json.dumps(answer, indent=2, sort_keys=True, default=str) + "\n")


def disposition(*operands):
    from tools import stack_command

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = stack_command.main(["disposition", *operands])
    return {"exit": code, "stderr": err.getvalue(),
            "answer": json.loads(out.getvalue()) if out.getvalue().strip()
            else None}


def receipts_of(authority, proposal_id):
    return {kind: authority.receipt(proposal_id, kind)
            for kind in ("verification", "review", "approval",
                         "integration")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    taken = parser.parse_args()
    place = pathlib.Path(taken.evidence).resolve()
    started = time.monotonic()

    from tests.tools.test_integration_worker import (
        TheWholeIntegrationRunsThroughThisPort as World)

    case = World()
    case.setUp()
    try:
        world = case.world
        authority = world.authority
        proposal_id = world.proposal_id
        work_id = authority.proposal(proposal_id)["assignment_ref"][
            "work_ref"]["work_id"]
        uuid = authority.authority_uuid
        # The world creates its Authority at a real file under its command
        # OWNER's root, which is what lets the installed command open the SAME
        # store the admission wrote to rather than a second one.
        store = str(pathlib.Path(world.owner.root)
                    / "ordinary-authority.sqlite3")

        before = receipts_of(authority, proposal_id)

        # THE SUPPORTED ADMISSION, through the accepted driver and the
        # simulated port. `started()` is the deployment's own two calls in
        # order: prepare, then admit.
        held, admitted = case.started()
        after = receipts_of(authority, proposal_id)

        step = {
            "step": "the receipt/admission boundary",
            "work_id": work_id, "proposal_id": proposal_id,
            "authority_uuid": uuid,
            "receipts_before_admission": before,
            "receipts_after_admission": after,
            "actors_after": {kind: (one or {}).get("actor")
                             for kind, one in after.items()},
            "dispositions_after": {kind: (one or {}).get("disposition")
                                   for kind, one in after.items()},
            "admitted": admitted,
            "simulated": ["engine (run/inspect/ps, no daemon)",
                          "provider (real child process over reviewed bytes)"],
        }
        say(step, place, "step-6-receipt-boundary.json")

        # NOW ASK THE OWNER'S OWN COMMAND. The authority handle above is the
        # world's; the command opens the same store for itself.
        owner = "baton.slaw"
        scope = authority.project_work(work_id)["scope"]
        for capability in ("approve", "integrate", "close"):
            authority.grant_capability(owner, capability, scope=scope)
        generation = authority.policy_generation()

        base = ["--authority-store", store, "--authority-uuid", uuid]
        asked = {"pending": disposition("pending", *base, "--work", work_id,
                                        "--participant", owner)}
        due = asked["pending"]["answer"] or {}
        candidate = None
        review_receipt = (after.get("review") or {}).get("receipt_id")
        for one in (due.get("proposals") or []):
            if one["proposal_id"] == proposal_id:
                candidate = one["candidate_digest"]
        asked["owner_action"] = due.get("owner_action")
        asked["holds"] = due.get("holds")

        # THE OWNER'S OWN APPROVAL, attempted on the candidate the native path
        # already approved for it. Whatever happens here is the answer to the
        # review's question; nothing is manufactured either way.
        if candidate and review_receipt:
            asked["owner_approve"] = disposition(
                "approve", *base, "--participant", owner, "--work", work_id,
                "--proposal", proposal_id,
                "--expect-candidate-digest", candidate,
                "--expect-review", review_receipt,
                "--policy-generation", str(generation),
                "--approval-id", "w321690-owner-approval",
                "--operation-id", "w321690-owner-approve")
        else:
            asked["owner_approve"] = {
                "not_attempted": "pending reported no candidate/review to "
                                 "decide on", "candidate": candidate,
                "review_receipt": review_receipt}

        answer = {
            "schema": "baton.w321690.receipt-boundary/1",
            "boundary": "accepted integration-worker world: real coordinator, "
                        "admission driver, Authority and worker entry; engine "
                        "and provider simulated and labelled; no live model, "
                        "live credential, deployment or Git mutation",
            "step": step, "owner": asked,
            "seconds": round(time.monotonic() - started, 3)}
        say(answer, place, "RECEIPT-BOUNDARY.json")
        print(json.dumps(answer, indent=2, sort_keys=True, default=str))
        return 0
    finally:
        case.doCleanups()


if __name__ == "__main__":
    raise SystemExit(main())
