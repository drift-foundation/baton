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

with tempfile.TemporaryDirectory(prefix="w16821-review-") as root:
    face = authority(root)
    core = face._core
    core.create_work(WORK, ROUTE, contract=V12, scope=SCOPE)
    core.add_route_handler(ROUTE, CLAUDE)
    assignment = core.claim(WORK, CLAUDE, operation_id="claim")
    core.publish(assignment, operation_id="publish", proposal_id="proposal-1",
                 result_id="result-1", result_digest="sha256:result",
                 candidate_digest="sha256:candidate",
                 input_digest="sha256:input", policy_digest="sha256:policy")
    face.grant_capability(VERIFIER, "verify", scope=SCOPE)
    try:
        core.verify(proposal_id="proposal-1", verification_id="verify-1",
                    actor=VERIFIER, observation="passed",
                    operation_id="verify-platform")
    except Refusal as error:
        scoped_receipt = {"result": "refused", "detail": str(error)}
    else:
        scoped_receipt = {"result": "accepted"}
    face.grant_capability(VERIFIER, "verify")
    receipt = core.verify(proposal_id="proposal-1", verification_id="verify-2",
                          actor=VERIFIER, observation="passed",
                          operation_id="verify-deployment")
    receipt_row = face.receipt("proposal-1", "verification")
    capability_projection = face.capabilities_of(VERIFIER)
    face.dispose()

with tempfile.TemporaryDirectory(prefix="w16821-review-close-") as root:
    face = authority(root)
    core = face._core
    core.create_work(WORK, ROUTE, contract=V12, scope=SCOPE)
    face.grant_capability(CLOSER, "close", scope=SCOPE)
    try:
        core.close(WORK, operation_id="close-platform", outcome="satisfying",
                   rationale="done", actor=CLOSER)
    except Refusal as error:
        scoped_close = {"result": "refused", "detail": str(error)}
    else:
        scoped_close = {"result": "accepted"}
    face.grant_capability(CLOSER, "close")
    closed = core.close(WORK, operation_id="close-deployment",
                        outcome="satisfying", rationale="done", actor=CLOSER)
    work_columns = [row[1] for row in core._store._db.execute("PRAGMA table_info(work)")]
    assignment_events = [dict(row) for row in core._store.all(
        "SELECT principal_id, effective_scope, grant_provenance, policy_generation "
        "FROM assignment_event")]
    face.dispose()

print({
    "work_scope": SCOPE,
    "scope_only_receipt": scoped_receipt,
    "deployment_grant_receipt": receipt,
    "recorded_receipt_scope": receipt_row["effective_scope"],
    "capabilities_of_after_two_scoped_grants": capability_projection,
    "scope_only_close": scoped_close,
    "deployment_grant_close": closed,
    "work_has_close_decision_columns": [name for name in work_columns if name in {
        "principal_id", "effective_scope", "grant_provenance", "policy_generation"}],
    "close_assignment_decisions": assignment_events,
})
