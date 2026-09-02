# Finding: Codex tool-host IPC field skew hides committed Baton operations

## Status

Confirmed 2026-09-01. External managed-runtime defect; no repository workaround
is accepted as a fix.

## Observed

The fresh `baton.merge` managed turn for W61984 issued the required standalone
canonical `claim`. The underlying Baton operation committed as assignment
episode 65421, but the Codex tool boundary returned:

```text
failed to decode code-mode IPC frame: unknown field
`code_mode_host_duration_ns`
```

The same decoder failure then prevented a read-only `detail`. The integrator
treated the mutation outcome as unknown, changed no files, and ended the turn.
The authority therefore retained an active claim while the runtime returned to
idle. The interactive `baton.prompt` context reproduced the same tool-host
decoder failure on otherwise ordinary local command execution.

## Confirmed boundary

This is not a Baton routing, readiness, CLI, execution-policy, or proposal
integration failure. Readiness forwarded the action, the dispatcher started a
turn, and the canonical claim committed. The failure lies between the Codex
tool host and its response decoder: a newly emitted timing field is rejected by
the receiving schema after the command has already run.

That failure mode is safety-relevant because a mutating operation can commit
while the model is told only that its outcome is unknown. Retrying blindly
would violate exact-operation discipline. A managed turn must stop, preserve
the claim and evidence, and require operator reconciliation against canonical
Baton state.

## Required correction

The Codex tool-host response decoder must tolerate the emitted
`code_mode_host_duration_ns` field, preferably through compatible additive
field handling. Acceptance requires a managed standalone Baton mutation and a
following read to return normally through the same tool boundary, with no
unknown outcome and no orphaned claim.

Until corrected, the only bounded recovery is operator reconciliation through
the canonical CLI outside the failing Codex tool boundary, followed by an
exact episode-qualified release when the repository diff proves that no Work
output was produced. Restarting or redelivering does not constitute the fix.

## Resolution — verified 2026-09-01

The managed stack had launched Codex CLI 0.151.0 even though 0.152.1 was
installed. After a drained restart, the dispatcher reported 0.152.1 and minted
fresh contexts. A direct bounded turn in the fresh `baton.merge` context
committed discussion message M66087 on W66012, received the mutation response
normally, then read W66012 at snapshot 66088 and received that response
normally. No unknown outcome, claim, workflow transition, or file edit was
left behind.

This satisfies the correction boundary above. W61984 remains separately gated
until W66012 closes; it may then be routed back to `baton.merge` for a fresh
assignment episode.
