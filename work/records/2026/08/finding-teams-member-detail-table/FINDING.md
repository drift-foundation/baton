# Finding: render Teams member details as a key/value table

## Status

Confirmed by Slawomir on 2026-08-19 and ready for implementation.

## Observed

Selecting a member in Teams currently paints a sequence of prose lines:
identity, roles, routes, held Work, runner state, adapter/provider/model,
session, incarnation, timestamps, runtime facts, and the last poke answer.
The data is useful, but labels and values begin at different columns and
several facts are packed into single sentences. An operator must reread the
whole block to find one field.

The runtime authority already exposes typed fields. Flattening them into prose
in the TUI throws away the scanability that structure provides.

## Confirmed decision — 2026-08-19

- Render Teams member details as grouped key/value rows: stable keys on the
  left, values on the right.
- Use visible sections for at least:
  - Identity and routing;
  - Workflow;
  - Runner state;
  - Operational diagnostics;
  - Last poke answer.
- Align the value column across rows. Wrapped continuation lines begin at the
  value column rather than under the key.
- Do not combine unrelated facts merely to save rows. Provider, model,
  session, incarnation, state, cause, transition time, last contact, and each
  operational fact receive independently discoverable keys.
- A published runtime `log` fact appears as a `Log` row with its exact locator,
  source, and observation age. When no log fact exists, presentation reports
  that it was not published rather than guessing a path.
- Preserve complete values whenever width permits. Narrow layouts wrap values
  predictably; they do not silently chop identifiers or allow a long key to
  consume the value column.
- This is presentation only. Canonical projections, poke/runtime semantics,
  freshness, authorization, and available actions do not change.

## Acceptance boundary

- A member's detail block is readable as a two-column key/value table with
  consistent alignment and visible section boundaries.
- Every fact currently exposed by member detail remains available, including
  roles, route coverage, held Work, runtime lease, safe operational facts, and
  the last poke answer.
- Missing, unknown, stale, and absent facts stay distinguishable; the renderer
  never substitutes a reassuring value.
- Long session, incarnation, path, model, and diagnostic values wrap under the
  value column and remain recoverable on a sufficiently wide terminal.
- Selection, scrolling, refresh, poke/withdraw actions, own/all team scope,
  tab navigation, and CLI/JSON parity remain unchanged.
- Focused virtual-screen and real-terminal regressions cover full, missing,
  unknown, stale, long-value, narrow, resize, and multi-route members.
- Operator documentation illustrates the same sections and key vocabulary.
