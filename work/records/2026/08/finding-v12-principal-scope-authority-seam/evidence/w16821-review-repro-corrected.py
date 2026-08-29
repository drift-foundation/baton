"""The reviewer's own reproduction, re-run against the corrected seam.

`w16821-review-repro.py` beside this file is the reviewer's script, kept
byte-for-byte.  Re-run unchanged it now stops at "verification receipt is
immutable", and that is the correction rather than a failure: its FIRST step --
the verifier granted `verify` only in the Work's own `scope:platform` -- used
to be refused and now succeeds, so its second step collides with the receipt
the first one wrote.

This companion runs the same three scenarios and REPORTS each outcome instead
of assuming the old one, so the two files read side by side say exactly what
changed.  Run from `v12/python` with `PYTHONPATH=src python3 <this file>`.
"""

import json
import os
import tempfile

from baton_v12.authority import Authority, Refusal, V12

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
ROUTE = "impl"
CLAUDE = "baton.claude"
VERIFIER = "baton.gemini"
CLOSER = "baton.closer"
SCOPE = "scope:platform"


def authority(root):
    return Authority.create(os.path.join(root, "authority.sqlite3"),
                            authority_uuid=UUID,
                            clock=lambda: "2026-08-28T20:00:00.000Z")


def attempt(call):
    try:
        return {"result": "accepted", "answer": call()}
    except Refusal as error:
        return {"result": "refused", "detail": str(error)}


answers = {}

# -- [P0] the receipt door decides in the TARGET's scope ---------------------
with tempfile.TemporaryDirectory(prefix="w16821-corrected-") as root:
    face = authority(root)
    core = face._core
    core.create_work(WORK, ROUTE, contract=V12, scope=SCOPE)
    core.add_route_handler(ROUTE, CLAUDE)
    assignment = core.claim(WORK, CLAUDE, operation_id="claim")
    core.publish(assignment, operation_id="publish", proposal_id="proposal-1",
                 result_id="result-1", result_digest="sha256:result",
                 candidate_digest="sha256:candidate",
                 input_digest="sha256:input", policy_digest="sha256:policy")
    answers["work_scope"] = face.project_work(WORK)["scope"]

    # The grant the reviewer's script found REFUSED.
    face.grant_capability(VERIFIER, "verify", scope=SCOPE)
    answers["scope_only_receipt"] = attempt(
        lambda: core.verify(proposal_id="proposal-1",
                            verification_id="verify-1", actor=VERIFIER,
                            observation="passed",
                            operation_id="verify-platform"))["result"]
    answers["recorded_receipt_scope"] = (
        face.receipt("proposal-1", "verification")["decision"]
        ["effective_scope"])

    # A SECOND verifier holding the capability only deployment-wide, so the
    # negative half is not hidden by the receipt the positive half wrote.
    face.grant_capability("baton.other", "verify")
    answers["deployment_only_receipt"] = attempt(
        lambda: core.review(proposal_id="proposal-1", review_id="review-1",
                            actor="baton.other", disposition="accepted",
                            operation_id="review-deployment"))
    face.grant_capability(VERIFIER, "verify")
    answers["capabilities_of_after_two_scoped_grants"] = \
        face.capabilities_of(VERIFIER)
    answers["grants_of_after_two_scoped_grants"] = face.grants_of(VERIFIER)
    answers["assignment_decision"] = [
        event["decision"] for event in face.assignment_events(WORK)
        if event["cause"] == "claimed"]
    answers["proposal_decision"] = face.proposal("proposal-1")["decision"]
    face.dispose()

# -- [P0] close decides in the Work's scope AND retains its decision ---------
with tempfile.TemporaryDirectory(prefix="w16821-corrected-close-") as root:
    face = authority(root)
    core = face._core
    core.create_work(WORK, ROUTE, contract=V12, scope=SCOPE)
    face.grant_capability(CLOSER, "close", scope=SCOPE)
    answers["scope_only_close"] = attempt(
        lambda: core.close(WORK, operation_id="close-platform",
                           outcome="satisfying", rationale="done",
                           actor=CLOSER))["result"]
    answers["work_close_decision"] = face.project_work(WORK)["close_decision"]
    face.dispose()

with tempfile.TemporaryDirectory(prefix="w16821-corrected-wrong-") as root:
    face = authority(root)
    core = face._core
    core.create_work(WORK, ROUTE, contract=V12, scope=SCOPE)
    face.grant_capability(CLOSER, "close")
    answers["deployment_only_close"] = attempt(
        lambda: core.close(WORK, operation_id="close-deployment",
                           outcome="satisfying", rationale="done",
                           actor=CLOSER))
    answers["still_open_after_refused_close"] = \
        face.project_work(WORK)["status"]
    face.dispose()

print(json.dumps(answers, indent=1, sort_keys=True))
