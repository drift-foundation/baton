# Finding: make runtime-state tables clear and responsive

## Status

Confirmed by Slawomir on 2026-08-19 and ready for implementation.

## Observed

Two related runtime-presentation choices make the current TUI harder to read:

1. The Jobs `Agent` column does not identify an agent. Its cells are runtime
   states such as `work`, `input`, `retry`, and `off`; `Handler` already names
   the participant.
2. The Teams Members table sizes every column to its floor/current content and
   leaves the rest of the terminal unused. It calculates `used` width but does
   not distribute the surplus. `Session` is additionally truncated to twelve
   characters before layout, so a wide terminal cannot recover the full
   locator.

The result is a tight table on the left with unused space on the right and one
of its most useful diagnostic identifiers needlessly chopped.

## Confirmed decision — 2026-08-19

- In Jobs, rename the runtime-state column from `Agent` to `Run`. This is a
  presentation rename only; canonical runtime fields and values do not move.
- In Teams, retain separate `Agent` and `State` columns. There `Agent`
  identifies the adapter family and `State` reports what the runner is doing.
- Make the Teams Members table responsive across the available terminal
  width:
  - keep compact categorical fields (`Role`, `Agent`, `State`, `Work`, and
    `Since`) bounded and stable;
  - use surplus width for useful identity/diagnostic text, including the
    participant/display identity and session locator;
  - preserve the complete session locator whenever it fits;
  - abbreviate or omit optional material only when the terminal is genuinely
    too narrow, using a deterministic order.
- Never pre-truncate a value before layout has determined the width available
  to its column.

This supersedes the Jobs `Agent` header and the always-abbreviated Teams
`Session` example in `work/records/2026/08/finding-agent-runtime-state/`. It
does not change that record's authority model or the distinction between
workflow and runner facts.

## Acceptance boundary

- Jobs renders `Run`, not `Agent`, beside `Handler`, with the same canonical
  runtime-state cells and JSON parity.
- Teams continues to distinguish adapter family (`Agent`) from runtime
  `State`.
- At a sufficiently wide terminal, the Members table consumes the useful
  width and displays a complete session locator rather than a forced
  twelve-character prefix.
- Narrow widths truncate or omit whole optional fields deterministically,
  never split identifiers ambiguously, and never paint beyond the screen.
- Selection highlighting, own-member emphasis, member detail, poke actions,
  resize, refresh, and cached-projection behavior remain unchanged.
- Focused virtual-screen and real-terminal regressions cover wide, exact-fit,
  narrow, resize, missing-session, and long-identity cases.
- Operator documentation uses the same Jobs and Teams column vocabulary.
