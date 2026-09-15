"""Reviewer probe: real disposable Authority and composed configuration, no live store."""
import json
from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal
from tests.tools.test_scheduler_trace import TheComposedOwnersSupplyAuthorizedTransitions

out = {}
for mode in ("no_grant", "wrong_scope", "correct_scope"):
    outer = TheComposedOwnersSupplyAuthorizedTransitions()
    outer.setUp()
    case = outer.case
    try:
        with Authority.open(case.authority_path, expected_authority_uuid=case.config["authority_uuid"]) as authority:
            if mode != "no_grant":
                authority.grant_capability("other.reviewer", "review", scope=case.scope if mode == "correct_scope" else "scope:elsewhere")
            holds = authority.holds_capability("other.reviewer", "review", scope=case.scope)
            principal = authority.principal_of("other.reviewer")
        participants = dict(case.document()["receipt_participants"], review="other.reviewer")
        try:
            _job, _control, composed = case.serving_two(receipt_participants=participants)
            out[mode] = dict(composed=True, participant=composed.sessions["review"].participant, principal=principal, scope=case.scope, holds_capability=holds)
        except ContractRefusal as exc:
            out[mode] = dict(composed=False, category=exc.category, code=exc.code, message=str(exc), principal=principal, scope=case.scope, holds_capability=holds)
    finally:
        outer.doCleanups()
print(json.dumps(out, indent=2))
assert not out["no_grant"]["composed"]
assert not out["wrong_scope"]["composed"]
assert out["correct_scope"]["composed"]
