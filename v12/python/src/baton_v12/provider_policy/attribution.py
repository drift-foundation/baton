"""Content-free attribution derived only from declared participation sources."""
import hashlib
import json
from . import PolicyRefusal, _text

SCHEMA = "baton.model-attribution/1"
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
           raw_digest=None, log_retained=True):
    selected = delivery["contract"]["selection"]
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
    return {"schema": SCHEMA, "attempt_id": delivery["attempt_id"],
            "job_id": delivery["home_identity"]["job_id"], "phase": phase,
            "provider": selected["provider"], "selected_cli_build": selected["cli_build"],
            "evidenced_cli_build": evidenced_build, "requested_model": selected["requested_model"],
            "mapped_identity": selected["reported_identity"], "contributors": list(reported),
            "contributor_sources": reported, "outcome": outcome,
            "evidence": {"digest": raw_digest if raw_digest is not None else
                         ("sha256:" + hashlib.sha256(raw).hexdigest() if type(raw) is bytes else None),
                         "log": {"attempt_id": delivery["attempt_id"], "stream": "provider.stdout"}}}


def validate(value, delivery, *, phase, raw):
    if type(value) is not dict or value.get("schema") != SCHEMA:
        raise PolicyRefusal("model-attribution-missing")
    expected = record(delivery, phase=phase, evidenced_build=value.get("evidenced_cli_build"), raw=raw,
                      partial=raw is None, log_retained=raw is not None)
    if value != expected:
        raise PolicyRefusal("model-attribution-invalid")
    return expected


def diagnostic(value):
    if value is None:
        return "Requested: not selected (account default)"
    reported = value.get("contributors", [])
    present = value.get("mapped_identity") in reported
    return ("Requested: " + value["requested_model"] + "; mapped identity: " + value["mapped_identity"]
            + "; Reported contributors: " + (", ".join(reported) or "no evidence")
            + "; Requested model reported: " + ("yes" if present else "no" if reported else "no evidence")
            + "; CLI build selected: " + value["selected_cli_build"]
            + "; CLI build evidenced: " + (value.get("evidenced_cli_build") or "no evidence")
            + "; attribution: " + value["outcome"])
