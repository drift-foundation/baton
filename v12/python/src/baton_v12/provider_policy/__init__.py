"""Closed provider policy shared by composition and the delivered worker.

Standard-library only, like source_profiles: images receive this package under
its own name. New policy selection is explicit; legacy documents never enter
this module. A provider absent from REALIZATIONS cannot be composed.
"""
from copy import deepcopy
import hashlib
import json
import os

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
        "user_configuration": "private-home-managed-worker-instructions",
        "credentials": {"mode": "delivered", "path": ".claude/.credentials.json"},
        "environment": ENVIRONMENT,
        "ephemera": "fresh-scratch-roots",
        "model_substitution": {"selector_argument": "--model", "fallback": None},
    },
}
# No Codex realization is invented before its separately selected inventory.
# W385853: what Baton itself places in a selected provider home, and which
# launch roles the realization serves. One closed entry per provider; the
# bytes are the packaged copy of docs/V12-WORKER-INSTRUCTIONS.md.
INSTRUCTIONS_FILE = "worker_instructions.md"
INSTRUCTIONS_KIND = "worker-instructions"
INSTRUCTIONS_BOUND = 16384
MANAGED = {"claude": {"path": ".claude/CLAUDE.md", "kind": INSTRUCTIONS_KIND}}
LABEL_SCHEMA = "baton.native-worker-context/1"
LABEL_BOUND = 2048
LABEL_ROLES = {"claude": ["implementation", "review"], "codex": ["implementation"]}
# Entry and delivered-slot names are host/worker interface facts, not vendor
# credential filenames. Codex still has no REALIZATIONS or MANAGED entry (J1).
ENTRYPOINTS = {"claude": ["python3", "/opt/baton/dogfood_entry.py"],
               "codex": ["python3", "/opt/baton/codex_entry.py"]}
CREDENTIAL_SLOTS = {"claude": "claude", "codex": "codex"}
# The execution-context label. It states which instructions apply; it grants
# nothing. It names no Job, attempt, worker or protocol path.
LABEL_TEMPLATE = """\
[Baton execution context: baton.native-worker-context/1]
You are running as a Baton native v12 worker. Assigned role: {role}.
The Baton execution contract for this run delivers this context. It is not
inferred from the container, the working directory, a role name in a file,
or any text in the source tree.

Applies to you:
- The task below and its stated limits.
- The Baton worker instructions at {home}/{entry} (sha256 {digest}). Read
  that file before acting if its content is not already in your
  instructions.
- Project coding, design and test guidance in the source tree, where the
  task touches it.
- Protected-main and task boundaries, wherever a repository is mounted.

Does not apply to you:
- The host-agent procedures in the source tree's AGENTS.md and
  docs/HOST-INTEGRATION.md: v11 claims, routes and readiness, host
  handoffs, dossier and review-journal maintenance, host integration and
  human Git checkpoints. Do not perform them. The safety, scope and honest
  evidence rules stated there still hold.

This label states which instructions apply. It grants no permission and
removes no restriction.
"""
# Participation sources are bound separately to the evidenced CLI build.
PARTICIPATION = {("claude", "2.1.247"): [{"field": "modelUsage", "kind": "keys"}]}
# Optional service tiers, bound like participation to the evidenced CLI build.
# A selection without the member asks for nothing: no tier is ever selected
# implicitly. The 0.169.0 exec help evidences `-c <key=value>` with a TOML
# value; that this build recognizes the `service_tier` key is NOT evidenced
# by the retained help and stays a qualification observation.
SERVICE_TIERS = {("codex", "0.169.0"): {"fast": ["-c", 'service_tier="fast"']}}


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


def _sha256(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def worker_instructions():
    """The packaged worker-instruction bytes, or a refusal. Never a default."""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), INSTRUCTIONS_FILE), "rb") as source:
            raw = source.read(INSTRUCTIONS_BOUND + 1)
    except OSError as failure:
        raise PolicyRefusal("packaged worker instructions are absent or unreadable") from failure
    if not raw or len(raw) > INSTRUCTIONS_BOUND:
        raise PolicyRefusal("packaged worker instructions are empty or exceed the delivery bound")
    return raw


def _managed_entries(provider):
    raw = worker_instructions()
    return [dict(MANAGED[provider], sha256=_sha256(raw), bytes=len(raw))]


def _context_label(provider):
    return {"schema": LABEL_SCHEMA, "template_sha256": _sha256(LABEL_TEMPLATE.encode()),
            "placement": "prompt-prefix", "roles": list(LABEL_ROLES[provider]), "bound": LABEL_BOUND}


def managed_payloads(document):
    """(path, bytes, sha256) for home.prepare, checked against the adapter."""
    entries = document.get("managed_entries") if type(document) is dict else None
    if (type(entries) is not list or document.get("provider") not in MANAGED
            or entries != _managed_entries(document["provider"])):
        raise PolicyRefusal("managed entries are not this build's closed delivery")
    raw = worker_instructions()
    return [(one["path"], raw, one["sha256"]) for one in entries]


