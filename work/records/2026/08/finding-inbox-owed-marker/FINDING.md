# Finding: show one owed-action marker on the Inbox tab

## Status

Confirmed by Slawomir on 2026-08-19 and ready for implementation.

## Observed

The top-level Inbox tab currently displays `total/unseen`. Although those are
separate projection fields, most live Inbox row kinds are unseen for their
entire lifetime or disappear when seen/resolved. The header therefore usually
shows `0/0` or `1/1`, consumes space, and emphasizes unreadness even though the
operator's important question is whether they owe an action.

The exact counts remain useful inside Inbox, where their meaning and rows are
visible. They are noise in the global tab label.

## Confirmed decision — 2026-08-19

- The top-level tab is `[Inbox]` when the current participant owes no action.
- It is `[Inbox *]` when one or more unresolved actions are owed.
- `*` is a single ASCII marker. It does not encode a count, severity, unseen
  state, or error.
- The marker derives from canonical `owed_action`, not from `total`, `unseen`,
  bold state, or TUI-local state.
- Active-tab highlighting remains independent: highlighting says which tab is
  selected; `*` says the participant owes action.
- Unseen attention-only content does not add the marker.
- Owed, unseen, and total counts remain available inside the Inbox view and in
  the CLI/JSON projection.

This supersedes only the `total/unseen` text in the top-level Inbox label from
`work/records/2026/08/finding-tui-jobs-teams-inbox/`. It retains that record's
Inbox rows, canonical counters, owed-action semantics, and active-tab model as
subsequently superseded by
`work/records/2026/08/finding-consistent-tui-tab-grammar/`.

## Acceptance boundary

- The tab bar renders exactly `[Inbox]` or `[Inbox *]`; no numeric Inbox counts
  appear there.
- Seen-but-unresolved owed action keeps `*`; unseen attention with nothing owed
  does not show it.
- Resolving the last owed action removes `*` on the next canonical refresh.
- Active/inactive highlighting, narrow whole-tab rendering, `[`/`]` tab
  navigation, Inbox contents, and JSON counters remain unchanged.
- Focused virtual-screen and real-terminal regressions cover zero, one, many,
  seen-but-owed, unseen-attention-only, resolution, narrow width, and refresh.
- Operator documentation and footer/header examples use the same marker.
