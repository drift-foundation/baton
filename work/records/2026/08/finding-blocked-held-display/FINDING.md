# Finding: blocked Work must not advance `Held`

## Observed — 2026-08-18

In the projection-11 live TUI, W2 is in phase `block`, has no Handler, and
waits on W3, yet its `Held` value advances. The row therefore looks as though
a recipient is working or late even though no participant can progress it.

## Confirmed UX rule

`Held` is the Handler-duration column. It advances only while a participant
holds the Work claim, starting at `claimed_at`. Queued, blocked, parked, and
terminal Work render `-` because none has a current Handler.

Blocked duration remains canonical operational evidence: the gate has its
typed identity and episode start, `Wait` names it, and Events may show how long
the block lasted. It does not belong in `Held`.

This explicitly supersedes the blocked-Held portion of the earlier ruling in
`work/records/2026/08/finding-recursive-target-graph/findings/finding-tui-held-duration/findings/finding-unclaimed-work-cue/FINDING.md`.

## Acceptance

- Every open row with `handler=null` renders `Held=-`, including `block` with
  either Work or Message gates.
- Claimed active Work continues to use `claimed_at` and the capped MM:SS
  presentation.
- Gate identity/start and Events duration remain available and unchanged.
- JSON/TUI parity tests distinguish gate duration from Handler duration.