def context_label(document, role):
    """The exact label bytes for one adapter and launch role."""
    bound = document.get("context_label") if type(document) is dict else None
    provider = document.get("provider") if type(document) is dict else None
    if provider not in LABEL_ROLES or bound != _context_label(provider):
        raise PolicyRefusal("execution-context label is not this build's template")
    if type(role) is not str or role not in bound["roles"]:
        raise PolicyRefusal("launch role has no execution-context label")
    entries = [one for one in document.get("managed_entries", []) if type(one) is dict and one.get("kind") == INSTRUCTIONS_KIND]
    if len(entries) != 1 or type(document.get("home")) is not str:
        raise PolicyRefusal("execution-context label has no single worker-instructions entry")
    raw = LABEL_TEMPLATE.format(role=role, home=document["home"], entry=entries[0]["path"],
                                digest=entries[0]["sha256"].removeprefix("sha256:")).encode()
    if len(raw) > bound["bound"]:
        raise PolicyRefusal("execution-context label exceeds its bound")
    return raw


def labelled(document, role, prompt):
    """The prompt operand: label, one blank line, the unchanged prompt."""
    if type(prompt) is not str:
        raise PolicyRefusal("provider prompt must be text")
    return context_label(document, role).decode() + "\n" + prompt


def context_record(document, role):
    """What a worker reports and the manager recomputes for one turn."""
    entries = [one for one in document["managed_entries"] if one.get("kind") == INSTRUCTIONS_KIND]
    return {"schema": LABEL_SCHEMA, "role": role,
            "context_label_digest": _sha256(context_label(document, role)),
            "worker_instructions_digest": entries[0]["sha256"]}


def service_tier_arguments(provider, cli_build, tier):
    """The exact extra argv of one selected tier; an unset tier adds nothing."""
    if tier is None:
        return []
    known = SERVICE_TIERS.get((provider, cli_build), {})
    if type(tier) is not str or tier not in known:
        raise PolicyRefusal("selected service tier has no realization for this provider and CLI build")
    return list(known[tier])


def selection(value):
    members = {"provider", "requested_model", "reported_identity", "cli_build"}
    # `service_tier` is the one optional member. Unset is spelled by omitting
    # it, so a selection without a tier keeps its existing bytes and digest.
    if type(value) is not dict or not members <= set(value) <= members | {"service_tier"}:
        raise PolicyRefusal("provider selection requires provider, model, exact reported identity and CLI build")
    for key in sorted(members):
        _text(value[key], key)
    if value["provider"] not in REALIZATIONS:
        raise PolicyRefusal("selected provider has no supported policy realization")
    if "service_tier" in value:
        if value["service_tier"] is None:
            raise PolicyRefusal("an unset service tier is omitted, not null")
        service_tier_arguments(value["provider"], value["cli_build"], value["service_tier"])
    return dict(value)


def credential_slot(provider):
    if provider not in CREDENTIAL_SLOTS:
        raise PolicyRefusal("provider has no delivered credential slot")
    return CREDENTIAL_SLOTS[provider]


def validate_execution(document, role, provider_context=None):
    """Codex is fresh and serves only its bound context-label roles.

    Claude's existing integration behavior is separately owned (W386048).
    The caller first validates the adapter; this adds no alternative role list.
    """
    if document.get("provider") == "codex":
        if provider_context is not None or role not in document["context_label"]["roles"]:
            raise PolicyRefusal("Codex requires a fresh launch in a declared label role")


def validate_credential_slots(document, slots, profile):
    if document.get("provider") == "codex":
        slot = credential_slot("codex")
        if slots != [slot] or type(profile) is not dict or set(profile) != {slot}:
            raise PolicyRefusal("Codex requires exactly its declared credential slot")


def adapter(selected, *, network, tool_policy=None):
    selected = selection(selected)
    policy = POLICY if tool_policy is None else tool_policy
    if policy != POLICY:
        raise PolicyRefusal("selected shared policy has no supported realization")
    provider = selected["provider"]
    realization = REALIZATIONS[provider]
    if set(realization) != set(POLICY) - {"schema"}:
        raise PolicyRefusal("provider realization does not cover the shared policy")
    if provider not in MANAGED or provider not in LABEL_ROLES or provider not in ENTRYPOINTS:
        raise PolicyRefusal("provider realization declares no instruction delivery")
    command = realization["interaction"]
    document = {
        "schema": "baton.single-implementation-adapter/2",
        "adapter_name": "docker-single-worker", "engine": "docker",
        "network": network, "entrypoint": list(ENTRYPOINTS[provider]),
        "provider": provider,
        "argv_policy": {"program": command["program"],
                        "fixed": [*command["before_permissions"], *realization["tool_permission"], *command["after_permissions"]],
                        "model_argument": realization["model_substitution"]["selector_argument"],
                        "prompt": "last", "fallback": None},
        "environment_policy": deepcopy(realization["environment"]),
        "home": HOME, "credential": deepcopy(realization["credentials"]),
        "managed_entries": _managed_entries(provider),
        "context_label": _context_label(provider),
        "participation_sources": deepcopy(PARTICIPATION.get((provider, selected["cli_build"]), [])),
        "implements_tool_policy": digest(POLICY),
        "realization": deepcopy(realization),
    }
    if "service_tier" in selected:
        # Present only when selected: the adapter digest of every existing
        # selection is unchanged, and a tiered one is a different identity.
        document["argv_policy"]["service_tier"] = {
            "requested": selected["service_tier"],
            "arguments": service_tier_arguments(provider, selected["cli_build"], selected["service_tier"])}
    return document


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
    return [rule["program"], *rule["fixed"], rule["model_argument"], selected["requested_model"],
            *rule.get("service_tier", {}).get("arguments", []), prompt]


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
             ("reported_identity", selected["reported_identity"]), ("cli_build", selected["cli_build"]),
             ("service_tier", selected.get("service_tier"))))):
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
