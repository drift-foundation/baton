# Finding: derive handoff phase from the destination route

## Observation — 2026-08-17

W49 was passed to `baton.impl` with `phase=queued`. Claude atomically claimed
it and began editing and testing, while the canonical Work projected both
`active=baton.claude` and `phase=queued`. The TUI therefore showed no active
implementation phase even though the ACP process was executing W49.

The claim itself remained exclusive, so no second participant could win the
same Work. The operational view was nevertheless false and would cause noisy
acquisition attempts and bad scheduling decisions as more agents share a
route.

## Confirmed decision

The destination route, not the caller, determines phase during a handoff.
`pass` removes `phase=` and derives the canonical stage from the resolved
route role atomically with Current. Implementation maps to `active`, research
to `research`, and reviewer/approver to `review`; an unmapped destination
refuses. Explicit phase mutation remains for an authorized same-route stage
change only. A route transfer never produces `queued`.

This is authority enforcement, not merely documentation. It makes the false
state that occurred on W49 unrepresentable through the public handoff.

## Acceptance boundary

- Handoffs to every stage role derive the expected phase without caller input.
- `phase=` on `pass` is an unknown/refused operand and changes no byte.
- An unmapped destination role refuses inside the authority transaction.
- Retry identity and pass/return races remain effectively once.
- Current, destination phase, planned Next, claim release, and episode minting
  remain one atomic event.
- Same-route phase transitions remain authorized separately.
- Source, packaged CLI, JSON/TUI parity, and representative workflows agree.

## Review clarification — 2026-08-17

The closed stage-role vocabulary includes the established abbreviations used
by the existing configuration surface: `dev` is implementation/`active`, and
`rev` is reviewer/`review`. This is not an open alias mechanism: the shipped
`conf/baton.example.json` uses `dev`, repository workflow fixtures use both,
and every other role still refuses unless explicitly added to the closed map.
The canonical `impl`, `rsrch`, `rview`, and `approv` spellings retain their
pinned meanings.

## Superseded — 2026-08-18

The decision that destination role determines `research`, `active`, or
`review` phase is superseded by the scheduler-state model recorded in
`../finding-phase-is-scheduler-state/FINDING.md`. Route still determines
eligibility and the kind of activity; it no longer names phase. This file is
preserved as the history of the live confusion that led to the replacement.
