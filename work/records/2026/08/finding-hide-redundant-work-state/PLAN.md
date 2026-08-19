# Plan

1. [done] Confirmed that the default Work list hides terminal rows and thus
   renders the same `open` State for every visible row.
2. [done] Approved removing State from open-only lists and showing compact
   `Out` values (`sat`, `nsat`, `rej`, `cancl`) only where terminal Work is
   visible; mixed-view open rows show `-`.
3. [done] Make Work-list columns lifecycle-aware without
   changing canonical status, phase, filtering, detail, or Events.
4. [done] Cover open-only, mixed, closed-only, narrow, resize,
   containment, selection, and projection parity.
5. [done] Independently verify the frozen implementation and focused plus
   adjacent v11 TUI gates before closure. The full implementer gate had one
   known unrelated W36 interrupt regression, already returned under W36.
