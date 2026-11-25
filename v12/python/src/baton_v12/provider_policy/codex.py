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
    """Recognize only the evidenced fresh-turn family, within the shared bound.

    This is a CLI terminal outcome, never candidate acceptance or attribution.
    Unknown events and failure shapes remain unclassified. Text is opaque;
    nested tool output cannot supply a terminal or a contributor.
    """
    if partial is not False or type(raw) is not bytes or not raw or len(raw) > MAX_OUTPUT:
        return "unclassified"
    try:
        lines = raw.decode("utf-8").split("\n")[:-1]
        if len(lines) < 4 or len(lines) > 1024 or not raw.endswith(b"\n"):
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
        pending, finished = {}, set()
        rerouted = False
        last_message = False
        for event in middle:
            if set(event) != {"type", "item"} or event["type"] not in ("item.started", "item.completed"):
                return "unclassified"
            item = event["item"]
            if type(item) is not dict or type(item.get("id")) is not str or not item["id"]:
                return "unclassified"
            ident = item["id"]
            if ident in finished:
                return "unclassified"
            last_message = item.get("type") == "agent_message"
            if last_message:
                if (set(item) != {"id", "type", "text"} or type(item["text"]) is not str
                        or event["type"] != "item.completed" or ident in pending):
                    return "unclassified"
                finished.add(ident)
            elif item.get("type") == "error":
                if (set(item) != {"id", "type", "message"} or event["type"] != "item.completed"
                        or ident in pending or type(item["message"]) is not str
                        or re.fullmatch(r"model rerouted: .+ -> .+ \(HighRiskCyberActivity\)", item["message"]) is None):
                    return "unclassified"
                rerouted = True
                finished.add(ident)
            elif item.get("type") == "command_execution":
                if (set(item) != {"id", "type", "command", "aggregated_output", "exit_code", "status"}
                        or type(item["command"]) is not str or type(item["aggregated_output"]) is not str):
                    return "unclassified"
                if event["type"] == "item.started":
                    if ident in pending or item["status"] != "in_progress" or item["exit_code"] is not None:
                        return "unclassified"
                    pending[ident] = item["command"]
                else:
                    if (ident not in pending or pending[ident] != item["command"]
                            or item["status"] != "completed" or type(item["exit_code"]) is not int
                            or item["exit_code"] != 0):
                        return "unclassified"
                    del pending[ident]
                    finished.add(ident)
            else:
                return "unclassified"
        return ("rerouted" if rerouted else "complete") if finished and last_message and not pending else "unclassified"
    except (ValueError, UnicodeError, RecursionError, KeyError, TypeError):
        return "unclassified"


def completed_turn(raw, *, partial):
    return stream_outcome(raw, partial=partial) == "complete"
