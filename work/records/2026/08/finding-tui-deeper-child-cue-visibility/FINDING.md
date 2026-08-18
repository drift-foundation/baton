# Finding: deeper Work exists but its disclosure cue is clipped

## Observed — 2026-08-18

The live v11 TUI showed W5, `Rewrite public docs and architecture for v11`,
with no indication that W6 existed beneath it. Canonical JSON proved W5 had
one open child and W6 was actively claimed by `baton.tuner`; re-rooting W5
with `u` exposed it.

The failure is in presentation, not authority. The renderer prefixes the
child title with `↳`, appends `▸N` after the complete title, and only then
truncates the combined string to the available Title width. A long title
therefore removes the exact disclosure cue that tells the user more Work is
hidden.

This violates the closed W71 contract in
`work/records/2026/08/finding-recursive-target-graph/findings/finding-tui-message-browser/FINDING.md`,
which requires a visible deeper-child disclosure. W71 remains closed; this is
a new follow-up defect with new evidence.

## Confirmed decision — 2026-08-18

Containment/disclosure symbols occupy reserved structural space before the
truncatable title. Title length, terminal width, selection, filters, and other
columns must never silently remove the fact that a visible Work has hidden
children. Do not copy a child's Handler onto its parent: the cue says that
deeper Work exists, while Handler continues to name only the exact claimed
row.

The companion three-level design is recorded independently in
`work/records/2026/08/finding-tui-three-level-work-tree/`. This defect remains
valid regardless of whether the visible window is two or three levels.

## Acceptance

- A long visible title with hidden children retains a fixed disclosure cue at
  every supported width where the Work row itself is shown.
- Leaf rows never show the cue, and parent Handler remains blank unless that
  parent itself is claimed.
- Focused virtual-screen and real-PTY coverage reproduce the live W5/W6 shape,
  including title truncation and resize.
- JSON authority/projection semantics and SQLite schema do not change.

