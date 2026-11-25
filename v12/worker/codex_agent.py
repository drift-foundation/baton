"""Codex 0.169.0 adapter; native composition remains gated.

Arguments/version are grounded in retained N3 inventory. Instruction and home
preparation use the shared D interface. There is no Codex policy realization
or credential filename until qualified integration supplies one. Terminal
success is grounded in a retained turn; contributor evidence remains missing.
"""
import json
import re

from claude_agent import ClaudeAgent, TaskRefusal, UNCLASSIFIED, MAX_PROVIDER_RECORD

CLI_BUILD = "0.169.0"
EXEC_COMMANDS = frozenset(("resume", "fork", "review", "help"))
ARGUMENTS = ("exec", "--dangerously-bypass-approvals-and-sandbox",
             "--ignore-user-config", "--ignore-rules", "--json")
SELECTED = object()


def _members(pairs):
    value = {}
    for key, member in pairs:
        if key in value:
            raise ValueError("duplicate JSON member")
        value[key] = member
    return value


def completed_turn(raw, *, partial):
    """Recognize only the evidenced fresh-turn family, within the shared bound.

    This is a CLI terminal outcome, never candidate acceptance or attribution.
    Unknown events and failure shapes remain unclassified. Text is opaque;
    nested tool output cannot supply a terminal or a contributor.
    """
    if partial is not False or type(raw) is not bytes or not raw or len(raw) > MAX_PROVIDER_RECORD:
        return False
    try:
        lines = raw.decode("utf-8").splitlines()
        if len(lines) < 4 or len(lines) > 1024 or not raw.endswith(b"\n"):
            return False
        events = [json.loads(line, object_pairs_hook=_members,
                            parse_constant=lambda value: (_ for _ in ()).throw(ValueError())) for line in lines]
        if any(type(event) is not dict for event in events):
            return False
        first, start, *middle, end = events
        if (set(first) != {"type", "thread_id"} or first["type"] != "thread.started"
                or type(first["thread_id"]) is not str or not first["thread_id"]
                or start != {"type": "turn.started"}
                or set(end) != {"type", "usage"} or end["type"] != "turn.completed"):
            return False
        usage = end["usage"]
        if (type(usage) is not dict or set(usage) != {"input_tokens", "cached_input_tokens",
                "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens"}
                or any(type(n) is not int or n < 0 for n in usage.values())):
            return False
        pending, finished = {}, set()
        last_message = False
        for event in middle:
            if set(event) != {"type", "item"} or event["type"] not in ("item.started", "item.completed"):
                return False
            item = event["item"]
            if type(item) is not dict or type(item.get("id")) is not str or not item["id"]:
                return False
            ident = item["id"]
            if ident in finished:
                return False
            last_message = item.get("type") == "agent_message"
            if last_message:
                if (set(item) != {"id", "type", "text"} or type(item["text"]) is not str
                        or event["type"] != "item.completed" or ident in pending):
                    return False
                finished.add(ident)
            elif item.get("type") == "command_execution":
                if (set(item) != {"id", "type", "command", "aggregated_output", "exit_code", "status"}
                        or type(item["command"]) is not str or type(item["aggregated_output"]) is not str):
                    return False
                if event["type"] == "item.started":
                    if ident in pending or item["status"] != "in_progress" or item["exit_code"] is not None:
                        return False
                    pending[ident] = item["command"]
                else:
                    if (ident not in pending or pending[ident] != item["command"]
                            or item["status"] != "completed" or type(item["exit_code"]) is not int
                            or item["exit_code"] != 0):
                        return False
                    del pending[ident]
                    finished.add(ident)
            else:
                return False
        return bool(finished) and last_message and not pending
    except (ValueError, UnicodeError, RecursionError, KeyError, TypeError):
        return False


def prompt_operand(prompt):
    """Refuse an operand the evidenced exec CLI could treat as a command."""
    if (type(prompt) is not str or not prompt.strip() or prompt.startswith("-")
            or prompt in EXEC_COMMANDS or "\0" in prompt):
        raise TaskRefusal("Codex requires a nonempty prompt operand, not an option or subcommand")
    return prompt


class CodexAgent(ClaudeAgent):
    provider_program = "codex"
    provider_arguments = ARGUMENTS
    # No filename is inferred from another build or from the host account.
    provider_home_state = None
    provider_credential = None

    def _provider_selection(self):
        seen = getattr(self, "_seen", None) or {}
        if (seen.get("schema") != "baton.worker-launch/6"
                or seen.get("provider_context") is not None):
            raise TaskRefusal("Codex requires a fresh provider-selected launch")
        selected = super()._provider_selection()
        # Host and worker consume the same bound context-label role list.
        import provider_policy
        try:
            provider_policy.validate_execution(selected["contract"]["adapter"], seen.get("role"), seen.get("provider_context"))
        except (ValueError, KeyError, TypeError) as failure:
            raise TaskRefusal("Codex requires its declared fresh execution role") from failure
        if selected["contract"]["selection"]["cli_build"] != CLI_BUILD:
            raise TaskRefusal("Codex requires its selected exact CLI build")
        return selected

    def provider_argv(self, prompt, *, model=None, service_tier=SELECTED):
        prompt = prompt_operand(prompt)
        # A worker that has seen its launch takes the tier from the validated
        # selection and nowhere else. A detached caller (the qualification
        # launcher) names it explicitly; None there means no tier.
        launched = model is None or getattr(self, "_seen", None) is not None
        if service_tier is not SELECTED and launched:
            raise TaskRefusal("Codex takes its service tier from the selection, not from an operand")
        if launched:
            # The shared runner first asks for argv without its model
            # argument. Resolve the same validated selection, never a default.
            chosen = self._provider_selection()["contract"]["selection"]
            model = chosen["requested_model"] if model is None else model
            service_tier = chosen.get("service_tier")
        elif service_tier is SELECTED:
            service_tier = None
        if (type(model) is not str or not model or len(model) > 256
                or model.startswith("-") or any(ord(char) < 32 for char in model)):
            raise TaskRefusal("Codex requires an explicit bounded model selector")
        import provider_policy
        try:
            extra = provider_policy.service_tier_arguments(self.provider_program, CLI_BUILD, service_tier)
        except ValueError as failure:
            raise TaskRefusal("Codex has no realization for the selected service tier") from failure
        return [self.provider_program, *self.provider_arguments, "--model", model, *extra, prompt]

    def invoke_provider(self, *, prompt, room, seen=None):
        # R1 applies before even preparing a home, not just at argv creation.
        prompt_operand(prompt)
        return super().invoke_provider(prompt=prompt, room=room, seen=seen)

    def provider_terminal(self, status, record, *, partial):
        if type(status) is int and status == 0 and completed_turn(record, partial=partial):
            return {"ok": True, "status": 0, "failure_reason": None, "why": None}
        return {"ok": False, "status": status, "failure_reason": UNCLASSIFIED,
                "why": "Codex did not supply a complete supported successful turn"}

    def decode_provider_version(self, raw):
        try:
            match = re.fullmatch(r"codex-cli ([0-9]+\.[0-9]+\.[0-9]+)\n?", raw.decode("utf-8"))
            return match.group(1) if match else None
        except UnicodeError:
            return None

    def provider_version(self, environment, candidate):
        build = super().provider_version(environment, candidate)
        if build != CLI_BUILD:
            raise TaskRefusal("Codex version probe did not establish the selected exact build")
        return build

    def provider_session_root(self, home):
        raise TaskRefusal("Codex session layout is not evidenced")
