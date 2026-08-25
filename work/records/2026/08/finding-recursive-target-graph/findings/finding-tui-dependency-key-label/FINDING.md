# Finding: `b links` reads as “blinks” in the Work footer

## Observed — 2026-08-16

During the fresh-authority trial, Slawomir read the footer text `b links` as
“blinks” and reasonably expected it to explain or control the active-row
blink. Pressing `b` instead opened the selected Work's dependency-neighbor
view and reported `(no blocking or dependent neighbors)`.

The dependency result was correct: active/claimed state does not imply a
blocker or dependent edge. The defect is the compressed key label, whose
adjacent `b` and `links` form a misleading English word.

## Confirmed correction — 2026-08-16

**Confirmed by Slawomir.** Label the action `[b] deps`. The brackets separate
the key from its meaning and `deps` accurately covers both blocker and
dependent neighbors without suggesting blink behavior.

This is a TUI wording/help correction only. The `b` key, links projection,
dependency graph, empty-state text, JSON, and protocol remain unchanged.

## Superseded key ruling — 2026-08-23

The instruction to preserve `b` is superseded by the independently scheduled
record `work/records/2026/08/finding-tui-dependency-key-d/`. The current
confirmed contract is `[d] deps`; lowercase `b` is removed with no
compatibility alias. The graph and protocol portions of the 2026-08-16 ruling
remain current.
