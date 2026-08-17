# Finding: claim duration needs an unambiguous `Held` display

## Observed — 2026-08-17

The Work table labels the current claim timer `Age` and changes the meaning of
the same five-character shape at one hour: below an hour it is `MM:SS`, then it
becomes `HH:MM`. A human cannot distinguish those units from a value such as
`01:30`. `Age` is also imprecise: the value measures how long the current
claimant has held the Work, not how old the Work is.

## Confirmed ruling — 2026-08-17

**Confirmed by Slawomir.** Rename the column `Held` and use a single
hours/minutes interpretation for every ordinary value:

- derive elapsed seconds from canonical `claimed_at` and the local clock as
  today, clamping negative elapsed time to zero;
- floor elapsed time to complete minutes;
- render `00:00` through `99:59` as `HH:MM`;
- render `99h+` above that fixed-width range rather than lying by saturation;
- render `-` for unclaimed Work.

The existing heartbeat alert remains a suffix to the timer (`!` when stale)
and never resets the Held duration. Scheduled refresh, claim/pass/release/close
semantics, JSON `claimed_at`, the authority schema and responsive omission of
the whole column do not change.

This is a follow-up to closed W33. W33 is not reopened, and its historical
decision/reviews remain intact; the supersession is also recorded in
`../finding-tui-claim-age/FINDING.md`.

## Acceptance boundary

- Pure formatter boundaries prove `00:00` before 60 seconds, `00:01` at 60
  seconds, `01:00` at one hour, `99:59` at the upper ordinary bound, `99h+`
  above it, `-` while unclaimed, and the negative-clock clamp.
- Wide Work tables use the exact `Held` header; narrow tables still omit the
  entire field without stealing the minimum Title budget.
- Heartbeat suffix, automatic refresh and packaged TUI coverage compose with
  the new label and scale without extra authority reads or a second timer.
- Canonical JSON remains a timestamp/null fact rather than a changing duration.

## Supersession — 2026-08-17: handoff-held duration and pickup state

**Confirmed by Slawomir.** This supersedes the earlier requirement above that
`Held` derives from `claimed_at` and renders `-` for every unclaimed Work.
Responsibility begins when the baton is passed to the destination endpoint,
not only when one of that endpoint's members later claims execution.

- `Held` starts at the committed handoff and does not reset when the recipient
  claims. A later pass starts a new destination-held interval.
- An unclaimed operational handoff prefixes the compact Phase cell with `>`.
- After the approved six-minute pickup/liveness threshold without a claim,
  `!` replaces `>` to flag overdue pickup.
- Claiming removes the pickup prefix while the same `Held` counter continues.
- No automatic claim, release, transfer, reassignment, or phase transition is
  inferred from either prefix or elapsed time.

The glyphs are TUI presentation only. Canonical JSON must expose structured
handoff/claim state and the recorded instant needed to derive the duration and
overdue condition. It must never encode pickup state in `>`/`!` strings or
require agents to scrape display text. Heartbeat staleness remains a separate
structured fact for an actual claimant; it does not reset `Held`.

This makes an atomic pass followed by a crashed or absent recipient visible as
pending pickup rather than leaving apparently active Work in silent limbo.
