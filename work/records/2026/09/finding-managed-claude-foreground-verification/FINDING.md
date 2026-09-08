# Managed Claude verification must remain in the foreground

2026-09-08 — baton.prompt. Work W114716.

## Observed

Incidents 35–40 follow K returning status responses while test gates or handoffs
remain outstanding. The Baton ACP bridge then destroys the delivered turn's
process domain and records the surviving claim. Exact earlier log locations and
source analysis are retained in the parent record's
RUNNER-DIAGNOSIS-2026-09-08.md. The installed Claude ACP adapter explicitly defers
settlement for background subagents but not background shell tasks; its normal
interactive lifecycle therefore differs from Baton's one-domain-per-delivery
contract. A model crash or timeout is not established by these incidents.

## Confirmed operational decision

Slawomir authorized CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1 in the managed
baton.claude environment, a restart, and returning the two affected product jobs
to Claude as implementer. This supersedes the temporary tuner allocation for
W110935 and W114085. Existing correction scopes and independent Codex review
remain unchanged. Dispatch stays paused during configuration and restart.

Anthropic documents that this setting disables explicit background execution,
automatic backgrounding and background subagents:
https://code.claude.com/docs/en/env-vars
The installed claude-agent-sdk contains the setting. The deployment template
does not currently set it. AgentSession overlays configured agent.env on the
child environment, and the inspected launcher does not clear that environment.
This supported setting is the selected first correction; a bridge continuation
redesign is deferred pending evidence that foreground execution is insufficient.

## Scope and acceptance

Change only agent.env.CLAUDE_CODE_DISABLE_BACKGROUND_TASKS to the string "1" in
/home/sl/baton-v11.14aecfb/acp-claude.template.json. The deployment renderer must
carry it into the next managed Claude context. Preserve adapter version, session
selection, deadline, permissions and existing process cleanup. Do not change the
other ACP participant or recover/dismiss incidents implicitly.

Validate exact JSON delta and next rendered configuration. After restart,
verify service health and, when an agent process starts, the effective flag.
The operational behavioral proof is one foreground test run whose result is
collected before handoff; no whole-suite run solely to validate this setting.
Do not claim the recurring failure fixed until that proof is observed.

## Operational limitation

The repository lifecycle CLI supports the complete service set, with no selected
service restart operand. That set includes the Codex backend hosting this
interactive context. A full stop issued from here can terminate the executor
before it starts or verifies the replacement. Prefer the operator's external
terminal for the stop/start pair; do not improvise a detached or untracked worker
or bypass lifecycle ownership to restart one process. This limitation is recorded
before any workaround; no selective restart is claimed to have been performed.

## 2026-09-08 post-restart outcome and closure decision

The earlier observation that the template lacked the setting is superseded by
the operator's application and verified restart: both template and generated
context contain string "1"; the replacement bridge was healthy. After operator
resume, Claude claimed W110935 at114798, reported a collected focused test result
of 371 tests in 29.088 seconds, OK, and returned it to review at114825. The ledger
confirms a 247-second claim ending with that return, followed by codex claim114828.
evidence/foreground-work-events.json retains the canonical read. The author's
PROGRESS and handoff label the episode114742 as the claim;114798 is the actual
claim event. This correction avoids reproducing that label as canonical identity.

This is the selected operational proof: a completed result and explicit handoff
after restart, replacing the earlier repeated held endings. Test execution is
the implementer's reported evidence; the handoff and released claim are directly
confirmed by the ledger. This is not a proof of permanent non-recurrence or a
claim of product review sign-off. No new test run was commissioned for this proof.
Slawomir approved recording this evidence and closing the setting job. Further
adapter changes remain deferred unless the same failure recurs. baton.prompt
prepares the close rationale; the operator owns the baton.ops terminal operation.
