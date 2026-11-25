"""Disjoint N4a draft for Codex 0.169.0, not a qualified provider.

Arguments come from the retained exact-build N3 exec help. Terminal parsing
and participation sources belong to N4b. The shared policy realization,
version decoder, credential slot and instruction delivery join after D;
until then composition and home preparation refuse rather than borrowing
Claude's credential or claiming a successful Codex turn.
"""
from claude_agent import ClaudeAgent, TaskRefusal, UNCLASSIFIED

CLI_BUILD = "0.169.0"
EXEC_COMMANDS = frozenset(("resume", "fork", "review", "help"))
ARGUMENTS = ("exec", "--dangerously-bypass-approvals-and-sandbox",
             "--ignore-user-config", "--ignore-rules", "--json")


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
        # The joined realization owns the role list. Missing D delivery is a
        # refusal, not a private default that could diverge from composition.
        roles = selected["contract"]["adapter"].get("context_label", {}).get("roles")
        if roles != ["implementation"] or seen.get("role") not in roles:
            raise TaskRefusal("Codex requires the implementation-only context label")
        if selected["contract"]["selection"]["cli_build"] != CLI_BUILD:
            raise TaskRefusal("Codex requires its selected exact CLI build")
        return selected

    def provider_argv(self, prompt, *, model=None):
        prompt = prompt_operand(prompt)
        if model is None:
            # The shared runner first asks for argv without its model
            # argument. Resolve the same validated selection, never a default.
            model = self._provider_selection()["contract"]["selection"]["requested_model"]
        if (type(model) is not str or not model or len(model) > 256
                or model.startswith("-") or any(ord(char) < 32 for char in model)):
            raise TaskRefusal("Codex requires an explicit bounded model selector")
        return [self.provider_program, *self.provider_arguments, "--model", model, prompt]

    def invoke_provider(self, *, prompt, room, seen=None):
        # R1 applies before even preparing a home, not just at argv creation.
        prompt_operand(prompt)
        return super().invoke_provider(prompt=prompt, room=room, seen=seen)

    def provider_terminal(self, status, record, *, partial):
        # No raw bytes, exit-zero convention or Claude-shaped fixture can
        # establish Codex success before exact-build turn evidence exists.
        return {"ok": False, "status": status, "failure_reason": UNCLASSIFIED,
                "why": "Codex terminal interpretation awaits exact-build turn evidence"}

    def _prepared_home(self, scratch):
        # J1 and the D-first slot hook are unresolved. In particular, never
        # delegate to the current shared implementation's Claude slot.
        raise TaskRefusal("Codex credential-path selection and home integration are pending")

    def provider_session_root(self, home):
        raise TaskRefusal("Codex session layout is not evidenced")
