"""W325034 — the supported human approval boundary, on a CLEAN native Job.

The research in `review-2026-10-18T18-00-19Z.md` narrowed this: `verify` and
`review` are session transitions independent of `approve`, and
`integration.driver.ordinary_test_evidence` plus
`worker_manager.review_cycles.integration_checkpoint` are public read-only
readers that cross-bind the producer's frozen result, the assignment, the
candidate and the accepted checkpoint. So the question is not whether a human
approval path exists but whether it can be driven from a CLEAN pre-receipt
state on a real native reviewed candidate. This file drives exactly that.

WHAT IT DELIBERATELY DOES NOT TOUCH: `_accepted_receipts` (private, and it
bundles the approval), `admit_accepted`/`continue_accepted` (automatic
integration admission, which is not the selected human-integration path), and
any forged receipt, invented worker observation or product edit.

WHAT IS REAL: the composed native Job, its real implementation and review
turns, the published proposal, the accepted checkpoint, and the two public
evidence readers. Every receipt below is written by the product's own session
transitions.

WHAT IS SIMULATED, AND LABELLED EVERYWHERE IT APPEARS: the engine (no daemon)
and the provider (injected at the adapter's process seam) in the Job's own
turns; the independent verifier's and reviewer's JUDGEMENTS, which a human or a
reviewing agent would make and which this driver makes on the basis of the
exact public observations it prints; and the owner's approval, human
integration record and closure, which stand in for Slawomir's decision and are
marked as rehearsal in the record's own bytes.

Run from `v12/python`:

    PYTHONPATH=src:. python3 <this file> --evidence <directory>
"""
import argparse
import hashlib
import io
import json
import pathlib
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout

VERIFIER = "baton.verifier-325034"
REVIEWER = "baton.reviewer-325034"
OWNER = "baton.slaw"
SIMULATED = "SIMULATED (W325034 rehearsal; no human act, no live provider)"


def say(place, name, answer):
    (place / name).write_text(
        json.dumps(answer, indent=2, sort_keys=True, default=str) + "\n")


def command(verb, *operands):
    from tools import stack_command

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = stack_command.main([verb, *operands])
    return {"exit": code, "stderr": err.getvalue().strip(),
            "answer": json.loads(out.getvalue()) if out.getvalue().strip()
            else None}


def receipts_of(authority, proposal_id):
    return {kind: authority.receipt(proposal_id, kind)
            for kind in ("verification", "review", "approval",
                         "integration")}


