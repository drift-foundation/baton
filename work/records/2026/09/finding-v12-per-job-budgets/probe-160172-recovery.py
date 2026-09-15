"""What the SUPPORTED explicit recovery verbs answer over a host-verification
hold, and WHICH assignment -- if any -- this deployment ever composed for the
account that hold is recorded under.

Read-only intent: every call is an owner's own, and whatever it answers,
including a refusal, is printed rather than worked around. Nothing is written."""
import json
import traceback
from unittest.mock import patch

from tests.tools.test_execution_limits import (
    TheComposedHostVerificationUsesTheJobsCeiling as Case)
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import queue, reconciliation, recovery, runtime

KEYS = ("attempt_id", "entry_id", "lease_id", "fence")


def refusal(what, call, *arguments, **named):
    try:
        return {what: call(*arguments, **named)}
    except ContractRefusal as refused:
        return {what: {"category": refused.category, "code": refused.code,
                       "message": str(refused)}}
    except Exception:                                       # noqa: BLE001
        return {what: traceback.format_exc().splitlines()[-1]}


case = Case("test_a_post_import_overrun_runs_once_and_defers")
case.setUp()
answer = {}
try:
    composed = []
    composing = runtime.compose_assignment

    def watching(*arguments, **named):
        made = composing(*arguments, **named)
        composed.append(made)
        return made

    with patch.object(runtime, "compose_assignment", watching):
        held, deployment, result_id, _before = case._post_import_failure(
            failing=True)
    row = reconciliation.result_of(deployment.integration, result_id)
    target = queue.target_of(deployment.integration,
                             row["canonical_target_id"])
    account = target["blocked_account"]
    answer["blocked_reason"] = target["blocked_reason"]
    answer["account"] = {name: account.get(name) for name in KEYS}
    answer["composed_assignments"] = [
        {name: one.get(name) for name in KEYS} for one in composed]
    answer["account_was_ever_composed"] = any(
        all(one.get(name) == account.get(name) for name in KEYS)
        for one in composed)
    if composed:
        answer.update(refusal("held_status_with_composed",
                              recovery.held_status, deployment.integration,
                              held.control, None, composed[-1]))
        answer.update(refusal("abandon_with_composed",
                              recovery.abandon_held_lease,
                              deployment.integration, held.control, None,
                              composed[-1]))
    answer.update(refusal(
        "compose_from_the_account", runtime.compose_assignment,
        deployment.integration, held.control,
        profile=deployment.integration_profile,
        canonical_target_id=row["canonical_target_id"],
        entry_id=account["entry_id"], lease_id=account["lease_id"],
        fence=account["fence"], attempt_id=account["attempt_id"]))
    after = queue.target_of(deployment.integration,
                            row["canonical_target_id"])
    answer["target_state_after"] = after["state"]
    answer["target_unchanged"] = after == target
    answer["result_unchanged"] = (
        reconciliation.result_of(deployment.integration, result_id) == row)
    answer["counts"] = [len(case.seen), case.materialized]
    print(json.dumps(answer, indent=2, default=str))
finally:
    case.doCleanups()
