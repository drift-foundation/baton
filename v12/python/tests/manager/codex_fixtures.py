"""Synthetic Codex policy for offline seam tests, NEVER vendor path evidence.

Production deliberately has no Codex realization. These patch-only names let
ordinary policy/delivery/home owners run while J1 remains unresolved.
"""
from contextlib import contextmanager, ExitStack
from copy import deepcopy
from unittest import mock

SELECTED = dict(provider="codex", requested_model="fixture-selector",
                reported_identity="fixture-reported", cli_build="0.169.0")


@contextmanager
def simulated(policy, *, home=None):
    realization = deepcopy(policy.REALIZATIONS["claude"])
    realization["interaction"] = {"program": "codex", "before_permissions": ["exec"],
        "after_permissions": ["--ignore-user-config", "--ignore-rules", "--json"]}
    realization["tool_permission"] = ["--dangerously-bypass-approvals-and-sandbox"]
    realization["credentials"] = {"mode": "seeded-retained", "path": "fixture/credential"}
    with ExitStack() as stack:
        stack.enter_context(mock.patch.dict(policy.REALIZATIONS, {"codex": realization}))
        stack.enter_context(mock.patch.dict(policy.MANAGED, {
            "codex": {"path": "fixture/instructions.md", "kind": policy.INSTRUCTIONS_KIND}}))
        if home is not None:
            stack.enter_context(mock.patch.object(policy, "HOME", str(home)))
            stack.enter_context(mock.patch.dict(policy.ENVIRONMENT, HOME=str(home)))
        yield


def delivered(policy):
    adapter = policy.adapter(SELECTED, network="bridge")
    profile = {"schema": "baton.single-implementation-runtime-profile/2", "provider": "codex",
               "model": SELECTED["requested_model"], "reported_identity": SELECTED["reported_identity"],
               "cli_build": SELECTED["cli_build"]}
    return policy.delivery({"selection": SELECTED, "adapter": adapter, "runtime_profile": profile},
        adapter_digest=policy.digest(adapter), profile_digest=policy.digest(profile),
        tool_policy_digest=policy.digest(policy.POLICY), authority_uuid="fixture-authority",
        job_id="fixture-job", worker_id="fixture-worker", attempt_id="fixture-attempt")


def configured(policy, *, attempt="fixture-attempt", job="fixture-job", authority="fixture-authority"):
    """Synthetic immutable image and adapter-call receipt, no native qualification."""
    from . import provider_fixtures
    from baton_v12.provider_policy import attribution
    with simulated(policy):
        value = provider_fixtures.delivery(attempt=attempt, job=job, authority=authority, **SELECTED)
        prompt = policy.labelled(value["contract"]["adapter"], "implementation", "SYNTHETIC PRIVATE PROMPT")
        receipt = attribution.invocation_record(value, "implementation",
            policy.argv(value["contract"]["adapter"], SELECTED, prompt), policy.ENVIRONMENT, 0, evidenced_build="0.169.0")
    return value, receipt