def dispositions(receipts):
    return {kind: (one or {}).get("disposition")
            for kind, one in receipts.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    taken = parser.parse_args()
    place = pathlib.Path(taken.evidence).resolve()
    place.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    steps = []

    from tests.tools.test_stage_execution import (
        TheComposedJobTraversesReviewAndAcceptance as Composed)
    from baton_v12.authority import Authority, Refusal
    from baton_v12.integration.driver import ordinary_test_evidence
    from baton_v12.worker_manager.review_cycles import integration_checkpoint

    case = Composed()
    case.setUp()
    try:
        uuid = case.config["authority_uuid"]
        store = case.authority_path
        work_id = case.submission["jobs"][0]["stages"][0]["work_id"]
        base = ["--authority-store", store, "--authority-uuid", uuid]

        # -- 1. a clean native reviewed Job, with NO receipts ---------------
        held = case.reviewed()
        case.drive(held.job, held.composed, "review", "completed", ticks=14)
        line = [dict(one) for one in held.control._connection.execute(
            "SELECT line_id, work_id, declared_base FROM review_lines")]
        line_id = line[0]["line_id"]
        reader = Authority.open_readonly(store, expected_authority_uuid=uuid)
        try:
            proposals = reader.proposals_of(work_id)
            proposal = proposals[-1]
            proposal_id = proposal["proposal_id"]
            clean = receipts_of(reader, proposal_id)
            accepted = integration_checkpoint(held.control, line_id)
            evidence = ordinary_test_evidence(held.control, reader,
                                              line_id=line_id,
                                              proposal_id=proposal_id)
        finally:
            reader.dispose()
        steps.append({
            "step": "1. clean native reviewed candidate, receipts absent",
            "work_id": work_id, "job_id": case.submission["jobs"][0]["job_id"],
            "implementation_attempt": held.attempt_id,
            "review_attempt": held.review,
            "line": line, "proposal_id": proposal_id,
            "candidate_digest": proposal["candidate_digest"],
            "input_digest": proposal["input_digest"],
            "policy_digest": proposal["policy_digest"],
            "assignment_ref": proposal["assignment_ref"],
            "stage_states": case.states(held.job, held.composed),
            "receipts": clean, "dispositions": dispositions(clean),
            "accepted_checkpoint": accepted,
            "ordinary_test_evidence": evidence,
            "simulated": ["engine (no daemon)", "provider (injected)"],
            "not_called": ["_accepted_receipts", "admit_accepted",
                           "continue_accepted"]})
        say(place, "step-1-clean-native-candidate.json", steps[-1])

        # -- 2. the deployment grants, before any dependent act -------------
        authority = Authority.open(store, expected_authority_uuid=uuid)
        try:
            scope = authority.project_work(work_id)["scope"]
            for participant, capability in ((VERIFIER, "verify"),
                                            (REVIEWER, "review"),
                                            (OWNER, "approve"),
                                            (OWNER, "integrate"),
                                            (OWNER, "close")):
                authority.grant_capability(participant, capability,
                                           scope=scope)
            generation = authority.policy_generation()
            grants = {who: authority.capabilities_of(who)
                      for who in (VERIFIER, REVIEWER, OWNER)}
        finally:
            authority.dispose()
        steps.append({"step": "2. deployment grants, then the pinned "
                              "generation",
                      "scope": scope, "grants": grants,
                      "policy_generation": generation,
                      "note": "an independently selected verifier and "
                              "reviewer, distinct from the owner; the owner "
                              "holds no verify or review grant"})
        say(place, "step-2-deployment-grants.json", steps[-1])

        # -- 3. the independent judgments, on THAT public evidence ----------
        witness = hashlib.sha256(
            json.dumps(evidence["observation"], sort_keys=True,
                       default=str).encode("utf-8")).hexdigest()
        judged = {"evidence_observation_digest": "sha256:" + witness,
                  "producer_attempt_id": evidence.get("attempt_id"),
                  "result_digest": evidence.get("result_digest"),
                  "accepted_verdict_id": (accepted or {}).get("verdict_id"),
                  "judgement": SIMULATED}
        authority = Authority.open(store, expected_authority_uuid=uuid)
        try:
            judged["verification"] = authority.session(VERIFIER).verify(
                {"proposal_id": proposal_id,
                 "verification_id": "w325034-verification",
                 "observation": "passed",
                 "operation_id": "w325034-verify"})
            judged["review"] = authority.session(REVIEWER).review(
                {"proposal_id": proposal_id,
                 "review_id": "w325034-review",
                 "disposition": "accepted",
                 "operation_id": "w325034-review"})
            judged["receipts_now"] = dispositions(
                receipts_of(authority, proposal_id))
        finally:
            authority.dispose()
        steps.append(dict({"step": "3. independent verifier and reviewer "
                                   "judgments, approval untouched"}, **judged))
        say(place, "step-3-independent-judgments.json", steps[-1])

        # -- 4. the owner's pending action: approval DUE, approval ABSENT ---
        pending = command("disposition", "pending", *base, "--work", work_id,
                          "--participant", OWNER)
        due = pending["answer"] or {}
        steps.append({"step": "4. owner pending action",
                      "owner_action": due.get("owner_action"),
                      "due": due.get("due"), "holds": due.get("holds"),
                      "approval_receipt": [
                          one["receipts"]["approval"]
                          for one in (due.get("proposals") or [])
                          if one["proposal_id"] == proposal_id],
                      "exit": pending["exit"]})
        say(place, "step-4-owner-pending.json", steps[-1])

        # -- 4b. the canonical record, which the citation needs -------------
        # W321688's binding is a prerequisite of citing anything as this
        # Work's evidence: `record_dossier_evidence` refuses a Work with no
        # dossier, which the first run of this driver discovered by being
        # refused. Allocating the record is a deployment act, not an owner
        # decision, so it is here rather than inside the owner's steps.
        locator = "pilot-human-boundary-" + uuid[:8]
        bound = command("record", "bind", *base, "--work", work_id,
                        "--locator", locator,
                        "--operation-id", "w325034-bind")
        steps.append({"step": "4b. the canonical dossier binding",
                      "locator": locator, "exit": bound["exit"],
                      "answer": bound["answer"], "stderr": bound["stderr"]})
        say(place, "step-4b-dossier-binding.json", steps[-1])

        # -- 5. the withheld-approval negatives -----------------------------
        root = place / "integration-root"
        root.mkdir(parents=True, exist_ok=True)
        reference = "INTEGRATION.json"
        document = {"schema": "baton.v12.human-integration-record/1",
                    "authority_uuid": uuid, "work_id": work_id,
                    "proposal_id": proposal_id,
                    "candidate_digest": proposal["candidate_digest"],
                    "commit": "0" * 40, "integrated_by": SIMULATED,
                    "integrated_at": "2026-10-18T18:10:00Z",
                    "notes": "W325034 rehearsal fixture. No human integrated "
                             "anything and no commit exists; the commit is "
                             "forty zeroes so it cannot be mistaken for one."}
        (root / reference).write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n")
        withheld = {
            "human_integration_with_approval_withheld": command(
                "disposition", "integrated", *base, "--participant", OWNER,
                "--work", work_id, "--proposal", proposal_id,
                "--expect-candidate-digest", proposal["candidate_digest"],
                "--root", str(root), "--reference", reference,
                "--commit", "0" * 40,
                "--integration-id", "w325034-integration-early",
                "--operation-id", "w325034-integrated-early",
                "--evidence-operation-id", "w325034-citation-early"),
            "satisfying_closure_with_approval_withheld": command(
                "disposition", "close", *base, "--participant", OWNER,
                "--work", work_id, "--outcome", "satisfying",
                "--rationale", "too early", "--proposal", proposal_id,
                "--expect-candidate-digest", proposal["candidate_digest"],
                "--root", str(root),
                "--operation-id", "w325034-close-early")}
        authority = Authority.open(store, expected_authority_uuid=uuid)
        try:
            try:
                authority.session(OWNER).integrate(
                    {"proposal_id": proposal_id,
                     "integration_id": "w325034-raw-integrate",
                     "operation_id": "w325034-raw"})
                withheld["authority_integrate"] = "ACCEPTED"
            except Refusal as refusal:
                withheld["authority_integrate"] = f"refused: {refusal}"
            withheld["receipts_unchanged"] = dispositions(
                receipts_of(authority, proposal_id))
        finally:
            authority.dispose()
        steps.append(dict({"step": "5. approval withheld: the negatives"},
                          **withheld))
        say(place, "step-5-withheld-approval.json", steps[-1])

        # -- 6. the owner's own decision, and the stale/duplicate checks ----
        owner_steps = {}
        for what, changed in (
                ("wrong review receipt", {"--expect-review": "not-the-one"}),
                ("stale candidate digest",
                 {"--expect-candidate-digest": "sha256:" + "f" * 64}),
                ("wrong principal", {"--participant": REVIEWER})):
            operands = {"--participant": OWNER, "--work": work_id,
                        "--proposal": proposal_id,
                        "--expect-candidate-digest":
                            proposal["candidate_digest"],
                        "--expect-review": "w325034-review",
                        "--policy-generation": str(generation),
                        "--approval-id": "w325034-approval",
                        "--operation-id": "w325034-approve"}
            operands.update(changed)
            flat = []
            for name, value in operands.items():
                flat += [name, value]
            owner_steps[f"refused: {what}"] = command(
                "disposition", "approve", *base, *flat)
        owner_steps["approve"] = command(
            "disposition", "approve", *base, "--participant", OWNER,
            "--work", work_id, "--proposal", proposal_id,
            "--expect-candidate-digest", proposal["candidate_digest"],
            "--expect-review", "w325034-review",
            "--policy-generation", str(generation),
            "--approval-id", "w325034-approval",
            "--operation-id", "w325034-approve")
        owner_steps["approve_replay"] = command(
            "disposition", "approve", *base, "--participant", OWNER,
            "--work", work_id, "--proposal", proposal_id,
            "--expect-candidate-digest", proposal["candidate_digest"],
            "--expect-review", "w325034-review",
            "--policy-generation", str(generation),
            "--approval-id", "w325034-approval",
            "--operation-id", "w325034-approve")
        owner_steps["integrated"] = command(
            "disposition", "integrated", *base, "--participant", OWNER,
            "--work", work_id, "--proposal", proposal_id,
            "--expect-candidate-digest", proposal["candidate_digest"],
            "--root", str(root), "--reference", reference,
            "--commit", "0" * 40,
            "--integration-id", "w325034-integration",
            "--operation-id", "w325034-integrated",
            "--evidence-operation-id", "w325034-citation")
        steps.append(dict({"step": "6. the owner's own decision",
                           "labelled": SIMULATED}, **owner_steps))
        say(place, "step-6-owner-decision.json", steps[-1])

        # -- 7. closure and readback ----------------------------------------
        closing = {
            "close": command(
                "disposition", "close", *base, "--participant", OWNER,
                "--work", work_id, "--outcome", "satisfying",
                "--rationale", "W325034 rehearsal closure (simulated owner)",
                "--proposal", proposal_id,
                "--expect-candidate-digest", proposal["candidate_digest"],
                "--root", str(root), "--operation-id", "w325034-close"),
            "readback": command(
                "disposition", "pending", *base, "--work", work_id,
                "--participant", OWNER, "--root", str(root))}
        reader = Authority.open_readonly(store, expected_authority_uuid=uuid)
        try:
            closing["final_receipts"] = {
                kind: {"actor": (one or {}).get("actor"),
                       "disposition": (one or {}).get("disposition"),
                       "receipt_id": (one or {}).get("receipt_id")}
                for kind, one in receipts_of(reader, proposal_id).items()}
            closing["work"] = {
                k: v for k, v in reader.project_work(work_id).items()
                if k in ("status", "phase", "outcome", "close_decision")}
        finally:
            reader.dispose()
        steps.append(dict({"step": "7. closure and readback"}, **closing))
        say(place, "step-7-closure-readback.json", steps[-1])

        answer = {"schema": "baton.w325034.human-boundary/1",
                  "boundary": "clean native reviewed candidate; public "
                              "read-only evidence readers; independent "
                              "session judgments; the installed disposition "
                              "command for every owner act. Engine and "
                              "provider simulated; verifier, reviewer and "
                              "owner judgments SIMULATED and labelled. No "
                              "_accepted_receipts, admit_accepted, forged "
                              "receipt, product edit, live model, live "
                              "credential, deployment or Git mutation.",
                  "steps": steps,
                  "seconds": round(time.monotonic() - started, 3)}
        say(place, "HUMAN-BOUNDARY.json", answer)
        print(json.dumps({"steps": [one["step"] for one in steps],
                          "seconds": answer["seconds"]}, indent=2))
        return 0
    except Exception:                                        # noqa: BLE001
        failure = {"failed": traceback.format_exc()[-3000:], "steps": steps}
        say(place, "HUMAN-BOUNDARY-FAILURE.json", failure)
        print(failure["failed"][-1500:])
        return 1
    finally:
        case.doCleanups()


if __name__ == "__main__":
    raise SystemExit(main())
