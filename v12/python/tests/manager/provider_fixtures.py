"""Synthetic provider identities; no account, registry or image is consulted."""
import json
from baton_v12 import provider_policy as policy
from tools import next_run_bindings

SELECTED = dict(provider="claude", requested_model="fixture-selector", reported_identity="fixture-reported", cli_build="2.1.247")


def identities(**changes):
    selected = dict(SELECTED, **changes)
    value = next_run_bindings.deployment_identities(image_reference="fixture/image:simulated",
        image_digest="sha256:" + "a" * 64, cli_build=selected["cli_build"], provider_network="bridge",
        runtime_uid=None, turn_seconds=30, verification_seconds=30, implementer_invocations=1,
        contextual=False, provider_selection=selected)
    return selected, value


def delivery(*, attempt="fixture-attempt", job="fixture-job", worker="fixture-worker", authority="fixture-authority", **changes):
    selected, value = identities(**changes)
    return policy.delivery({"selection": selected, "adapter": value["adapter"], "runtime_profile": value["runtime_profile"]},
        adapter_digest=value["adapter_digest"], profile_digest=value["profile_digest"], tool_policy_digest=policy.digest(policy.POLICY),
        authority_uuid=authority, job_id=job, worker_id=worker, attempt_id=attempt)


def terminal(*contributors, **changes):
    value = dict(type="result", subtype="success", is_error=False, modelUsage={name: {"outputTokens": 1} for name in contributors})
    value.update(changes)
    return json.dumps(value).encode()
