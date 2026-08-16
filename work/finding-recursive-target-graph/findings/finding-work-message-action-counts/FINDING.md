# Finding: the v11 Work list hides total messages and pending requests

## Observed

The second v11 trial list exposes personal `New` but does not show how much
conversation exists under each Work or whether the viewer currently owes a
directed response. An operator must drill into Work and Threads merely to learn
whether an item has substantial discussion or a pending `@` obligation.

## Confirmed decision — 2026-08-15

**Confirmed by Slawomir during the second v11 trial.** The Work list includes a
compact `Msg/My` column, for example:

```text
Msg/My
41/1
```

`Msg` is the total distinct message count in the same visible Work scope used
for its conversation projection. Where a row summarizes descendants, the count
is recursive and overlap-safe: one Message reachable through multiple labelled
paths is counted once for that row. It is a conversation-volume count, not an
unread count, and does not decrease when messages are seen or answered.

`My` is the number of unresolved directed `@` obligations in that scope for
which the current participant is an eligible handler. It does not count unseen
status messages, `+` inclusions, another member's obligations, Current/Next
ownership, or ordinary messages that request no response. When any authorized
handler resolves a shared route obligation, it ceases to be pending for every
eligible handler. Withdrawal on terminal closure likewise removes it from
`My`.

An answer may therefore increase `Msg` while decreasing `My`. `New` remains a
separate personal seen-cursor count; `Msg/My` does not replace or reinterpret
it. Canonical JSON exposes unambiguous full fields such as `message_count` and
`my_pending_obligations`; the TUI alone combines them compactly.

Both values are pure projections over existing Messages, Thread labels,
descendant relationships, obligations, and seen-independent state. Reading the
list performs no seen or workflow mutation. This is queued for the next
immutable revision and does not rewrite the current trial.
