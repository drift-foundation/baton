"""Provider-selected evidence basis; configuration never becomes participation."""
import hashlib
import json
from . import PolicyRefusal, _text
from . import codex

SCHEMA = "baton.model-attribution/1"
CONFIGURED_SCHEMA = "baton.model-attribution/2"
MAX_OUTPUT = 1 << 16


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate member")
        result[key] = value
    return result


def contributors(raw, sources, *, partial=False):
    if partial or type(raw) is not bytes or len(raw) > MAX_OUTPUT:
        return {}
    try:
        value = json.loads(raw, object_pairs_hook=_pairs,
                           parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
        # This parser supports the qualified terminal-result family only.
        # Configuration echoes, text, tools and errors have no participation.
        if (type(value) is not dict or value.get("type") != "result"
                or value.get("subtype") != "success" or value.get("is_error") is not False):
            return {}
        found = {}
        for source in sources:
            field = source["field"]
            at = value
            for member in field.split("."):
                at = at.get(member) if type(at) is dict else None
            if at is None:
                continue
            if source["kind"] == "keys" and type(at) is dict:
                names = list(at)
            elif source["kind"] == "value" and type(at) is str:
                names = [at]
            else:
                return {}
            for name in names:
                _text(name, "reported contributor")
                found.setdefault(name, set()).add(field)
        return {name: sorted(found[name]) for name in sorted(found)}
    except (ValueError, UnicodeError, RecursionError, KeyError, TypeError):
        return {}


def record(delivery, *, phase, evidenced_build, raw, partial=False,
           raw_digest=None, log_retained=True, invocation=None):
    selected = delivery["contract"]["selection"]
    if selected["provider"] == "codex":
        return configured_record(delivery, phase=phase, evidenced_build=evidenced_build,
            raw=raw, partial=partial, raw_digest=raw_digest, log_retained=log_retained,
            invocation=invocation)
    sources = delivery["contract"]["adapter"]["participation_sources"]
    reported = contributors(raw, sources, partial=partial)
    if not log_retained:
        reported = {}
    if evidenced_build is not None:
        try:
            _text(evidenced_build, "evidenced build")
        except ValueError:
            evidenced_build = None
    outcome = ("missing" if not reported or evidenced_build is None else
               "matched" if selected["reported_identity"] in reported and evidenced_build == selected["cli_build"] else "conflicting")
    answer = {"schema": SCHEMA, "attempt_id": delivery["attempt_id"],
            "job_id": delivery["home_identity"]["job_id"], "phase": phase,
            "provider": selected["provider"], "selected_cli_build": selected["cli_build"],
            "evidenced_cli_build": evidenced_build, "requested_model": selected["requested_model"],
            "mapped_identity": selected["reported_identity"], "contributors": list(reported),
            "contributor_sources": reported, "outcome": outcome,
            "evidence": {"digest": raw_digest if raw_digest is not None else
                         ("sha256:" + hashlib.sha256(raw).hexdigest() if type(raw) is bytes else None),
                         "log": {"attempt_id": delivery["attempt_id"], "stream": "provider.stdout"}}}
    if "service_tier" in selected:
        # REQUESTED IS NOT OBSERVED. No build has a declared source for the
        # tier a provider actually served, so nothing here reads one: not the
        # selection, not argv, not a configuration echo in the output.
        answer["service_tier"] = {"requested": selected["service_tier"], "observed": None, "outcome": "missing"}
    return answer


def validate(value, delivery, *, phase, raw, invocation_raw=None):
    permitted = CONFIGURED_SCHEMA if delivery["contract"]["selection"]["provider"] == "codex" else SCHEMA
    if type(value) is not dict or value.get("schema") != permitted:
        raise PolicyRefusal("model-attribution-missing")
    if permitted == CONFIGURED_SCHEMA and value.get("invocation") is not None:
        try:
            if (type(invocation_raw) is not bytes or len(invocation_raw) > MAX_OUTPUT
                    or json.loads(invocation_raw, object_pairs_hook=_pairs) != value["invocation"]):
                raise ValueError("invocation receipt disagrees")
        except (ValueError, TypeError, UnicodeError, RecursionError) as failure:
            raise PolicyRefusal("model-attribution-invalid") from failure
    expected = record(delivery, phase=phase, evidenced_build=value.get("evidenced_cli_build"), raw=raw,
                      partial=raw is None, log_retained=raw is not None,
                      invocation=value.get("invocation") if permitted == CONFIGURED_SCHEMA else None)
    if value != expected:
        raise PolicyRefusal("model-attribution-invalid")
    return expected


def diagnostic(value):
    if value is None:
        return "Requested: not selected (account default)"
    if value.get("schema") == CONFIGURED_SCHEMA:
        return ("Requested: " + str(value["requested_model"]) + "; basis: configured-model; "
                + ("Configured model accepted" if acceptable(value) else "Configured model not accepted")
                + "; actual participation unknown; " + value["reroute_observation"]
                + ("; surface: Codex 0.169.0 exec --json stdout (complete framed invocation observation required; substantive judgment belongs to independent review)"
                   if value["selected_cli_build"] == "0.169.0" and value["evidenced_cli_build"] == "0.169.0"
                   else "; surface: unqualified or unknown CLI build")
                + "; invocation: adapter-recorded, host-validated; CLI build selected: "
                + str(value["selected_cli_build"]) + "; CLI build evidenced: "
                + (value["evidenced_cli_build"] or "no evidence")
                + "; admitted image: " + (value["image_digest"] or "no evidence")
                + "; attribution: " + value["outcome"]
                + ("; Service tier requested: " + value["service_tier"]["requested"] + "; observed: no evidence"
                   if value.get("service_tier") else ""))
    reported = value.get("contributors", [])
    present = value.get("mapped_identity") in reported
    return ("Requested: " + value["requested_model"] + "; mapped identity: " + value["mapped_identity"]
            + "; Reported contributors: " + (", ".join(reported) or "no evidence")
            + "; Requested model reported: " + ("yes" if present else "no" if reported else "no evidence")
            + "; CLI build selected: " + value["selected_cli_build"]
            + "; CLI build evidenced: " + (value.get("evidenced_cli_build") or "no evidence")
            + "; attribution: " + value["outcome"]
            + ("; Service tier requested: " + value["service_tier"]["requested"] + "; observed: "
               + (value["service_tier"]["observed"] or "no evidence") if value.get("service_tier") else ""))


def acceptable(value):
    return ((value.get("schema") == SCHEMA and value.get("outcome") == "matched")
            or (value.get("schema") == CONFIGURED_SCHEMA and value.get("basis") == "configured-model"
                and value.get("outcome") == "configured-model-accepted"))


def invocation_record(delivery, phase, argv, environment, status, *, expected_home=None, evidenced_build=None):
    """Capture the actual adapter call vector, never infer it from stdout.

    Prompt content is represented by its exact UTF-8 digest/length. No prompt,
    credential, private HOME or scratch path is copied to ordinary metadata.
    This is adapter-recorded evidence, not independent host observation.
    """
    from . import digest, context_record
    if type(argv) is not list or not argv or any(type(x) is not str for x in argv):
        return None
    prompt = argv[-1].encode("utf-8")
    expected_home = delivery["contract"]["adapter"]["home"] if expected_home is None else expected_home
    return {"selection_digest": digest(delivery), "phase": phase, "evidenced_cli_build": evidenced_build,
            "argv_prefix": argv[:-1], "prompt_digest": "sha256:" + hashlib.sha256(prompt).hexdigest(),
            "prompt_bytes": len(prompt), "argv_digest": digest(argv),
            "environment_policy": delivery["contract"]["adapter"]["environment_policy"],
            "environment_validated": (set(environment) == set(delivery["contract"]["adapter"]["environment_policy"])
                and environment.get("PATH") == delivery["contract"]["adapter"]["environment_policy"]["PATH"]
                and environment.get("HOME") == expected_home
                and ("CODEX_HOME" not in delivery["contract"]["adapter"]["environment_policy"]
                     or environment.get("CODEX_HOME") == expected_home + "/codex")),
            "context_label": context_record(delivery["contract"]["adapter"], phase),
            "status": status}


def configured_record(delivery, *, phase, evidenced_build, raw, partial, raw_digest,
                      log_retained, invocation):
    from . import argv, digest, context_record
    import re
    selected = delivery["contract"]["selection"]
    adapter = delivery["contract"]["adapter"]
    profile = delivery["contract"].get("runtime_profile", {})
    image = profile.get("image_digest")
    sha = lambda value: type(value) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None
    if type(evidenced_build) is not str or not evidenced_build:
        evidenced_build = None
    observed = codex.stream_outcome(raw, partial=partial) if log_retained else "unclassified"
    required = {"argv_prefix", "prompt_digest", "prompt_bytes", "argv_digest", "environment_policy",
                "environment_validated", "context_label", "status", "selection_digest", "phase", "evidenced_cli_build"}
    valid = False
    try:
        valid = (type(invocation) is dict and set(invocation) == required
                 and invocation["selection_digest"] == digest(delivery) and invocation["phase"] == phase
                 and invocation["evidenced_cli_build"] == evidenced_build
                 and invocation["argv_prefix"] == argv(adapter, selected, "")[:-1]
                 and sha(invocation["prompt_digest"]) and sha(invocation["argv_digest"])
                 and type(invocation["prompt_bytes"]) is int and invocation["prompt_bytes"] > 0
                 and invocation["environment_policy"] == adapter["environment_policy"]
                 and invocation["environment_validated"] is True
                 and invocation["context_label"] == context_record(adapter, phase)
                 and type(invocation["status"]) is int and invocation["status"] == 0
                 and sha(image) and delivery["adapter_digest"] == digest(adapter)
                 and delivery["profile_digest"] == digest(profile)
                 and profile["provider"] == "codex" and profile["model"] == selected["requested_model"]
                 and profile["cli_build"] == selected["cli_build"]
                 and adapter["participation_sources"] == [] and phase == "implementation")
    except (ValueError, KeyError, TypeError):
        pass
    if selected["cli_build"] != codex.CLI_BUILD or evidenced_build != codex.CLI_BUILD:
        observed = "unknown"
    outcome = ("rerouted" if observed == "rerouted" else
               "unqualified-build" if selected["cli_build"] != codex.CLI_BUILD else
               "conflicting" if evidenced_build not in (None, codex.CLI_BUILD) else
               "missing" if invocation is None or evidenced_build is None or not sha(image) or observed != "complete" else
               "conflicting" if not valid or evidenced_build != codex.CLI_BUILD else "configured-model-accepted")
    answer = {"schema": CONFIGURED_SCHEMA, "basis": "configured-model", "attempt_id": delivery["attempt_id"],
              "job_id": delivery["home_identity"]["job_id"], "phase": phase, "provider": "codex",
              "selected_cli_build": selected["cli_build"], "evidenced_cli_build": evidenced_build,
              "requested_model": selected["requested_model"], "image_digest": image,
              "selection_digest": digest(delivery), "contributors": [], "contributor_sources": {},
              "actual_participation": "unknown", "invocation": invocation, "outcome": outcome,
              "reroute_observation": "reroute observed" if observed == "rerouted" else
                  "no reroute observed" if observed == "complete" else "reroute observation incomplete",
              "evidence": {"digest": raw_digest if raw_digest is not None else
                  "sha256:" + hashlib.sha256(raw).hexdigest() if type(raw) is bytes else None,
                  "log": {"attempt_id": delivery["attempt_id"], "stream": "provider.stdout"}}}
    if "service_tier" in selected:
        answer["service_tier"] = {"requested": selected["service_tier"], "observed": None, "outcome": "missing"}
    return answer
