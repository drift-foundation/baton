# Finding: the blocker-summary column should say Wait

## Parent

`finding-v11-messaging-cutover-gate` — observed while reading the live W24
dependency sequence in the v11 TUI.

## Observed

The compact Work table labels the first-open-blocker summary `Blk` and renders
a directional arrow such as `← W148`. `Blk` is ambiguous between “blocks” and
“blocked by,” while the arrow competes visually with the separate `↳`
containment marker. The cell reports only current open blockers, not the
complete dependency graph.

## Decision — 2026-08-16

Rename the column `Wait` and render the first open blocker without an arrow:

```text
Wait
W171
W171+2
```

- `W171+2` means the Work waits on W171 and two additional open blockers.
- Select the displayed blocker deterministically from the canonical open
  blocker order.
- Leave the cell empty when no open blocker exists.
- `↳` remains exclusively the containment-tree marker.
- `[b] deps` remains the complete dependency/dependent graph view, including
  relations not present in the containment tree.

This is presentation only; dependency readiness, closure and event semantics
do not change.

## Acceptance

- Wide and narrow Work tables use `Wait`, never `Blk`, and contain no blocker
  arrow.
- Zero, one and multiple open blockers render empty, `Wn`, and `Wn+N`
  respectively without hiding the exact count.
- Deterministic selection, ultra-short local IDs, dependency-detail navigation
  and containment indentation remain intact.

