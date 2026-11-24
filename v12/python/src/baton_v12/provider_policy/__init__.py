"""Closed provider policy shared by composition and the delivered worker.

Standard-library only, like source_profiles: images receive this package under
its own name. New policy selection is explicit; legacy documents never enter
this module. A provider absent from REALIZATIONS cannot be composed.
"""
from copy import deepcopy
import hashlib
import json

POLICY = {
    "schema": "baton.worker-tool-policy/2",
    "interaction": "noninteractive-one-prompt-one-process",
    "tool_permission": "full-inside-container",
    "provider_sandbox": "none-container-boundary",
    "user_configuration": "adapter-composed-only",
    "credentials": "delivered-no-ambient-no-operator-writes",
    "environment": "closed-composed",
    "ephemera": "fresh-per-child",
    "model_substitution": "none",
}
HOME = "/run/baton/provider-home"
ENVIRONMENT = {"HOME": HOME, "PATH": "/usr/local/bin:/usr/bin:/bin",
               "TMPDIR": "fresh", "XDG_CACHE_HOME": "fresh",
               "PYTHONPYCACHEPREFIX": "fresh"}
# Each policy member has one concrete realization. Unknown providers and
# selected values refuse rather than inheriting another provider's flags.
REALIZATIONS = {
    "claude": {
        "interaction": {"program": "claude", "before_permissions": ["--print"],
                        "after_permissions": ["--output-format", "json"]},
        "tool_permission": ["--dangerously-skip-permissions"],
        "provider_sandbox": "container",
        "user_configuration": "private-home-empty-managed-entries",
        "credentials": {"mode": "delivered", "path": ".claude/.credentials.json"},
        "environment": ENVIRONMENT,
        "ephemera": "fresh-scratch-roots",
        "model_substitution": {"selector_argument": "--model", "fallback": None},
    },
}
# No Codex realization is invented before its separately selected inventory.
# Participation sources are bound separately to the evidenced CLI build.
PARTICIPATION = {("claude", "2.1.247"): [{"field": "modelUsage", "kind": "keys"}]}


class PolicyRefusal(ValueError):
    pass


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _text(value, what):
    if type(value) is not str or not value or len(value) > 256 or any(ord(c) < 32 for c in value):
        raise PolicyRefusal(what + " must be explicit bounded text")
    return value


def selection(value):
    members = {"provider", "requested_model", "reported_identity", "cli_build"}
    if type(value) is not dict or set(value) != members:
        raise PolicyRefusal("provider selection requires provider, model, exact reported identity and CLI build")
    for key in sorted(members):
        _text(value[key], key)
    if value["provider"] not in REALIZATIONS:
        raise PolicyRefusal("selected provider has no supported policy realization")
    return dict(value)


def adapter(selected, *, network, tool_policy=None):
    selected = selection(selected)
    policy = POLICY if tool_policy is None else tool_policy
    if policy != POLICY:
        raise PolicyRefusal("selected shared policy has no supported realization")
    provider = selected["provider"]
    realization = REALIZATIONS[provider]
    if set(realization) != set(POLICY) - {"schema"}:
        raise PolicyRefusal("provider realization does not cover the shared policy")
    command = realization["interaction"]
    return {
        "schema": "baton.single-implementation-adapter/2",
        "adapter_name": "docker-single-worker", "engine": "docker",
        "network": network, "entrypoint": ["python3", "/opt/baton/dogfood_entry.py"],
        "provider": provider,
        "argv_policy": {"program": command["program"],
                        "fixed": [*command["before_permissions"], *realization["tool_permission"], *command["after_permissions"]],
                        "model_argument": realization["model_substitution"]["selector_argument"],
                        "prompt": "last", "fallback": None},
        "environment_policy": deepcopy(realization["environment"]),
        "home": HOME, "credential": deepcopy(realization["credentials"]),
        "managed_entries": [],
        "participation_sources": deepcopy(PARTICIPATION.get((provider, selected["cli_build"]), [])),
        "implements_tool_policy": digest(POLICY),
        "realization": deepcopy(realization),
    }


def validate_adapter(document, selected, *, adapter_digest, tool_policy_digest):
    if type(document) is not dict or digest(document) != adapter_digest:
        raise PolicyRefusal("adapter identity disagrees")
    if document.get("implements_tool_policy") != tool_policy_digest:
        raise PolicyRefusal("adapter implements a different Job tool policy")
    expected = adapter(selected, network=document.get("network"))
    if document != expected:
        raise PolicyRefusal("adapter is not this build's selected realization")
    return deepcopy(document)


def argv(document, selected, prompt):
    selected = selection(selected)
    if document != adapter(selected, network=document.get("network")):
        raise PolicyRefusal("provider command policy disagrees")
    rule = document["argv_policy"]
    return [rule["program"], *rule["fixed"], rule["model_argument"], selected["requested_model"], prompt]


def delivery(binding, *, adapter_digest, profile_digest, tool_policy_digest,
             authority_uuid, job_id, worker_id, attempt_id):
    if type(binding) is not dict or set(binding) != {"selection", "adapter", "runtime_profile"}:
        raise PolicyRefusal("provider contract members disagree")
    selected = selection(binding["selection"])
    validate_adapter(binding["adapter"], selected,
                     adapter_digest=adapter_digest, tool_policy_digest=tool_policy_digest)
    profile = binding["runtime_profile"]
    if (type(profile) is not dict or profile.get("schema") != "baton.single-implementation-runtime-profile/2"
            or digest(profile) != profile_digest or any(profile.get(key) != value for key, value in
            (("provider", selected["provider"]), ("model", selected["requested_model"]),
             ("reported_identity", selected["reported_identity"]), ("cli_build", selected["cli_build"])))):
        raise PolicyRefusal("selected profile identity disagrees")
    for name, value in (("authority", authority_uuid), ("Job", job_id), ("worker", worker_id), ("attempt", attempt_id)):
        if type(value) is not str or not value:
            raise PolicyRefusal("provider delivery lacks " + name)
    return {"schema": "baton.provider-delivery/1", "contract": deepcopy(binding),
            "adapter_digest": adapter_digest, "profile_digest": profile_digest,
            "tool_policy_digest": tool_policy_digest,
            "home_identity": {"authority_uuid": authority_uuid, "job_id": job_id,
                              "worker_id": worker_id}, "attempt_id": attempt_id}


def validate_delivery(document, job_execution):
    members = {"schema", "contract", "adapter_digest", "profile_digest", "tool_policy_digest", "home_identity", "attempt_id"}
    if type(document) is not dict or set(document) != members or document["schema"] != "baton.provider-delivery/1":
        raise PolicyRefusal("provider delivery members disagree")
    bound = document["home_identity"]
    if type(bound) is not dict or set(bound) != {"authority_uuid", "job_id", "worker_id"}:
        raise PolicyRefusal("provider home identity disagrees")
    if (type(job_execution) is not dict or document["attempt_id"] != job_execution.get("attempt_id")
            or bound["job_id"] != job_execution.get("job_id")):
        raise PolicyRefusal("provider delivery belongs to another Job or attempt")
    expected = delivery(document["contract"], adapter_digest=document["adapter_digest"],
                        profile_digest=document["profile_digest"], tool_policy_digest=document["tool_policy_digest"],
                        **bound, attempt_id=document["attempt_id"])
    if expected != document:
        raise PolicyRefusal("provider delivery binding disagrees")
    return expected
