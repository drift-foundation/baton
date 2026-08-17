# Finding: pass is a Work event, not a discussion message

## Parent

`finding-v11-messaging-cutover-gate` — discovered while returning live Codex
readiness Work `W148` from `baton.ops` to `baton.bug`.

## Observed

The v11 `pass` operation requires `thread=` because its handoff comment is
currently appended as a discussion message. In the TUI, W148 and its visible
local Work selector were sufficient to identify the workflow mutation, but the
required authority-wide thread identifier was not exposed. The plausible
`thread=T148` input was refused; only the undiscoverable full identifier
`7ba67cb8-T148` worked.

This is not merely a missing display label. Requiring any discussion thread
for a Work-level baton transfer couples two independent concepts and forces a
human to select a message destination that has no bearing on who owns the Work
next.

## Decision — 2026-08-16

**Superseded in part 2026-08-17 by
`finding-route-derived-handoff-phase`:** `pass` remains a threadless Work
transition with durable `comment=` evidence, but `phase=` is no longer caller
input. The destination route derives it atomically; the example and wording
below are retained as historical decision evidence.

`pass` is an authoritative Work transition and must not require or accept a
discussion thread.

The ordinary operation is:

```text
pass work=W148 to=baton.bug phase=review comment="Compact wake verified."
```

- `work=` remains mandatory. TUI selection must never silently choose the
  mutation target because refresh or cursor movement could redirect a pasted
  command.
- `comment=` is durable handoff evidence stored with the authoritative pass
  event alongside actor, destination, destination phase, sequence and time.
- Passing releases the current claim, changes Current and phase, and wakes the
  destination through Work readiness. None of that depends on a Thread.
- A pass does not create a Message, advance a Thread cursor, or alter Message,
  My, New, or obligation counts.
- Conversation remains explicit and separate: use `say` when a discussion
  message is wanted.
- Remove `thread=` from the public pass grammar rather than retaining it as an
  optional or advanced selector. There is no thread-selection decision in a
  Work transfer.

This ruling supersedes the earlier pass shape described as “handoff evidence
appended to the thread.” The evidence remains durable, but its owner is the
Work event journal.

## Acceptance

- CLI and TUI command mode accept the mandatory `work=`, `to=` and `comment=`
  pass shape without `thread=`; destination phase and planned return endpoint
  remain supported.
- `thread=` is rejected as an unknown pass operand so old coupling cannot
  silently survive.
- The pass event projects the exact comment and complete transition metadata.
- Atomic claim release, Current/phase transfer, retry replay, stale/unauthorized
  refusal and destination readiness retain their existing guarantees.
- Passing leaves all discussion-message and personal cursor/count projections
  unchanged.
- Workflow tests cover a normal implementation-to-review handoff, an
  approval-to-review return, and a pass on Work containing several Threads.
