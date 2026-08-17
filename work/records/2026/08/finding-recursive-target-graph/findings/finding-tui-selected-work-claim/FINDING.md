# Finding — claim the selected Work directly from the TUI

## 2026-08-16 — observed gap

The Work table lets a human select an actionable row, but claiming still
requires opening the command bar and retyping the Work selector:

```text
:claim work=W163
```

That duplicates context the TUI already has, creates an avoidable transcription
opportunity, and obscures the normal transition from ready Work to one active
claimant.

## 2026-08-16 — confirmed ruling

In normal Work-table navigation, lowercase `c` claims the selected Work. The
shortcut invokes the same canonical atomic `claim` operation as the JSON/CLI
surface; it is not a second mutation contract and it does not optimistically
change local state.

The authority remains final. Blocked Work, ineligible viewers, terminal Work,
and competing claims fail closed and the TUI displays the returned diagnostic.
A successful claim schedules the ordinary on-demand refresh while preserving
the selected row. The shortcut does not weaken route resolution, claim
exclusivity, or the active-work policy.

This is a TUI usability correction only. The public `claim work=...` operation
and its protocol semantics do not change.
