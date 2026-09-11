"""R1(b): can a REAL configured owner give a RESULT's evidence, in P's order?

The review is right that a callable answering a dictionary does not prove an
independent judgement, and that "an actual accepted evidence owner/adapter must
be made concrete and proved". This asks the accepted owner API whether that is
possible WITHOUT changing the order CONTRACT-v1 section 3 lists, and records
exactly what it answers, so the amendment returned in FINDING.md rests on a
measurement rather than on an assertion.

Three questions, against a real Authority:

1. What attributable evidence verbs does a configured session actually have?
2. Can any of them be used before the derived proposal exists -- which is the
   order section 3 lists, `record_result_evidence` then `publish_result`?
3. If the order were inverted, would the same real sessions produce real,
   re-readable receipts on the DERIVED proposal?

No product or test file is changed. Disposable Authority only.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, "/home/sl/src/baton/v12/python/src")

from baton_v12.authority import Authority  # noqa: E402
from baton_v12.authority.errors import Refusal  # noqa: E402

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123456f-W133117"
PRODUCER = "baton.producer"
INTEGRATOR = "baton.integrator"
OWNERS = {"verification": ("baton.result-verify", "verify"),
          "review": ("baton.result-review", "review"),
          "approval": ("baton.result-approve", "approve")}

answers = {}
root = tempfile.mkdtemp(prefix="p-amendment-")
authority = Authority.create(os.path.join(root, "authority.sqlite3"),
                             authority_uuid=UUID)
try:
    authority.set_policy("canonical_target", "a" * 40)
    authority.create_work(WORK, "impl", contract="v12-assignment-1",
                          operation_id="create-work")
    authority.add_route_handler("impl", PRODUCER)
    authority.add_route_handler("integ", INTEGRATOR)
    for participant, verb in OWNERS.values():
        authority.grant_capability(participant, verb)

    producer = authority.session(PRODUCER)
    claimed = producer.claim({"work_id": WORK, "operation_id": "claim-1"})
    producer.publish({"expect": claimed["assignment"],
                      "operation_id": "publish-original",
                      "proposal_id": "proposal-b1", "result_id": "result-b1",
                      "result_digest": "sha256:" + "1" * 64,
                      "candidate_digest": "b" * 40,
                      "input_digest": "sha256:" + "2" * 64,
                      "policy_digest": "sha256:" + "3" * 64})
    producer.pass_work({"expect": claimed["assignment"],
                        "operation_id": "pass-to-integ", "to_route": "integ"})
    integrator = authority.session(INTEGRATOR)
    fixed = integrator.claim({"work_id": WORK,
                              "operation_id": "claim-integ"})["assignment"]

    # -- 1. what an owner actually has ---------------------------------------
    session = authority.session(OWNERS["verification"][0])
    answers["session_verbs"] = sorted(
        name for name in dir(session) if not name.startswith("_"))
    import inspect
    answers["evidence_verb_signatures"] = {
        verb: str(inspect.signature(getattr(session, verb)))
        for _participant, verb in OWNERS.values()}

    # -- 2. can an owner judge a RESULT before its proposal exists? -----------
    #
    # Every attributable evidence verb the Authority exposes is keyed by
    # proposal_id. In section 3's order the derived proposal does not exist
    # when `record_result_evidence` runs, so there is nothing for a real owner
    # to write a receipt against.
    try:
        session.verify({"proposal_id": "proposal-derived-not-yet",
                        "verification_id": "v1",
                        "observation": "passed",
                        "operation_id": "verify-before-publication"})
        answers["evidence_before_publication"] = "ACCEPTED -- unexpected"
    except Refusal as refused:
        answers["evidence_before_publication"] = f"refused: {refused}"

    # And the shape P's corrected interface asks for is not a shape these
    # verbs take at all, which is the review's own observation.
    try:
        session.verify({"result_id": "result-1",
                        "content_digest": "sha256:" + "4" * 64,
                        "candidate": "c" * 40, "target": "a" * 40,
                        "observations": "sha256:" + "5" * 64})
        answers["result_shaped_operands"] = "ACCEPTED -- unexpected"
    except TypeError as refused:
        answers["result_shaped_operands"] = f"TypeError: {refused}"
    except Refusal as refused:
        answers["result_shaped_operands"] = f"refused: {refused}"

    # -- 3. would the INVERTED order work with the same real owners? ----------
    derived = integrator.publish({
        "expect": fixed, "operation_id": "publish-derived",
        "proposal_id": "proposal-derived", "result_id": "result-combined",
        "result_digest": "sha256:" + "6" * 64, "candidate_digest": "d" * 40,
        "input_digest": "sha256:" + "7" * 64,
        "policy_digest": "sha256:" + "8" * 64, "target": "c" * 40})
    answers["derived_proposal_published_first"] = derived["proposal_id"]
    generation = authority.policy_generation()
    written = {}
    for kind, (participant, verb) in OWNERS.items():
        owner = authority.session(participant)
        operands = {"proposal_id": "proposal-derived",
                    "operation_id": f"derived-{kind}"}
        if kind == "verification":
            operands.update(verification_id="derived-verification-1",
                            observation="passed")
        elif kind == "review":
            operands.update(review_id="derived-review-1",
                            disposition="accepted")
        else:
            operands.update(approval_id="derived-approval-1",
                            disposition="approved",
                            policy_generation=generation)
        written[kind] = getattr(owner, verb)(operands)
    answers["real_receipts_on_the_derived_proposal"] = {
        kind: {"actor": one["actor"], "disposition": one["disposition"],
               "candidate_digest": one["candidate_digest"],
               "target": one["target"]}
        for kind, one in written.items()}
    answers["receipts_read_back"] = {
        kind: authority.receipt("proposal-derived", kind)["actor"]
        for kind in OWNERS}
    answers["the_producers_receipts_are_untouched"] = (
        authority.receipts("proposal-b1"))
finally:
    authority.dispose()

print(json.dumps(answers, indent=2, default=str))
gap = (answers["evidence_before_publication"].startswith("refused")
       and not answers["result_shaped_operands"].startswith("ACCEPTED"))
inverted_works = (len(answers["real_receipts_on_the_derived_proposal"]) == 3
                  and set(answers["receipts_read_back"].values())
                  == {participant for participant, _ in OWNERS.values()})
print("\nEVIDENCE-BEFORE-PUBLICATION IS EXPRESSIBLE WITH REAL OWNERS:",
      "NO" if gap else "YES")
print("PUBLICATION-BEFORE-EVIDENCE IS EXPRESSIBLE WITH REAL OWNERS:",
      "YES" if inverted_works else "NO")
sys.exit(0 if (gap and inverted_works) else 1)
