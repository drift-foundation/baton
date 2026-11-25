"""Codex 0.169.0 adapter; native composition remains gated.

Arguments/version are grounded in retained N3 inventory. Instruction and home
preparation use the shared D interface. There is no Codex policy realization
or credential filename until qualified integration supplies one. Terminal
success is grounded in a retained turn; actual contributors remain unknown.
"""
import json
import re

from claude_agent import ClaudeAgent, TaskRefusal, UNCLASSIFIED, MAX_PROVIDER_RECORD

CLI_BUILD = "0.169.0"
EXEC_COMMANDS = frozenset(("resume", "fork", "review", "help"))
ARGUMENTS = ("exec", "--dangerously-bypass-approvals-and-sandbox",
             "--ignore-user-config", "--ignore-rules", "--json")
SELECTED = object()


from provider_policy.codex import completed_turn, stream_outcome


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
                "why": "Codex reported a model reroute" if stream_outcome(record, partial=partial) == "rerouted" else
                    "Codex did not supply a complete supported successful turn"}

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
