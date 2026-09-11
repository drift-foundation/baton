"""P's mandatory FIRST gate, against a REAL Authority.

Can the existing scoped publication/session API express a DERIVED integration
proposal -- new result identity, combined candidate, pinned target snapshot --
under the actual integration-role fixed assignment, with no Authority edit?
"""
import json, os, sys, tempfile

sys.path.insert(0, "/home/sl/src/baton/v12/python/src")
from baton_v12.authority import Authority, Refusal

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123456f-W133117"
PRODUCER = "baton.producer"
INTEGRATOR = "baton.integrator"
answers = {}

root = tempfile.mkdtemp(prefix="p-gate-")
place = os.path.join(root, "authority.sqlite3")
authority = Authority.create(place, authority_uuid=UUID)
try:
    authority.set_policy("canonical_target", "a" * 40)
    authority.create_work(WORK, "impl", contract="v12-assignment-1",
                          operation_id="create-work")
    authority.add_route_handler("impl", PRODUCER)
    authority.add_route_handler("integ", INTEGRATOR)

    # -- the producer's ORIGINAL submission, published on its own assignment --
    producer = authority.session(PRODUCER)
    claimed = producer.claim({"work_id": WORK, "operation_id": "claim-1"})
    original = producer.publish({
        "expect": claimed["assignment"], "operation_id": "publish-original",
        "proposal_id": "proposal-original", "result_id": "result-original",
        "result_digest": "sha256:" + "1" * 64,
        "candidate_digest": "b" * 40, "input_digest": "sha256:" + "2" * 64,
        "policy_digest": "sha256:" + "3" * 64})
    answers["original_proposal"] = original

    # -- the Work moves to the integration role, exactly as serving does -----
    producer.pass_work({"expect": claimed["assignment"],
                        "operation_id": "pass-to-integ", "to_route": "integ",
                        "comment": "ready for integration"})
    integrator = authority.session(INTEGRATOR)
    took = integrator.claim({"work_id": WORK, "operation_id": "claim-integ"})
    fixed = took["assignment"]
    answers["integration_assignment"] = fixed

    # -- THE GATE: a DERIVED proposal under that integration assignment ------
    # New result identity owned by the reconciliation record, the combined
    # candidate, and the PINNED target snapshot named explicitly rather than
    # defaulted to whatever the canonical target is now.
    snapshot = "c" * 40
    derived = integrator.publish({
        "expect": fixed, "operation_id": "publish-derived",
        "proposal_id": "proposal-derived", "result_id": "result-combined",
        "result_digest": "sha256:" + "4" * 64,
        "candidate_digest": "d" * 40, "input_digest": "sha256:" + "5" * 64,
        "policy_digest": "sha256:" + "6" * 64, "target": snapshot})
    answers["derived_proposal"] = derived
    answers["derived_names_integration_assignment"] = (
        derived["assignment_ref"] == fixed)
    answers["derived_target_is_the_pinned_snapshot"] = (
        derived["target"] == snapshot)

    # -- readback through the ordinary reader ---------------------------------
    read = authority.proposal("proposal-derived")
    answers["readback_matches"] = (
        read["candidate_digest"] == "d" * 40
        and read["target"] == snapshot
        and read["result_id"] == "result-combined")

    # -- publish retry replays the exact proposal -----------------------------
    again = integrator.publish({
        "expect": fixed, "operation_id": "publish-derived",
        "proposal_id": "proposal-derived", "result_id": "result-combined",
        "result_digest": "sha256:" + "4" * 64,
        "candidate_digest": "d" * 40, "input_digest": "sha256:" + "5" * 64,
        "policy_digest": "sha256:" + "6" * 64, "target": snapshot})
    answers["retry_replays_identically"] = (again == derived)

    # -- the ORIGINAL submission is untouched ---------------------------------
    # THE ORIGINAL SUBMISSION IS UNTOUCHED, compared member by member: the
    # reader's document and the act's own answer are two shapes of one fact,
    # so equality of the whole objects would be a statement about shapes.
    held = authority.proposal("proposal-original")
    answers["original_reader_document"] = held
    answers["original_untouched"] = all(
        held[name] == original[name] for name in
        ("proposal_id", "result_id", "result_digest", "candidate_digest",
         "input_digest", "policy_digest", "target"))
    answers["original_still_names_its_producer"] = (
        held["assignment_ref"] == original["assignment_ref"]
        if "assignment_ref" in held else held.get("participant") == PRODUCER)

    # -- and reusing the PRODUCER's result identity under the integration
    #    assignment refuses, which is why the derived result_id must be new ---
    try:
        integrator.publish({
            "expect": fixed, "operation_id": "publish-borrowed",
            "proposal_id": "proposal-borrowed", "result_id": "result-original",
            "result_digest": "sha256:" + "1" * 64,
            "candidate_digest": "d" * 40, "input_digest": "sha256:" + "5" * 64,
            "policy_digest": "sha256:" + "6" * 64, "target": snapshot})
        answers["borrowed_result_identity"] = "ACCEPTED -- unexpected"
    except Refusal as refusal:
        answers["borrowed_result_identity"] = f"refused: {refusal}"
finally:
    authority.dispose()

print(json.dumps(answers, indent=2, default=str))
gate = (answers.get("derived_names_integration_assignment")
        and answers.get("derived_target_is_the_pinned_snapshot")
        and answers.get("readback_matches")
        and answers.get("retry_replays_identically")
        and answers.get("original_untouched"))
print("\nGATE:", "EXPRESSIBLE" if gate else "NOT EXPRESSIBLE")
sys.exit(0 if gate else 1)
