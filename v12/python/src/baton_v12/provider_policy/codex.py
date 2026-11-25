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
    if raw.count(b"\n") > 1024:
        return "unclassified"
    observed = TurnObservation()
    observed.feed(raw)
    return observed.finish(True)


def completed_turn(raw, *, partial):
    return stream_outcome(raw, partial=partial) == "complete"

def _activity(event):
    kind = event.get("type")
    if type(kind) is not str or not kind:
        return "unclassified"
    if kind in ("error", "turn.failed"):
        return "faulted"
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
                return "rerouted"
            else:
                return "faulted"
    return "complete"

class TurnObservation:
    """Consume one frame at a time. Memory is bounded independently of turn length."""
    MAX_FRAME = 4 << 20

    def __init__(self):
        self.pending = bytearray()
        self.phase = "thread"
        self.outcome = "complete"

    def feed(self, chunk):
        for index, piece in enumerate(chunk.split(b"\n")):
            if index:
                self._line()
                self.pending.clear()
            if self.phase != "invalid":
                if len(self.pending) + len(piece) > self.MAX_FRAME:
                    self.phase = "invalid"
                else:
                    self.pending.extend(piece)

    def _line(self):
        if self.phase == "invalid":
            return
        try:
            event = json.loads(self.pending.decode("utf-8"), object_pairs_hook=_members,
                               parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            if not isinstance(event, dict):
                raise ValueError()
            if self.phase == "thread":
                if set(event) != {"type", "thread_id"} or event["type"] != "thread.started" or not isinstance(event["thread_id"], str) or not event["thread_id"]:
                    raise ValueError()
                self.phase = "start"
            elif self.phase == "start" and event == {"type": "turn.started"}:
                self.phase = "active"
            elif self.phase != "active":
                raise ValueError()
            elif event.get("type") == "turn.completed":
                usage = event.get("usage")
                if set(event) != {"type", "usage"} or not isinstance(usage, dict) or set(usage) != {"input_tokens","cached_input_tokens","cache_write_input_tokens","output_tokens","reasoning_output_tokens"} or any(type(n) is not int or n < 0 for n in usage.values()):
                    raise ValueError()
                self.phase = "ended"
            else:
                outcome = _activity(event)
                if outcome == "unclassified":
                    raise ValueError()
                if outcome == "rerouted" or (self.outcome == "complete" and outcome == "faulted"):
                    self.outcome = outcome
        except (ValueError, TypeError, RecursionError):
            self.phase = "invalid"

    def finish(self, eof):
        return self.outcome if eof and self.phase == "ended" and not self.pending else "unclassified"
