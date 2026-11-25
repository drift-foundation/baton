"""Exact-build Codex stdout interpretation shared by worker and host.

Only Codex 0.169.0 is qualified for this observation surface. Reroute negatives
are source-defined error items, not a claim that a live reroute was captured.
"""
import json
import re

CLI_BUILD = "0.169.0"
MAX_OUTPUT = 1 << 16

def _members(pairs):
    value = {}
    for key, member in pairs:
        if key in value:
            raise ValueError("duplicate JSON member")
        value[key] = member
    return value


def stream_outcome(raw, *, partial=False):
    """Recognize a bounded framed invocation, never substantive task success.

    Ordinary activity payloads are opaque; they need no success catalogue or
    matching item lifecycle. Structural framing, explicit faults and the
    supported reroute signal remain meaningful. A tool's exit/status is activity
    evidence for review, not the invocation's or candidate's verdict.
    """
    if partial is not False or type(raw) is not bytes or not raw or len(raw) > MAX_OUTPUT:
        return "unclassified"
    try:
        lines = raw.decode("utf-8").split("\n")[:-1]
        if len(lines) < 3 or len(lines) > 1024 or not raw.endswith(b"\n"):
            return "unclassified"
        events = [json.loads(line, object_pairs_hook=_members,
                            parse_constant=lambda value: (_ for _ in ()).throw(ValueError())) for line in lines]
        if any(type(event) is not dict for event in events):
            return "unclassified"
        first, start, *middle, end = events
        if (set(first) != {"type", "thread_id"} or first["type"] != "thread.started"
                or type(first["thread_id"]) is not str or not first["thread_id"]
                or start != {"type": "turn.started"}
                or set(end) != {"type", "usage"} or end["type"] != "turn.completed"):
            return "unclassified"
        usage = end["usage"]
        if (type(usage) is not dict or set(usage) != {"input_tokens", "cached_input_tokens",
                "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens"}
                or any(type(n) is not int or n < 0 for n in usage.values())):
            return "unclassified"
        rerouted = False
        faulted = False
        for event in middle:
            kind = event.get("type")
            if type(kind) is not str or not kind:
                return "unclassified"
            if kind in ("error", "turn.failed"):
                faulted = True
            elif kind.startswith(("thread.", "turn.")):
                # A second/misordered/unknown lifecycle boundary is not activity.
                return "unclassified"
            if kind.startswith("item."):
                item = event.get("item")
                if (type(item) is not dict or type(item.get("id")) is not str
                        or not item["id"] or type(item.get("type")) is not str
                        or not item["type"]):
                    return "unclassified"
                if item["type"] == "error":
                    message = item.get("message")
                    if type(message) is not str:
                        return "unclassified"
                    if re.fullmatch(r"model rerouted: .+ -> .+ \(HighRiskCyberActivity\)", message):
                        rerouted = True
                    else:
                        faulted = True
        return "rerouted" if rerouted else "faulted" if faulted else "complete"
    except (ValueError, UnicodeError, RecursionError, KeyError, TypeError):
        return "unclassified"


def completed_turn(raw, *, partial):
    return stream_outcome(raw, partial=partial) == "complete"
