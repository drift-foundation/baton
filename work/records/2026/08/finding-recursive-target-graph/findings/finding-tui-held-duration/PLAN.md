# Plan

**Status:** queued as W226; its approved scope now includes structured pending
pickup state and is no longer presentation-only.

1. Revalidate the current `age_cell`, `age_field`, Work-table column metadata,
   responsive layout and W33/W47 tests against the current tree.
2. Expose structured handoff-held and pickup/claim facts in canonical JSON;
   glyphs remain a TUI-only projection.
3. Rename the compact TUI header from `Age` to `Held`; start its floored
   `HH:MM` interval at handoff, retain it through claim, render through `99:59`,
   and retain `99h+` and the negative-clock clamp.
4. Prefix an unclaimed operational destination Phase with `>`, replacing it
   with `!` after six minutes. Claim removes the prefix without resetting
   `Held`; no timeout mutates workflow authority.
5. Update focused authority, projection, renderer, refresh, heartbeat and
   packaged-TUI tests, including pass-before-claim, overdue pickup, claim,
   repass, terminal and structured-JSON/no-glyph boundaries.
6. Run focused tests and `just test-v11`, then return for independent review.
