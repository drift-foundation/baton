"""W321690 — ONE joined native Job lifecycle, driven to the owner's closure.

Review 2026-10-18T17-42-19Z requires one shared deterministic fixture that
carries continuity from an admitted native attempt, through its terminal
candidate, to an eligible independent review, and on to the owner's
disposition and closure on the SAME authority -- because splitting those
assertions is the isolated-proof gap this Work owns.

WHAT IS REAL HERE. The serving object is `tools.stage_execution`'s own
`operations_from` composition. The Authority, Job, Control and Integration
stores are real local ones. The development line is a real version-controlled
checkout materialized by the accepted checkpoint profile. The worker is the
actual `claude_agent` workload entered through `baton_worker.serve_exchange`
over the namespaces the deployment mounted. The ending is `review_driver`'s,
so the seal, the intake receipt, the retention decision, the publication, the
checkpoint freeze and the cleanup are the accepted public operations. The
owner's acts are the installed `disposition` command's.

THE TWO SIMULATED SEAMS, LABELLED. The ENGINE is a callable with no daemon,
and the PROVIDER inside the workload is injected. Both are the accepted
`ComposedOneJobCase` seams this file borrows rather than re-invents, and this
Work's FINDING is what permits them: "Simulate providers/engine at their
normal boundary; exercise real coordination APIs."

WHAT IS NOT REACHED, and is not claimed: no daemon, no container, no image,
no network, no live model, no live credential, no deployment, no Git mutation.
Every decision a provider or engine would have made here is simulated and
labelled as such in the evidence this writes.

Run from `v12/python`:

    PYTHONPATH=src:. python3 <this file> --evidence <directory>
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent


def say(answer, place, name):
    place.mkdir(parents=True, exist_ok=True)
    body = json.dumps(answer, indent=2, sort_keys=True, default=str) + "\n"
    (place / name).write_text(body)
    return name


def disposition(*operands):
    """The installed owner command, as an operator would reach it."""
    from tools import stack_command
    import io
    from contextlib import redirect_stderr, redirect_stdout

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = stack_command.main(["disposition", *operands])
    return code, out.getvalue(), err.getvalue()


def record_verb(*operands):
    from tools import stack_command
    import io
    from contextlib import redirect_stderr, redirect_stdout

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = stack_command.main(["record", *operands])
    return code, out.getvalue(), err.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    taken = parser.parse_args()
    place = pathlib.Path(taken.evidence).resolve()
    started = time.monotonic()
    steps = []

    from tests.tools.test_stage_execution import (
        TheComposedJobTraversesReviewAndAcceptance as Composed)
    from baton_v12.authority import Authority

    case = Composed()
    case.setUp()
    try:
        config = case.config
        uuid = config["authority_uuid"]
        store = case.authority_path
        # The Work every stage of this Job is bound to, read from the
        # submission the fixture actually submitted rather than from a
        # deployment member this composition does not carry.
        work_id = case.submission["jobs"][0]["stages"][0]["work_id"]
        owner = config["participant"]

        # -- 1. the admitted native attempt and its terminal candidate -------
        held = case.reviewed()
        attempt = held.attempt_id
        review_attempt = held.review
        states = case.states(held.job, held.composed)
        projected = case.projected()

        authority = Authority.open_readonly(store,
                                            expected_authority_uuid=uuid)
        try:
            proposals = authority.proposals_of(work_id)
            receipts = {}
            for one in proposals:
                receipts[one["proposal_id"]] = {
                    kind: authority.receipt(one["proposal_id"], kind)
                    for kind in ("verification", "review", "approval",
                                 "integration")}
            target = authority.canonical_target()
            generation = authority.policy_generation()
        finally:
            authority.dispose()

        steps.append({
            "step": "1. admitted attempt, terminal candidate, review stage",
            "work_id": work_id,
            "implementation_attempt": attempt,
            "review_attempt": review_attempt,
            "stage_states": states,
            "work_route_now": projected["route"],
            "proposals": [{"proposal_id": one["proposal_id"],
                           "candidate_digest": one["candidate_digest"],
                           "result_id": one["result_id"],
                           "input_digest": one["input_digest"],
                           "assignment_ref": one["assignment_ref"]}
                          for one in proposals],
            "receipts": receipts,
            "canonical_target": target,
            "policy_generation": generation,
            "private_output_roots": sorted(held.roots)
            if isinstance(held.roots, dict) else str(held.roots),
            "simulated": ["engine (no daemon)", "provider (injected)"],
        })
        say(steps[-1], place, "step-1-native-lifecycle.json")

        # -- 2. the owner's disposition on THAT SAME authority ---------------
        # The dossier binding first: the owner command resolves evidence
        # through W321688's record surface, so the Work needs its canonical
        # record before anything can be cited against it.
        locator = "operator-quickstart-" + uuid[:8]
        code, out, err = record_verb(
            "bind", "--authority-store", store, "--authority-uuid", uuid,
            "--work", work_id, "--locator", locator,
            "--operation-id", "w321690-bind")
        bound = {"exit": code, "answer": json.loads(out) if out.strip()
                 else None, "stderr": err}

        code, out, err = disposition(
            "pending", "--authority-store", store, "--authority-uuid", uuid,
            "--work", work_id, "--participant", owner)
        pending = {"exit": code,
                   "answer": json.loads(out) if out.strip() else None,
                   "stderr": err}
        steps.append({"step": "2. owner pending action on the same authority",
                      "dossier": bound, "pending": pending})
        say(steps[-1], place, "step-2-owner-pending.json")

        # -- 3. the review ending, and the receipts it writes ----------------
        case.drive(held.job, held.composed, "review", "completed")
        states_after_review = case.states(held.job, held.composed)
        authority = Authority.open_readonly(store,
                                            expected_authority_uuid=uuid)
        try:
            proposals = authority.proposals_of(work_id)
            receipts = {one["proposal_id"]: {
                kind: authority.receipt(one["proposal_id"], kind)
                for kind in ("verification", "review", "approval",
                             "integration")} for one in proposals}
            route_after = authority.project_work(work_id)["route"]
        finally:
            authority.dispose()
        steps.append({"step": "3. the review ending and its receipts",
                      "stage_states": states_after_review,
                      "work_route_now": route_after,
                      "receipts": receipts})
        say(steps[-1], place, "step-3-review-ending.json")

        # -- 3b. the integration stage, which OWNS the publication ----------
        # The proposal's identity says so (`integration-driver.proposal:`), so
        # the owner's disposition cannot be due until this stage has run: the
        # verification and review receipts the owner command requires are
        # written on this side of the line, not by the review ending.
        integration = {}
        try:
            case.drive(held.job, held.composed, "integration", "claimed")
            integration["drove_to"] = "claimed"
        except Exception as failure:                         # noqa: BLE001
            integration["drove_to"] = None
            integration["detail"] = f"{type(failure).__name__}: {failure}"
        authority = Authority.open_readonly(store,
                                            expected_authority_uuid=uuid)
        try:
            integration["stage_states"] = case.states(held.job, held.composed)
            integration["receipts"] = {
                one["proposal_id"]: {
                    kind: authority.receipt(one["proposal_id"], kind)
                    for kind in ("verification", "review", "approval",
                                 "integration")}
                for one in authority.proposals_of(work_id)}
        finally:
            authority.dispose()
        steps.append(dict({"step": "3b. the integration stage and the "
                                   "receipts it publishes"}, **integration))
        say(steps[-1], place, "step-3b-integration-stage.json")

        # -- 4. the owner's grants, as the DEPLOYMENT act they are -----------
        # `bootstrap --owner_participant` makes these at install time; this
        # fixture's deployment document predates that selection, so the same
        # three grants are made here through the trusted bootstrap face and
        # labelled as a deployment act rather than an owner act.
        owner_participant = "baton.slaw"
        authority = Authority.open(store, expected_authority_uuid=uuid)
        try:
            scope = authority.project_work(work_id)["scope"]
            for capability in ("approve", "integrate", "close"):
                authority.grant_capability(owner_participant, capability,
                                           scope=scope)
            granted = authority.capabilities_of(owner_participant)
            generation_now = authority.policy_generation()
        finally:
            authority.dispose()
        steps.append({"step": "4. owner grants (deployment act, labelled)",
                      "owner_participant": owner_participant,
                      "scope": scope, "capabilities": granted,
                      "policy_generation": generation_now,
                      "equivalent_selection": "bootstrap input member "
                                              "owner_participant (W321689)"})
        say(steps[-1], place, "step-4-owner-grants.json")

        # -- 5. pending, approve, human integration, closure, readback -------
        base = ["--authority-store", store, "--authority-uuid", uuid]
        owner_steps = {}
        code, out, err = disposition("pending", *base, "--work", work_id,
                                     "--participant", owner_participant)
        owner_steps["pending"] = {"exit": code, "stderr": err,
                                  "answer": json.loads(out) if out.strip()
                                  else None}
        due = owner_steps["pending"]["answer"] or {}
        proposal_id = due.get("latest_proposal")
        candidate = None
        review_receipt = None
        for one in (due.get("proposals") or []):
            if one["proposal_id"] == proposal_id:
                candidate = one["candidate_digest"]
                review_receipt = ((one["receipts"].get("review") or {})
                                  .get("receipt_id"))
        owner_steps["read_for_decision"] = {
            "proposal": proposal_id, "candidate_digest": candidate,
            "review_receipt": review_receipt,
            "owner_action": due.get("owner_action"),
            "holds": due.get("holds")}

        if due.get("owner_action") == "approval-due":
            code, out, err = disposition(
                "approve", *base, "--participant", owner_participant,
                "--work", work_id, "--proposal", proposal_id,
                "--expect-candidate-digest", candidate,
                "--expect-review", review_receipt,
                "--policy-generation", str(generation_now),
                "--approval-id", "w321690-approval",
                "--operation-id", "w321690-approve")
            owner_steps["approve"] = {"exit": code, "stderr": err,
                                      "answer": json.loads(out)
                                      if out.strip() else None}
            # The human integration record, written where the dossier cites it.
            root = pathlib.Path(place / "integration-root")
            reference = "INTEGRATION.json"
            root.mkdir(parents=True, exist_ok=True)
            document = {
                "schema": "baton.v12.human-integration-record/1",
                "authority_uuid": uuid, "work_id": work_id,
                "proposal_id": proposal_id, "candidate_digest": candidate,
                "commit": "0" * 40,
                "integrated_by": "SIMULATED (rehearsal; no human act, no Git)",
                "integrated_at": "2026-10-18T17:45:00Z",
                "notes": "W321690 rehearsal: this record is a FIXTURE. No "
                         "human integrated anything and no commit exists; "
                         "the commit field is forty zeroes so it cannot be "
                         "mistaken for one."}
            (root / reference).write_text(
                json.dumps(document, indent=2, sort_keys=True) + "\n")
            code, out, err = disposition(
                "integrated", *base, "--participant", owner_participant,
                "--work", work_id, "--proposal", proposal_id,
                "--expect-candidate-digest", candidate,
                "--root", str(root), "--reference", reference,
                "--commit", "0" * 40,
                "--integration-id", "w321690-integration",
                "--operation-id", "w321690-integrated",
                "--evidence-operation-id", "w321690-citation")
            owner_steps["integrated"] = {"exit": code, "stderr": err,
                                         "answer": json.loads(out)
                                         if out.strip() else None}
            code, out, err = disposition(
                "close", *base, "--participant", owner_participant,
                "--work", work_id, "--outcome", "satisfying",
                "--rationale", "W321690 rehearsal closure (simulated)",
                "--proposal", proposal_id,
                "--expect-candidate-digest", candidate,
                "--root", str(root), "--operation-id", "w321690-close")
            owner_steps["close"] = {"exit": code, "stderr": err,
                                    "answer": json.loads(out) if out.strip()
                                    else None}
            code, out, err = disposition("pending", *base, "--work", work_id,
                                         "--participant", owner_participant,
                                         "--root", str(root))
            owner_steps["readback"] = {"exit": code, "stderr": err,
                                       "answer": json.loads(out)
                                       if out.strip() else None}
        steps.append({"step": "5. owner disposition on the same authority",
                      "acts": owner_steps})
        say(steps[-1], place, "step-5-owner-disposition.json")

        answer = {
            "schema": "baton.w321690.joined-rehearsal/1",
            "boundary": "real coordination, Authority/Job/Control/Integration "
                        "stores, accepted checkpoint profile and real "
                        "version-controlled line; engine and provider "
                        "simulated at their own boundary and labelled; no "
                        "daemon, container, image, network, live model, live "
                        "credential, deployment or Git mutation",
            "authority_uuid": uuid,
            "steps": steps,
            "seconds": round(time.monotonic() - started, 3),
        }
        say(answer, place, "JOINED-REHEARSAL.json")
        print(json.dumps(answer, indent=2, sort_keys=True, default=str))
        return 0
    finally:
        case.doCleanups()


if __name__ == "__main__":
    raise SystemExit(main())
